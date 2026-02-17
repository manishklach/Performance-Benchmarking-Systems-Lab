from __future__ import annotations
from dataclasses import dataclass
from typing import List

try:
    import psutil  # type: ignore
except Exception:
    psutil = None  # type: ignore

@dataclass
class RunStats:
    name: str
    agents: int
    steps: int
    p50_ms: float
    p95_ms: float
    cpu_util: float
    cpu_ms: float
    io_wait_ms: float
    parse_ms: float
    json_kb: float
    ctx_switches: int | None

def percentile(values: List[float], q: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    k = (len(values) - 1) * q
    f = int(k)
    c = min(f + 1, len(values) - 1)
    if f == c:
        return values[f]
    d0 = values[f] * (c - k)
    d1 = values[c] * (k - f)
    return d0 + d1

def collect_ctx_switches() -> int | None:
    if psutil is None:
        return None
    try:
        p = psutil.Process()
        cs = p.num_ctx_switches()
        return int(getattr(cs, "voluntary", 0) + getattr(cs, "involuntary", 0))
    except Exception:
        return None

def make_stats(
    name: str,
    agents: int,
    steps: int,
    step_latencies_ms: List[float],
    cpu_time_s: float,
    wall_time_s: float,
    cpu_ms: float,
    io_wait_ms: float,
    parse_ms: float,
    json_kb: float,
    ctx_switches: int | None,
) -> RunStats:
    return RunStats(
        name=name,
        agents=agents,
        steps=steps,
        p50_ms=percentile(step_latencies_ms, 0.50),
        p95_ms=percentile(step_latencies_ms, 0.95),
        cpu_util=(cpu_time_s / wall_time_s) if wall_time_s > 0 else 0.0,
        cpu_ms=cpu_ms,
        io_wait_ms=io_wait_ms,
        parse_ms=parse_ms,
        json_kb=json_kb,
        ctx_switches=ctx_switches,
    )
