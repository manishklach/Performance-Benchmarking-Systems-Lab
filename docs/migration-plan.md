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
- `reliable-gpu-kernel-bench` was imported and later removed from this monorepo by request.
- `Codex-Agent-Monitor` was imported and later removed from this monorepo by request.
- `hbf-ready-bench` was imported and later removed from this monorepo by request.
- `Windows-Kernel-Monitor` was imported and later removed from this monorepo by request.

## Recommended Steps

1. Decide whether to keep the repo focused on the remaining active projects or repurpose it further.
2. Add a clearer top-level project index if more projects are introduced later.
