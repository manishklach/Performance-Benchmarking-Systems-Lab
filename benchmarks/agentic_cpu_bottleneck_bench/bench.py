from __future__ import annotations
import asyncio
from agentic_bench.workload import Workload
from agentic_bench.sim import run_sim
from agentic_bench.metrics import make_stats

WORKLOADS = [
    "workloads/reasoning_heavy.json",
    "workloads/action_heavy.json",
    "workloads/mixed.json",
]

def main() -> None:
    agents = 32
    steps = 200

    rows = []
    for path in WORKLOADS:
        wl = Workload.from_json(path)
        out = asyncio.run(run_sim(wl, agents=agents, steps=steps, seed=0))
        stats = make_stats(
            name=wl.name,
            agents=agents,
            steps=steps,
            step_latencies_ms=out["latencies_ms"],
            cpu_time_s=out["cpu_time_s"],
            wall_time_s=out["wall_time_s"],
            cpu_ms=out["cpu_ms_per_step"],
            io_wait_ms=out["io_wait_ms_per_step"],
            parse_ms=out["parse_ms_per_step"],
            json_kb=out["json_kb_per_step"],
            ctx_switches=out["ctx_switches"],
        )
        rows.append(stats)

    print("=" * 118)
    print("Agentic CPU Bottleneck Bench — Benchmark Table")
    print("=" * 118)
    header = ["workload","agents","steps","p50_ms","p95_ms","cpu_util","cpu_ms","io_wait_ms","parse_ms","json_kb","ctx_sw"]
    print(" ".join(h.ljust(12) for h in header))
    for s in rows:
        print(
            f"{s.name.ljust(12)} "
            f"{str(s.agents).ljust(12)} "
            f"{str(s.steps).ljust(12)} "
            f"{f'{s.p50_ms:.2f}'.ljust(12)} "
            f"{f'{s.p95_ms:.2f}'.ljust(12)} "
            f"{f'{s.cpu_util:.3f}'.ljust(12)} "
            f"{f'{s.cpu_ms:.2f}'.ljust(12)} "
            f"{f'{s.io_wait_ms:.2f}'.ljust(12)} "
            f"{f'{s.parse_ms:.2f}'.ljust(12)} "
            f"{f'{s.json_kb:.2f}'.ljust(12)} "
            f"{str(s.ctx_switches) if s.ctx_switches is not None else '-':<12}"
        )
    print("=" * 118)
    print("Tip: vary fan-out to see CPU vs wait-bound behavior:")
    print("  python run_bench.py --workload workloads/mixed.json --agents 8 --steps 200")
    print("  python run_bench.py --workload workloads/mixed.json --agents 64 --steps 200")
    print("=" * 118)

if __name__ == "__main__":
    main()
