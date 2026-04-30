# Migration Plan

## Import Targets

1. `amd-apu-toolkit`
2. `reliable-gpu-kernel-bench`
3. `Codex-Agent-Monitor`
4. `speedtest-web`
5. `hbf-ready-bench`
6. `Windows-Kernel-Monitor`

## Current Status

- `amd-apu-toolkit` exists locally as a standalone git repository.
- `speedtest-web` exists locally as a standalone git repository.
- The other listed repositories are not present in this workspace yet.

## Recommended Steps

1. Import existing local repositories with preserved history.
2. Add missing repositories once their source locations are available.
3. Create shared documentation for benchmark conventions, naming, and output formats.
4. Decide whether each imported project remains independently releasable or becomes monorepo-native.
