from __future__ import annotations

import re
import shutil
import subprocess
import time
from dataclasses import dataclass


@dataclass
class OpenClProbeResult:
    platform_name: str | None
    platform_version: str | None
    device_name: str | None
    driver_version: str | None
    max_compute_units: int | None
    unified_memory: bool | None
    average_clinfo_ms: float
    iterations: int


PATTERNS = {
    "platform_name": r"Platform Name:\s+(.+)",
    "platform_version": r"Platform Version:\s+(.+)",
    "device_name": r"Device Name:\s+(.+)",
    "board_name": r"Board name:\s+(.+)",
    "driver_version": r"Driver version:\s+(.+)",
    "max_compute_units": r"Max compute units:\s+(\d+)",
    "unified_memory": r"Unified memory for Host and Device:\s+(\d+)",
}


def _extract(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def probe_opencl(iterations: int) -> OpenClProbeResult:
    clinfo_path = shutil.which("clinfo")
    if not clinfo_path:
        raise RuntimeError("clinfo is not available on this machine.")

    completed = subprocess.run(
        [clinfo_path],
        check=True,
        capture_output=True,
        text=True,
    )
    output = completed.stdout

    elapsed: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        subprocess.run(
            [clinfo_path],
            check=True,
            capture_output=True,
            text=True,
        )
        elapsed.append((time.perf_counter() - start) * 1000)

    max_compute_units = _extract(PATTERNS["max_compute_units"], output)
    unified_memory = _extract(PATTERNS["unified_memory"], output)

    return OpenClProbeResult(
        platform_name=_extract(PATTERNS["platform_name"], output),
        platform_version=_extract(PATTERNS["platform_version"], output),
        device_name=_extract(PATTERNS["device_name"], output) or _extract(PATTERNS["board_name"], output),
        driver_version=_extract(PATTERNS["driver_version"], output),
        max_compute_units=int(max_compute_units) if max_compute_units else None,
        unified_memory=(unified_memory == "1") if unified_memory is not None else None,
        average_clinfo_ms=round(sum(elapsed) / len(elapsed), 2),
        iterations=iterations,
    )
