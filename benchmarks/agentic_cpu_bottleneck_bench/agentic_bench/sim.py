from __future__ import annotations
import asyncio
import json
import math
import os
import random
import sqlite3
import tempfile
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .util import jitter
from .workload import Workload

def _busy_cpu_ms(ms: float) -> None:
    if ms <= 0:
        return
    t0 = time.perf_counter()
    x = 0.0
    while (time.perf_counter() - t0) * 1000.0 < ms:
        x = math.sin(x + 0.1) * math.cos(x + 0.2) + 0.000001

def _json_parse_kb(kb: float) -> Tuple[float, float]:
    if kb <= 0:
        return 0.0, 0.0
    target = int(kb * 1024)
    payload = {"t": time.time(), "s": "x" * max(0, target - 64)}
    s = json.dumps(payload)
    t0 = time.perf_counter()
    _ = json.loads(s)
    dt = (time.perf_counter() - t0) * 1000.0
    return dt, len(s) / 1024.0

def _memory_ops(store: Dict[str, str], ops: int, hit_rate: float) -> None:
    if ops <= 0:
        return
    keys = list(store.keys())
    for _ in range(ops):
        if keys and random.random() < hit_rate:
            _ = store[random.choice(keys)]
        else:
            k = f"k{random.randint(0, 200000)}"
            store[k] = "v" * (random.randint(10, 200))
            if len(store) > 50000:
                for _ in range(2000):
                    store.pop(next(iter(store)))

async def _tool_wait(wait_ms: float) -> None:
    await asyncio.sleep(max(0.0, wait_ms / 1000.0))

def _disk_read_mock(bytes_n: int = 8192) -> None:
    with tempfile.NamedTemporaryFile(delete=True) as f:
        f.write(os.urandom(bytes_n))
        f.flush()
        f.seek(0)
        _ = f.read()

def _sqlite_mock() -> None:
    con = sqlite3.connect(":memory:")
    cur = con.cursor()
    cur.execute("create table t(k integer primary key, v text)")
    cur.executemany("insert into t(k,v) values (?,?)", [(i, "x"*20) for i in range(50)])
    cur.execute("select v from t where k = 10")
    _ = cur.fetchone()
    con.close()

@dataclass
class StepAccumulators:
    cpu_ms: float = 0.0
    io_wait_ms: float = 0.0
    parse_ms: float = 0.0
    json_kb: float = 0.0

async def agent_worker(agent_id: int, wl: Workload, steps: int, latencies_ms: List[float], acc: StepAccumulators) -> None:
    store: Dict[str, str] = {"seed": "v"}
    for _ in range(steps):
        t0 = time.perf_counter()

        cpu_ms = jitter(wl.planning.cpu_ms_mean, wl.planning.cpu_ms_jitter)
        _busy_cpu_ms(cpu_ms)
        acc.cpu_ms += cpu_ms

        kb = jitter(wl.planning.json_kb_mean, wl.planning.json_kb_jitter)
        dt_parse, kb_actual = _json_parse_kb(kb)
        acc.parse_ms += dt_parse
        acc.json_kb += kb_actual

        _memory_ops(store, wl.memory.ops_per_step, wl.memory.hit_rate)

        for tool in wl.tools:
            if random.random() < tool.p:
                w = jitter(tool.wait_ms_mean, tool.wait_ms_jitter)
                kb2 = jitter(tool.json_kb_mean, tool.json_kb_jitter)
                dt2, kb2_actual = _json_parse_kb(kb2)
                acc.parse_ms += dt2
                acc.json_kb += kb2_actual

                if tool.name == "fs_read":
                    _disk_read_mock()
                elif tool.name == "db_read":
                    _sqlite_mock()

                acc.io_wait_ms += w
                await _tool_wait(w)

        latencies_ms.append((time.perf_counter() - t0) * 1000.0)

async def run_sim(wl: Workload, agents: int, steps: int, seed: int = 0) -> dict:
    random.seed(seed)
    latencies_ms: List[float] = []
    acc = StepAccumulators()

    from .metrics import collect_ctx_switches
    ctx0 = collect_ctx_switches()

    wall0 = time.perf_counter()
    cpu0 = time.process_time()

    tasks = [asyncio.create_task(agent_worker(i, wl, steps, latencies_ms, acc)) for i in range(agents)]
    await asyncio.gather(*tasks)

    cpu1 = time.process_time()
    wall1 = time.perf_counter()

    ctx1 = collect_ctx_switches()
    ctx_delta = None
    if ctx0 is not None and ctx1 is not None:
        ctx_delta = max(0, ctx1 - ctx0)

    total_steps = agents * steps
    return {
        "latencies_ms": latencies_ms,
        "cpu_time_s": (cpu1 - cpu0),
        "wall_time_s": (wall1 - wall0),
        "cpu_ms_per_step": acc.cpu_ms / max(1, total_steps),
        "io_wait_ms_per_step": acc.io_wait_ms / max(1, total_steps),
        "parse_ms_per_step": acc.parse_ms / max(1, total_steps),
        "json_kb_per_step": acc.json_kb / max(1, total_steps),
        "ctx_switches": ctx_delta,
    }
