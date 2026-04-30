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
- `speedtest-web`

## Active Layout

```text
tools/amd-apu-toolkit
apps/speedtest-web
```

## Notes

Additional benchmarking and monitoring repos were imported during consolidation work and later removed from this monorepo by request.
