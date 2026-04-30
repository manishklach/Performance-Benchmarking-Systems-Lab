# Performance Benchmarking Systems Lab

Performance Benchmarking Systems Lab is a master monorepo for benchmarking, monitoring, and systems-performance projects.

## Goals

- Keep related benchmarking and observability projects in one place.
- Make shared scripts, docs, and experiment notes easier to maintain.
- Preserve room for both standalone tools and cross-project workflows.

## Repository Layout

```text
apps/         User-facing apps and dashboards
benchmarks/   Performance, kernel, GPU, and reliability benchmarks
tools/        Utility projects, monitors, and supporting CLIs
shared/       Common code, schemas, and reusable assets
docs/         Design notes, runbooks, and migration plans
```

## Planned Project Imports

- `amd-apu-toolkit`
- `reliable-gpu-kernel-bench`
- `Codex-Agent-Monitor`
- `speedtest-web`
- `hbf-ready-bench`
- `Windows-Kernel-Monitor`

## Suggested Initial Placement

```text
tools/amd-apu-toolkit
benchmarks/reliable-gpu-kernel-bench
apps/Codex-Agent-Monitor
apps/speedtest-web
benchmarks/hbf-ready-bench
tools/Windows-Kernel-Monitor
```

## Import Strategy

Use subtree-style imports or history-preserving migrations so each project can move into this repo without losing commit history.
