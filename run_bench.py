from __future__ import annotations
import argparse
import asyncio
from agentic_bench.workload import Workload
from agentic_bench.sim import run_sim
from agentic_bench.metrics import make_stats

def main() -> None:
    ap = argparse.ArgumentParser(description="Agentic CPU Bottleneck Bench — run a single workload.")
    ap.add_argument("--workload", required=True, help="Path to workload JSON (e.g., workloads/mixed.json)")
    ap.add_argument("--agents", type=int, default=32, help="Number of concurrent agents")
    ap.add_argument("--steps", type=int, default=200, help="Steps per agent")
    ap.add_argument("--seed", type=int, default=0, help="Random seed")
    args = ap.parse_args()

    wl = Workload.from_json(args.workload)
    out = asyncio.run(run_sim(wl, agents=args.agents, steps=args.steps, seed=args.seed))
    stats = make_stats(
        name=wl.name,
        agents=args.agents,
        steps=args.steps,
        step_latencies_ms=out["latencies_ms"],
        cpu_time_s=out["cpu_time_s"],
        wall_time_s=out["wall_time_s"],
        cpu_ms=out["cpu_ms_per_step"],
        io_wait_ms=out["io_wait_ms_per_step"],
        parse_ms=out["parse_ms_per_step"],
        json_kb=out["json_kb_per_step"],
        ctx_switches=out["ctx_switches"],
    )

    print("=" * 110)
    print("Agentic CPU Bottleneck Bench — Run Summary")
    print("=" * 110)
    print(f"Workload: {wl.name}  | agents={stats.agents} steps/agent={stats.steps}")
    print(f"p50_ms={stats.p50_ms:.2f}  p95_ms={stats.p95_ms:.2f}  cpu_util={stats.cpu_util:.3f}")
    print(f"cpu_ms/step={stats.cpu_ms:.2f}  io_wait_ms/step={stats.io_wait_ms:.2f}  parse_ms/step={stats.parse_ms:.2f}  json_kb/step={stats.json_kb:.2f}")
    if stats.ctx_switches is not None:
        print(f"ctx_switches(delta)={stats.ctx_switches}")
    print("=" * 110)

if __name__ == "__main__":
    main()
