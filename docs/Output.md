# Sample Outputs
These are example runs captured on Windows.



## One-command benchmark (bench.py)

.\\.venv\\Scripts\\python.exe .\\bench.py

======================================================================================================================

Agentic CPU Bottleneck Bench — Benchmark Table

======================================================================================================================

workload     agents       steps        p50\_ms       p95\_ms       cpu\_util     cpu\_ms       io\_wait\_ms   parse\_ms     json\_kb      ctx\_sw

reasoning\_heavy 32           200          3.43         828.03       0.991        3.04         1.79         0.05         24.83        1638

action\_heavy 32           200          41.24        119.99       0.943        1.02         19.38        0.03         17.30        150

mixed        32           200          2.95         208.86       0.975        1.62         7.58         0.03         14.83        133

======================================================================================================================

Tip: vary fan-out to see CPU vs wait-bound behavior:

&nbsp; python run\_bench.py --workload workloads/mixed.json --agents 8 --steps 200

&nbsp; python run\_bench.py --workload workloads/mixed.json --agents 64 --steps 200

======================================================================================================================


## agents=8, workload=reasoning\_heavy

.\\.venv\\Scripts\\python.exe .\\run\_bench.py --workload workloads\\reasoning\_heavy.json --agents 8 --steps 200

==============================================================================================================

Agentic CPU Bottleneck Bench — Run Summary

==============================================================================================================

Workload: reasoning\_heavy  | agents=8 steps/agent=200

p50\_ms=3.46  p95\_ms=189.65  cpu\_util=0.987

cpu\_ms/step=3.07  io\_wait\_ms/step=1.89  parse\_ms/step=0.05  json\_kb/step=24.76

ctx\_switches(delta)=104

==============================================================================================================

## agents=64, workload=reasoning\_heavy

.\\.venv\\Scripts\\python.exe .\\run\_bench.py --workload workloads\\reasoning\_heavy.json --agents 64 --steps 200

==============================================================================================================

Agentic CPU Bottleneck Bench — Run Summary

==============================================================================================================

Workload: reasoning\_heavy  | agents=64 steps/agent=200

p50\_ms=3.40  p95\_ms=1542.77  cpu\_util=0.994

cpu\_ms/step=2.99  io\_wait\_ms/step=1.95  parse\_ms/step=0.04  json\_kb/step=24.71

ctx\_switches(delta)=1331

==============================================================================================================

## agents=8, workload=action\_heavy

.\\.venv\\Scripts\\python.exe .\\run\_bench.py --workload workloads\\action\_heavy.json --agents 8 --steps 200

==============================================================================================================

Agentic CPU Bottleneck Bench — Run Summary

==============================================================================================================

Workload: action\_heavy  | agents=8 steps/agent=200

p50\_ms=13.29  p95\_ms=71.00  cpu\_util=0.571

cpu\_ms/step=1.01  io\_wait\_ms/step=19.52  parse\_ms/step=0.05  json\_kb/step=17.54

ctx\_switches(delta)=686

==============================================================================================================

## agents=64, workload=action\_heavy

.\\.venv\\Scripts\\python.exe .\\run\_bench.py --workload workloads\\action\_heavy.json --agents 64 --steps 200

==============================================================================================================

Agentic CPU Bottleneck Bench — Run Summary

==============================================================================================================

Workload: action\_heavy  | agents=64 steps/agent=200

p50\_ms=96.92  p95\_ms=252.13  cpu\_util=0.956

cpu\_ms/step=1.01  io\_wait\_ms/step=18.92  parse\_ms/step=0.04  json\_kb/step=17.20

ctx\_switches(delta)=3613

==============================================================================================================









