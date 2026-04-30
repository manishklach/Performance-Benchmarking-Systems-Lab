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
- The other listed repositories are not present in this workspace yet.

## Recommended Steps

1. Add missing repositories once their source locations are available.
2. Create shared documentation for benchmark conventions, naming, and output formats.
3. Decide whether each imported project remains independently releasable or becomes monorepo-native.
