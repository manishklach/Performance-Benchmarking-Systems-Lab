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
- `reliable-gpu-kernel-bench` has been restored in `benchmarks/reliable-gpu-kernel-bench` and remains part of this monorepo.
- `Codex-Agent-Monitor` has been restored in `apps/Codex-Agent-Monitor` and remains part of this monorepo.
- `speedtest-web` has been imported into `apps/speedtest-web` with preserved git history.
- `hbf-ready-bench` has been restored in `benchmarks/hbf-ready-bench` and remains part of this monorepo.
- `Windows-Kernel-Monitor` has been restored in `tools/Windows-Kernel-Monitor` and remains part of this monorepo.

## Recommended Steps

1. Keep the monorepo README and project index aligned with the active project set.
2. Add shared benchmark conventions and contribution guidance when you want to standardize the projects further.
