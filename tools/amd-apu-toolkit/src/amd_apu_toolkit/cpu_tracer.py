from __future__ import annotations

import csv
import io
import os
from dataclasses import dataclass

from .windows import run_powershell, sample_counters


SYSTEM_COUNTERS = [
    r"\System\Processor Queue Length",
    r"\System\Context Switches/sec",
    r"\Memory\Page Faults/sec",
    r"\Memory\Pages Input/sec",
    r"\Memory\Page Reads/sec",
    r"\Memory\Committed Bytes",
    r"\Memory\Commit Limit",
    r"\Memory\% Committed Bytes In Use",
    r"\Processor(_Total)\% DPC Time",
    r"\Processor(_Total)\% Interrupt Time",
    r"\PhysicalDisk(_Total)\Current Disk Queue Length",
    r"\Paging File(_Total)\% Usage",
]


@dataclass
class CpuProcessSample:
    pid: int
    name: str
    cpu_util_percent: float
    thread_count: int
    working_set_private_mb: float


def sample_cpu_processes(limit: int = 15) -> list[CpuProcessSample]:
    logical_cpus = max(1, os.cpu_count() or 1)
    script = (
        "Get-CimInstance Win32_PerfFormattedData_PerfProc_Process | "
        "Select-Object Name,IDProcess,PercentProcessorTime,ThreadCount,WorkingSetPrivate | "
        "ConvertTo-Csv -NoTypeInformation"
    )
    output = run_powershell(script)
    rows = csv.DictReader(io.StringIO(output))
    results: list[CpuProcessSample] = []
    for row in rows:
        name = (row.get("Name") or "").strip()
        if name in {"_Total", "Idle"}:
            continue
        try:
            pid = int(row.get("IDProcess") or 0)
            raw_cpu = float(row.get("PercentProcessorTime") or 0.0)
            thread_count = int(row.get("ThreadCount") or 0)
            working_set_private = float(row.get("WorkingSetPrivate") or 0.0) / 1024**2
        except ValueError:
            continue
        cpu_percent = round(raw_cpu / logical_cpus, 2)
        if cpu_percent <= 0:
            continue
        results.append(
            CpuProcessSample(
                pid=pid,
                name=name,
                cpu_util_percent=cpu_percent,
                thread_count=thread_count,
                working_set_private_mb=round(working_set_private, 2),
            )
        )
    results.sort(key=lambda item: item.cpu_util_percent, reverse=True)
    return results[:limit]


def sample_cpu_latency_metrics() -> dict[str, float]:
    samples = sample_counters(SYSTEM_COUNTERS)
    logical_cpus = max(1, os.cpu_count() or 1)
    metrics = {
        "processor_queue_length": 0.0,
        "runnable_threads_per_core": 0.0,
        "context_switches_per_sec": 0.0,
        "page_faults_per_sec": 0.0,
        "pages_input_per_sec": 0.0,
        "hard_faults_per_sec": 0.0,
        "committed_gb": 0.0,
        "commit_limit_gb": 0.0,
        "commit_in_use_percent": 0.0,
        "dpc_time_percent": 0.0,
        "interrupt_time_percent": 0.0,
        "disk_queue_depth": 0.0,
        "pagefile_usage_percent": 0.0,
        "memory_compression_mb": 0.0,
    }
    for path, value in samples.items():
        if value is None:
            continue
        lowered = path.lower()
        if lowered.endswith(r"\processor queue length"):
            metrics["processor_queue_length"] = round(value, 2)
            metrics["runnable_threads_per_core"] = round(value / logical_cpus, 3)
        elif lowered.endswith(r"\context switches/sec"):
            metrics["context_switches_per_sec"] = round(value, 2)
        elif lowered.endswith(r"\page faults/sec"):
            metrics["page_faults_per_sec"] = round(value, 2)
        elif lowered.endswith(r"\pages input/sec"):
            metrics["pages_input_per_sec"] = round(value, 2)
        elif lowered.endswith(r"\page reads/sec"):
            metrics["hard_faults_per_sec"] = round(value, 2)
        elif lowered.endswith(r"\committed bytes"):
            metrics["committed_gb"] = round(value / 1024**3, 2)
        elif lowered.endswith(r"\commit limit"):
            metrics["commit_limit_gb"] = round(value / 1024**3, 2)
        elif lowered.endswith(r"\% committed bytes in use"):
            metrics["commit_in_use_percent"] = round(value, 2)
        elif lowered.endswith(r"\% dpc time"):
            metrics["dpc_time_percent"] = round(value, 2)
        elif lowered.endswith(r"\% interrupt time"):
            metrics["interrupt_time_percent"] = round(value, 2)
        elif lowered.endswith(r"\current disk queue length"):
            metrics["disk_queue_depth"] = round(value, 2)
        elif lowered.endswith(r"\% usage"):
            metrics["pagefile_usage_percent"] = round(value, 2)
    metrics["memory_compression_mb"] = sample_memory_compression_mb()
    return metrics


def sample_memory_compression_mb() -> float:
    script = (
        "Get-Process -Name 'Memory Compression' -ErrorAction SilentlyContinue | "
        "Select-Object -First 1 -ExpandProperty WorkingSet64"
    )
    try:
        output = run_powershell(script)
    except Exception:
        return 0.0
    try:
        return round(float(output or 0.0) / 1024**2, 2)
    except ValueError:
        return 0.0


def sample_power_battery_metrics() -> dict[str, object]:
    battery_script = (
        "$battery = Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue | Select-Object -First 1 "
        "EstimatedChargeRemaining,BatteryStatus,EstimatedRunTime,DesignCapacity,FullChargeCapacity;"
        "$battery | ConvertTo-Json -Compress"
    )
    battery_raw = None
    try:
        battery_out = run_powershell(battery_script)
        battery_raw = None if not battery_out else battery_out
    except Exception:
        battery_raw = None

    power_plan = "unknown"
    try:
        scheme = run_powershell("powercfg /getactivescheme")
        if ":" in scheme:
            power_plan = scheme.split(":", 1)[1].strip()
    except Exception:
        pass

    saver_state = "unknown"
    try:
        saver_out = run_powershell("(Get-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Power\\User\\PowerSchemes').ActivePowerScheme")
        if saver_out:
            saver_state = "active plan detected"
    except Exception:
        pass

    metrics: dict[str, object] = {
        "has_battery": False,
        "battery_percent": None,
        "battery_status": "desktop/ac-only",
        "battery_remaining_min": None,
        "battery_health_percent": None,
        "ac_online": None,
        "power_plan": power_plan,
        "battery_saver_state": saver_state,
    }
    if not battery_raw:
        return metrics

    import json

    try:
        battery = json.loads(battery_raw)
    except json.JSONDecodeError:
        return metrics

    status_map = {
        1: "discharging",
        2: "ac idle",
        3: "charging",
        4: "low",
        5: "critical",
        6: "charging high",
        7: "charging low",
        8: "charging critical",
        9: "undefined",
        10: "partially charged",
        11: "partially charged",
    }
    design = battery.get("DesignCapacity") or 0
    full = battery.get("FullChargeCapacity") or 0
    health = round((float(full) / float(design)) * 100, 2) if design and full else None
    status_value = int(battery.get("BatteryStatus") or 0)
    metrics.update(
        {
            "has_battery": True,
            "battery_percent": battery.get("EstimatedChargeRemaining"),
            "battery_status": status_map.get(status_value, "unknown"),
            "battery_remaining_min": battery.get("EstimatedRunTime"),
            "battery_health_percent": health,
            "ac_online": status_value in {2, 3, 6, 7, 8, 9, 11},
        }
    )
    return metrics


def compute_risk_score(cpu_latency: dict[str, float], power_sample: dict[str, object], pressure_score: int, gpu_top_engine_util: float) -> dict[str, object]:
    score = 0
    reasons: list[str] = []

    if pressure_score >= 4:
        score += 25
        reasons.append("high UMA pressure")
    elif pressure_score >= 2:
        score += 12
        reasons.append("moderate UMA pressure")

    if cpu_latency.get("hard_faults_per_sec", 0.0) >= 100:
        score += 18
        reasons.append("hard faults")
    elif cpu_latency.get("hard_faults_per_sec", 0.0) >= 20:
        score += 10
        reasons.append("fault spikes")

    if cpu_latency.get("disk_queue_depth", 0.0) >= 2:
        score += 15
        reasons.append("disk queue")

    if cpu_latency.get("pagefile_usage_percent", 0.0) >= 20:
        score += 10
        reasons.append("pagefile usage")

    if cpu_latency.get("runnable_threads_per_core", 0.0) >= 1:
        score += 12
        reasons.append("scheduler backlog")
    elif cpu_latency.get("runnable_threads_per_core", 0.0) >= 0.4:
        score += 6

    if cpu_latency.get("dpc_time_percent", 0.0) >= 5 or cpu_latency.get("interrupt_time_percent", 0.0) >= 5:
        score += 10
        reasons.append("dpc/interrupt noise")

    if float(power_sample.get("free_memory_gb") or 0.0) <= 2:
        score += 10
        reasons.append("low free RAM")

    if cpu_latency.get("commit_in_use_percent", 0.0) >= 85:
        score += 10
        reasons.append("high commit")

    if gpu_top_engine_util >= 40:
        score += 8
        reasons.append("gpu spike")

    score = max(0, min(100, score))
    if score >= 60:
        level = "high"
    elif score >= 30:
        level = "moderate"
    else:
        level = "low"
    return {"score": score, "level": level, "reasons": reasons[:4]}
