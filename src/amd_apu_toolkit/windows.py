from __future__ import annotations

import csv
import io
import json
import subprocess
from typing import Iterable


def run_powershell(command: str) -> str:
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def run_json_powershell(command: str):
    output = run_powershell(f"{command} | ConvertTo-Json -Depth 4")
    if not output:
        return None
    return json.loads(output)


def list_counter_paths(prefixes: Iterable[str]) -> list[str]:
    prefix_list = list(prefixes)
    selected: list[str] = []
    candidate_sets: list[str] = []
    if any("gpu engine(" in prefix.lower() for prefix in prefix_list):
        candidate_sets.append("GPU Engine")
    if any("gpu adapter memory(" in prefix.lower() for prefix in prefix_list):
        candidate_sets.append("GPU Adapter Memory")

    for counter_set in candidate_sets:
        try:
            output = run_powershell(
                f"Get-Counter -ListSet '{counter_set}' | Select-Object -ExpandProperty Paths"
            )
        except subprocess.CalledProcessError:
            continue
        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue
            lowered = line.lower()
            if any(prefix.lower() in lowered for prefix in prefix_list):
                selected.append(line)

    return sorted(set(selected))


def sample_counters(counter_paths: list[str]) -> dict[str, float | None]:
    if not counter_paths:
        return {}
    quoted = ",".join(f"'{path}'" for path in counter_paths)
    script = (
        f"Get-Counter {quoted} | Select-Object -ExpandProperty CounterSamples | "
        "Select-Object Path,CookedValue | ConvertTo-Csv -NoTypeInformation"
    )
    output = run_powershell(script)
    rows = csv.DictReader(io.StringIO(output))
    result: dict[str, float | None] = {}
    for row in rows:
        try:
            result[row["Path"]] = float(row["CookedValue"])
        except (TypeError, ValueError):
            result[row["Path"]] = None
    return result
