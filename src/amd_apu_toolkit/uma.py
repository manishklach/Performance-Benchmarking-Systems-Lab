from __future__ import annotations

from dataclasses import dataclass

from .windows import list_counter_paths, run_json_powershell, sample_counters


@dataclass
class UmaSnapshot:
    total_memory_gb: float
    free_memory_gb: float
    cpu_util_percent: float | None
    gpu_util_percent: float | None
    gpu_dedicated_mb: float | None
    gpu_shared_mb: float | None
    pressure_score: int
    verdict: str


def inspect_uma() -> UmaSnapshot:
    system = run_json_powershell(
        "Get-CimInstance Win32_ComputerSystem | "
        "Select-Object TotalPhysicalMemory"
    )
    total_memory_gb = round(int(system["TotalPhysicalMemory"]) / 1024**3, 2)

    counter_paths = [
        r"\Memory\Available MBytes",
        r"\Processor Information(_Total)\% Processor Utility",
    ]

    gpu_paths = list_counter_paths(
        [
            r"\GPU Engine(",
            r"\GPU Adapter Memory(",
        ]
    )
    counter_paths.extend(
        path
        for path in gpu_paths
        if "utilization percentage" in path.lower()
        or "dedicated usage" in path.lower()
        or "shared usage" in path.lower()
    )

    samples = sample_counters(counter_paths)
    free_memory_mb = None
    cpu_util = None
    for path, value in samples.items():
        lowered = path.lower()
        if lowered.endswith(r"\available mbytes"):
            free_memory_mb = value
        elif lowered.endswith(r"\% processor utility"):
            cpu_util = value
    free_memory_gb = round((free_memory_mb or 0) / 1024, 2)

    gpu_util = 0.0
    gpu_util_seen = False
    gpu_dedicated_mb = 0.0
    gpu_shared_mb = 0.0

    for path, value in samples.items():
        lowered = path.lower()
        if value is None:
            continue
        if "utilization percentage" in lowered:
            gpu_util += value
            gpu_util_seen = True
        elif "dedicated usage" in lowered:
            gpu_dedicated_mb += value / 1024**2
        elif "shared usage" in lowered:
            gpu_shared_mb += value / 1024**2

    pressure_score = 0
    if free_memory_gb < 2.0:
        pressure_score += 2
    elif free_memory_gb < 4.0:
        pressure_score += 1
    if cpu_util and cpu_util > 80:
        pressure_score += 1
    if gpu_shared_mb > 1024:
        pressure_score += 1
    if gpu_util_seen and gpu_util > 70:
        pressure_score += 1

    if pressure_score >= 4:
        verdict = "high shared-memory pressure"
    elif pressure_score >= 2:
        verdict = "moderate shared-memory pressure"
    else:
        verdict = "healthy for mixed CPU/GPU workloads"

    return UmaSnapshot(
        total_memory_gb=total_memory_gb,
        free_memory_gb=free_memory_gb,
        cpu_util_percent=round(cpu_util, 2) if cpu_util is not None else None,
        gpu_util_percent=round(gpu_util, 2) if gpu_util_seen else None,
        gpu_dedicated_mb=round(gpu_dedicated_mb, 1) if gpu_dedicated_mb else None,
        gpu_shared_mb=round(gpu_shared_mb, 1) if gpu_shared_mb else None,
        pressure_score=pressure_score,
        verdict=verdict,
    )
