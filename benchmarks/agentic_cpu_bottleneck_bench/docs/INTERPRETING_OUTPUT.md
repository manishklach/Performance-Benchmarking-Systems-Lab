# Interpreting Output

This benchmark is a *control-plane* simulator: it measures agent-loop overhead, not model quality.

## Reading the table

- `p50_ms`, `p95_ms`  
  Median and tail latency per **agent step** (across all agents and steps).

- `cpu_util`  
  `process_cpu_time / wall_time` for the run. Rough proxy for CPU saturation:
  - near 1.0 on a single core means the process is CPU-bound
  - lower values with high p95 often indicate wait/coordination overhead

- `cpu_ms`  
  CPU time spent per step (planning + parsing + memory ops + scheduling overhead).

- `io_wait_ms`  
  Simulated wait time due to “tool calls” (RPC/I/O). When this dominates, p95 can grow even when CPU isn’t saturated.

- `parse_ms` and `json_kb`  
  Serialization cost. If parse is significant, batching or using binary codecs often helps.

## What “CPU bottleneck” looks like

1. **CPU-bound orchestration**  
   - high `cpu_util`
   - rising p50 and p95 as `--agents` increases
   - `cpu_ms` is a big fraction of `p50_ms`

2. **Wait-bound orchestration**  
   - lower `cpu_util`
   - high p95 due to tool-call waits + concurrency contention
   - `io_wait_ms` dominates

3. **Mixed bottleneck**  
   - both `cpu_util` and `io_wait_ms` are high
   - often seen in “action-heavy” workloads under fan-out

## Next improvements
- Add real HTTP calls behind a `--real-net` flag
- Add NUMA awareness (pin agents to workers)
- Add queue-depth + backpressure metrics for “agent storm” scenarios
