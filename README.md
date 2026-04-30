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

## Current Projects

- `amd-apu-toolkit`
- `agentic_cpu_bottleneck_bench`
- `reliable-gpu-kernel-bench`
- `Codex-Agent-Monitor`
- `speedtest-web`
- `hbf-ready-bench`
- `Windows-Kernel-Monitor`

## Active Layout

```text
apps/Codex-Agent-Monitor
benchmarks/hbf-ready-bench
benchmarks/agentic_cpu_bottleneck_bench
benchmarks/reliable-gpu-kernel-bench
tools/amd-apu-toolkit
apps/speedtest-web
tools/Windows-Kernel-Monitor
```

## Notes

Standalone repositories were consolidated here with history preserved. The master repo is the source of truth for these projects.
