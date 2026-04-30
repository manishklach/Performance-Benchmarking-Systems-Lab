# Performance Benchmarking Systems Lab

Performance Benchmarking Systems Lab is the central monorepo for a collection of benchmarking, monitoring, telemetry, and systems-performance projects focused on practical measurement, reproducible evaluation, and developer-facing tooling.

It brings together GPU and CPU benchmark harnesses, agent-runtime performance analysis, Windows and AMD APU monitoring utilities, and web-based diagnostics into one source of truth with preserved project history. The goal is to make it easier to compare experiments, share conventions, reuse supporting code, and evolve related performance tools under a single repository.

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
