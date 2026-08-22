# Greenmile Benchmark Methodology

Greenmile does not ship hardcoded performance claims. The Performance Lab invokes `POST /api/benchmarks`; every returned value is measured and stored in PostgreSQL.

## Workloads

Deterministic workloads contain 100, 500, 1,000, or 5,000 stops drawn reproducibly from the seeded scenario. The API records the scenario ID, generator version, stop count, algorithm names, and timestamp.

## Comparison

- **Baseline:** separate closed delivery and return routes.
- **Optimized:** clustered, combined bidirectional routes using nearest neighbour and bounded 2-opt.

For each requested workload, the runner executes both algorithms for the requested repetition count and records:

- median baseline and optimized latency;
- optimized p50, p95, and p99 latency;
- baseline and optimized route distance;
- route-quality delta;
- constraint violation count;
- process resident memory;
- individual optimized timing samples.

## Correct interpretation

A speed improvement is credible only alongside route quality and constraint results. A positive route-quality delta means the optimized route is longer than the comparison route; this must not be hidden. The current routing provider is Haversine, so distances are great-circle estimates rather than road distances.

## Reproduce

```bash
docker compose up --build -d
curl -X POST http://localhost:8000/api/benchmarks \
  -H 'Content-Type: application/json' \
  -d '{"workloads":[100,500,1000,5000],"repetitions":3}'
```

Machine, Docker resource allocation, active background processes, and provider configuration affect latency. Record those details with any published result; do not copy example numbers from design documents.
