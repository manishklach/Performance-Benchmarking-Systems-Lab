from __future__ import annotations

import csv
import io
import re
import time
from dataclasses import dataclass
from typing import Iterable

from .windows import run_powershell


INSTANCE_PATTERN = re.compile(r"pid_(\d+).*?engtype_([^_]+(?: [^_]+)*)", re.IGNORECASE)
SYSTEM_PROCESS_NAMES = {"csrss.exe", "dwm.exe", "System", "svchost.exe", "audiodg.exe"}


@dataclass
class GpuProcessSample:
    pid: int
    name: str
    command_line: str | None
    total_util_percent: float
    engines: dict[str, float]
    is_system: bool


@dataclass
class GpuEngineSample:
    total_util_percent: float
    engines: dict[str, float]
    running_time_deltas_ms: dict[str, float] | None = None


def _sample_gpu_counter(counter_name: str) -> list[dict[str, str]]:
    script = (
        f"Get-Counter '\\GPU Engine(*)\\{counter_name}' | "
        "Select-Object -ExpandProperty CounterSamples | "
        "Select-Object InstanceName,CookedValue | ConvertTo-Csv -NoTypeInformation"
    )
    output = run_powershell(script)
    return list(csv.DictReader(io.StringIO(output)))


def _sample_gpu_counters() -> list[dict[str, str]]:
    return _sample_gpu_counter("Utilization Percentage")


def _process_lookup() -> dict[int, dict[str, str | None]]:
    script = (
        "Get-CimInstance Win32_Process | "
        "Select-Object ProcessId,Name,CommandLine | ConvertTo-Csv -NoTypeInformation"
    )
    output = run_powershell(script)
    lookup: dict[int, dict[str, str | None]] = {}
    for row in csv.DictReader(io.StringIO(output)):
        try:
            pid = int(row["ProcessId"])
        except (TypeError, ValueError):
            continue
        lookup[pid] = {
            "name": row.get("Name") or "<unknown>",
            "command_line": row.get("CommandLine") or None,
        }
    return lookup


def trace_gpu_processes(limit: int = 10, include_idle: bool = False) -> list[GpuProcessSample]:
    counters = _sample_gpu_counters()
    processes = _process_lookup()
    aggregate: dict[int, dict[str, object]] = {}

    for row in counters:
        instance_name = row.get("InstanceName", "")
        match = INSTANCE_PATTERN.search(instance_name)
        if not match:
            continue
        pid = int(match.group(1))
        engine_type = match.group(2).strip()
        try:
            value = float(row.get("CookedValue", "0") or 0.0)
        except ValueError:
            continue

        if pid not in aggregate:
            proc_info = processes.get(pid, {"name": "<unknown>", "command_line": None})
            aggregate[pid] = {
                "name": proc_info["name"],
                "command_line": proc_info["command_line"],
                "total": 0.0,
                "engines": {},
            }

        aggregate[pid]["total"] = float(aggregate[pid]["total"]) + value
        engines = aggregate[pid]["engines"]
        assert isinstance(engines, dict)
        engines[engine_type] = float(engines.get(engine_type, 0.0)) + value

    results: list[GpuProcessSample] = []
    for pid, data in aggregate.items():
        total = round(float(data["total"]), 2)
        if not include_idle and total <= 0:
            continue
        engines = {
            key: round(value, 2)
            for key, value in sorted(data["engines"].items(), key=lambda item: item[1], reverse=True)
            if include_idle or value > 0
        }
        results.append(
            GpuProcessSample(
                pid=pid,
                name=str(data["name"]),
                command_line=data["command_line"] if isinstance(data["command_line"], str) else None,
                total_util_percent=total,
                engines=engines,
                is_system=str(data["name"]) in SYSTEM_PROCESS_NAMES or pid in {0, 4},
            )
        )

    results.sort(key=lambda item: item.total_util_percent, reverse=True)
    return results[:limit]


def sample_gpu_engines(include_idle: bool = False) -> GpuEngineSample:
    counters = _sample_gpu_counters()
    engines: dict[str, float] = {}
    total = 0.0
    for row in counters:
        instance_name = row.get("InstanceName", "")
        match = INSTANCE_PATTERN.search(instance_name)
        if not match:
            continue
        engine_type = match.group(2).strip()
        try:
            value = float(row.get("CookedValue", "0") or 0.0)
        except ValueError:
            continue
        total += value
        engines[engine_type] = engines.get(engine_type, 0.0) + value

    filtered = {
        key: round(value, 2)
        for key, value in sorted(engines.items(), key=lambda item: item[1], reverse=True)
        if include_idle or value > 0
    }
    return GpuEngineSample(total_util_percent=round(total, 2), engines=filtered)


def sample_gpu_engine_running_times() -> dict[str, float]:
    counters = _sample_gpu_counter("Running Time")
    engines: dict[str, float] = {}
    for row in counters:
        instance_name = row.get("InstanceName", "")
        match = INSTANCE_PATTERN.search(instance_name)
        if not match:
            continue
        engine_type = match.group(2).strip()
        try:
            value = float(row.get("CookedValue", "0") or 0.0)
        except ValueError:
            continue
        engines[engine_type] = engines.get(engine_type, 0.0) + value
    return engines


def format_engine_summary(engines: Iterable[tuple[str, float]]) -> str:
    return ", ".join(f"{name}={value:.2f}%" for name, value in engines)


def format_trace_report(results: list[GpuProcessSample]) -> str:
    lines = [
        "GPU Process Trace",
        "  note: this build attributes GPU usage to processes, not individual threads.",
    ]
    app_rows = [item for item in results if not item.is_system]
    system_rows = [item for item in results if item.is_system]

    if app_rows:
        lines.append("  apps:")
        for item in app_rows:
            lines.extend(_format_process_lines(item))
    if system_rows:
        lines.append("  system:")
        for item in system_rows:
            lines.extend(_format_process_lines(item))
    if len(lines) == 2:
        lines.append("  no active GPU consumers found.")
    return "\n".join(lines)


def _format_process_lines(item: GpuProcessSample) -> list[str]:
    lines = [f"    {item.total_util_percent:7.2f}%  pid={item.pid:<6} name={item.name}"]
    engine_summary = format_engine_summary(item.engines.items()) if item.engines else "no active engines"
    lines.append(f"             engines: {engine_summary}")
    if item.command_line:
        lines.append(f"             cmd: {item.command_line}")
    return lines


def watch_gpu_processes(limit: int = 10, interval: float = 1.0, include_idle: bool = False, iterations: int | None = None) -> None:
    count = 0
    while iterations is None or count < iterations:
        results = trace_gpu_processes(limit=limit, include_idle=include_idle)
        print("\x1bc", end="")
        print(time.strftime("%Y-%m-%d %H:%M:%S"))
        print(format_trace_report(results))
        count += 1
        if iterations is None or count < iterations:
            time.sleep(interval)
