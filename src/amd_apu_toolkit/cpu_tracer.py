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
    r"\Processor(_Total)\% DPC Time",
    r"\Processor(_Total)\% Interrupt Time",
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
    metrics = {
        "processor_queue_length": 0.0,
        "context_switches_per_sec": 0.0,
        "page_faults_per_sec": 0.0,
        "pages_input_per_sec": 0.0,
        "dpc_time_percent": 0.0,
        "interrupt_time_percent": 0.0,
    }
    for path, value in samples.items():
        if value is None:
            continue
        lowered = path.lower()
        if lowered.endswith(r"\processor queue length"):
            metrics["processor_queue_length"] = round(value, 2)
        elif lowered.endswith(r"\context switches/sec"):
            metrics["context_switches_per_sec"] = round(value, 2)
        elif lowered.endswith(r"\page faults/sec"):
            metrics["page_faults_per_sec"] = round(value, 2)
        elif lowered.endswith(r"\pages input/sec"):
            metrics["pages_input_per_sec"] = round(value, 2)
        elif lowered.endswith(r"\% dpc time"):
            metrics["dpc_time_percent"] = round(value, 2)
        elif lowered.endswith(r"\% interrupt time"):
            metrics["interrupt_time_percent"] = round(value, 2)
    return metrics
