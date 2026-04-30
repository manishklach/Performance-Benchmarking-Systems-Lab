# Migration Plan

## Import Targets

1. `amd-apu-toolkit`
2. `agentic_cpu_bottleneck_bench`
3. `reliable-gpu-kernel-bench`
4. `Codex-Agent-Monitor`
5. `speedtest-web`
6. `hbf-ready-bench`
7. `Windows-Kernel-Monitor`

## Current Status

- `amd-apu-toolkit` has been imported into `tools/amd-apu-toolkit` with preserved git history.
- `agentic_cpu_bottleneck_bench` has been imported into `benchmarks/agentic_cpu_bottleneck_bench` with preserved git history.
- `speedtest-web` has been imported into `apps/speedtest-web` with preserved git history.
- `reliable-gpu-kernel-bench` was imported and later removed from this monorepo by request.
- `Codex-Agent-Monitor` was imported and later removed from this monorepo by request.
- `hbf-ready-bench` was imported and later removed from this monorepo by request.
- `Windows-Kernel-Monitor` was imported and later removed from this monorepo by request.

## Recommended Steps

1. Decide whether to keep the repo focused on the remaining active projects or repurpose it further.
2. Add a clearer top-level project index if more projects are introduced later.
