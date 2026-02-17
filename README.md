# Agentic CPU Bottleneck Bench

A **vendor-neutral benchmark harness** that makes the “CPU bottleneck in agentic AI” measurable.

It simulates multi-agent loops with configurable mixes of:
- planning / routing overhead (CPU-bound string + JSON work)
- tool-call orchestration (RPC-like waits + serialization)
- memory lookups (KV-style access patterns)
- I/O-like behavior (disk + sqlite mocks)

It produces a compact table with **p50/p95 step latency**, **CPU utilization proxy**, and **orchestration vs work** breakdown.

> This is not a model benchmark. It is a **control-plane / agent-runtime benchmark**.

---

## Quickstart (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe .\bench.py
```

Run a single scenario:

```powershell
.\.venv\Scripts\python.exe .\run_bench.py --workload workloads\mixed.json --agents 32 --steps 200
```

---

## Sample outputs
See [`docs/output.md`](docs/output.md) for real benchmark output tables and fan-out runs.

## What you get

The benchmark prints a table like:

- `p50_ms`, `p95_ms` — step latency distribution
- `cpu_util` — process CPU time / wall time (rough proxy for CPU saturation)
- `cpu_ms` — CPU time spent per step
- `io_wait_ms` — simulated tool/I/O wait per step
- `json_kb`, `parse_ms` — serialization + parsing costs
- optional: context switches if `psutil` is available

---

## Workloads

- `workloads/reasoning_heavy.json` — few tool calls, more CPU planning + parsing
- `workloads/action_heavy.json` — frequent tool calls and higher orchestration overhead
- `workloads/mixed.json` — typical “agent” blend

You can add your own JSON workload; see `workloads/schema.json`.

---

## Interpreting results

Common patterns:
- **High p95 with low cpu_util** → coordination / waits dominate (tool calls, I/O, blocking)
- **High cpu_util with rising p50/p95** → CPU saturated (planning/parsing dominates)
- **Large parse_ms / json_kb** → serialization overhead is a real tax; consider batching / binary codecs
- **Many agents increases tail** → lock contention + event loop overhead (agent fan-out)

See: `docs/INTERPRETING_OUTPUT.md`

---

## Repo layout

- `bench.py` — one-command benchmark table
- `run_bench.py` — run a single workload with CLI flags
- `agentic_bench/` — simulator + metrics
- `workloads/` — workload profiles (JSON)
- `tools/` — optional helpers
- `.github/workflows/test.yml` — CI sanity run

---

## License

MIT — see `LICENSE`.
