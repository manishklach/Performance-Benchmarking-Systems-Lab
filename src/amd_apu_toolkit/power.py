from __future__ import annotations

import csv
import math
import time
from dataclasses import dataclass
from pathlib import Path

from .windows import list_counter_paths, sample_counters


@dataclass
class PowerRun:
    csv_path: Path
    samples: int
    avg_cpu_util: float | None
    peak_gpu_util: float | None
    min_free_memory_gb: float | None


def collect_power_sample(counter_paths: list[str] | None = None) -> dict[str, float | str | None]:
    if counter_paths is None:
        counter_paths = build_counter_paths()
    sample = sample_counters(counter_paths)
    cpu_util = None
    cpu_time = None
    free_memory_gb = None
    gpu_util = 0.0
    gpu_util_seen = False
    gpu_shared_mb = 0.0
    gpu_dedicated_mb = 0.0
    gpu_total_committed_mb = 0.0

    for path, value in sample.items():
        lowered = path.lower()
        if value is None:
            continue
        if lowered.endswith(r"\% processor time"):
            cpu_time = value
        elif lowered.endswith(r"\% processor utility"):
            cpu_util = value
        elif lowered.endswith(r"\available mbytes"):
            free_memory_gb = value / 1024
        elif "utilization percentage" in lowered:
            gpu_util += value
            gpu_util_seen = True
        elif "shared usage" in lowered:
            gpu_shared_mb += value / 1024**2
        elif "dedicated usage" in lowered:
            gpu_dedicated_mb += value / 1024**2
        elif "total committed" in lowered:
            gpu_total_committed_mb += value / 1024**2

    cpu_value = cpu_time if cpu_time is not None else cpu_util
    if cpu_value is not None:
        cpu_value = max(0.0, min(100.0, cpu_value))

    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cpu_util_percent": round(cpu_value, 2) if cpu_value is not None else None,
        "gpu_util_percent": round(gpu_util, 2) if gpu_util_seen else None,
        "gpu_shared_mb": round(gpu_shared_mb, 2) if gpu_shared_mb else None,
        "gpu_dedicated_mb": round(gpu_dedicated_mb, 2) if gpu_dedicated_mb else None,
        "gpu_total_committed_mb": round(gpu_total_committed_mb, 2) if gpu_total_committed_mb else None,
        "free_memory_gb": round(free_memory_gb, 2) if free_memory_gb is not None else None,
    }


def build_counter_paths() -> list[str]:
    counter_paths = [
        r"\Processor(_Total)\% Processor Time",
        r"\Processor Information(_Total)\% Processor Utility",
        r"\Memory\Available MBytes",
    ]
    gpu_paths = list_counter_paths([r"\GPU Engine(", r"\GPU Adapter Memory("])
    counter_paths.extend(
        path
        for path in gpu_paths
        if "utilization percentage" in path.lower()
        or "shared usage" in path.lower()
        or "dedicated usage" in path.lower()
        or "total committed" in path.lower()
    )
    return counter_paths


def correlate_power(duration: int, interval: float, output_dir: Path) -> PowerRun:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"power_trace_{int(time.time())}.csv"
    counter_paths = build_counter_paths()

    rows: list[dict[str, float | str | None]] = []
    sample_count = max(1, math.ceil(duration / interval))
    for index in range(sample_count):
        rows.append(collect_power_sample(counter_paths))
        if index < sample_count - 1:
            time.sleep(interval)

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    cpu_values = [row["cpu_util_percent"] for row in rows if row["cpu_util_percent"] is not None]
    gpu_values = [row["gpu_util_percent"] for row in rows if row["gpu_util_percent"] is not None]
    free_values = [row["free_memory_gb"] for row in rows if row["free_memory_gb"] is not None]

    return PowerRun(
        csv_path=csv_path,
        samples=len(rows),
        avg_cpu_util=round(sum(cpu_values) / len(cpu_values), 2) if cpu_values else None,
        peak_gpu_util=max(gpu_values) if gpu_values else None,
        min_free_memory_gb=min(free_values) if free_values else None,
    )
