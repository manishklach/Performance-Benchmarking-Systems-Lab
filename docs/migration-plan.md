# Migration Plan

## Import Targets

1. `amd-apu-toolkit`
2. `reliable-gpu-kernel-bench`
3. `Codex-Agent-Monitor`
4. `speedtest-web`
5. `hbf-ready-bench`
6. `Windows-Kernel-Monitor`

## Current Status

- `amd-apu-toolkit` has been imported into `tools/amd-apu-toolkit` with preserved git history.
- `speedtest-web` has been imported into `apps/speedtest-web` with preserved git history.
- `reliable-gpu-kernel-bench` has been imported into `benchmarks/reliable-gpu-kernel-bench` with preserved git history.
- `Codex-Agent-Monitor` has been imported into `apps/Codex-Agent-Monitor` with preserved git history.
- `hbf-ready-bench` has been imported into `benchmarks/hbf-ready-bench` with preserved git history.
- `Windows-Kernel-Monitor` has been imported into `tools/Windows-Kernel-Monitor` with preserved git history.

## Recommended Steps

1. Create shared documentation for benchmark conventions, naming, and output formats.
2. Decide whether each imported project remains independently releasable or becomes monorepo-native.
