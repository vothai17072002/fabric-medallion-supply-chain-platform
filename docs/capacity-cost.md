# Capacity, performance, and cost design

## Status

No capacity SKU, CU history, data volume, file layout, batch duration, or production query latency was included in the sanitized observation. This document is a **measurement and decision framework**, not a capacity-sizing claim.

## Workload classes

| Workload | Demand shape | Principal contention risk | Primary SLI |
|---|---|---|---|
| BRZ ingestion | Source-arrival bursts | Copy/ingest overlapping critical transformations | Ingest lag and CU/time |
| SIL transformation | Batch, join and history intensive | Warehouse concurrency and long critical path | Duration, queue/throttling, rows/CU |
| Gold publication | Bounded aggregate/dimensional build | Competing with report queries | Publish duration and reconciliation time |
| Direct Lake semantic query | Interactive and bursty | File/row-group guardrails, memory and concurrent users | P50/P95 latency, query failures/fallback where applicable |
| Backfill | Large but schedulable | Starving daily publication and interactive workloads | Backfill throughput within daily SLO |

## Capacity design loop

1. Capture at least 30 representative days including period-end and planning peaks.
2. Separate background and interactive operations by item and time window.
3. Establish baseline CU, duration, queue, throttling, query latency, and storage growth.
4. Find the critical path and the highest-cost transforms before increasing capacity.
5. Test scheduling, partition pruning, materialization, file layout, and concurrency limits.
6. Scale only when optimization cannot meet the approved reliability/performance envelope.
7. Re-measure cost per successful publication and representative query workload.

## Direct Lake guardrails

The release evidence should record:

- selected Direct Lake mode and permitted fallback/failure behavior;
- table row, file, and row-group distribution against the capacity guardrails;
- framing or automatic-update policy;
- effect of security features and views on storage-mode behavior;
- representative cold/warm query benchmarks;
- model memory and concurrent-user behavior;
- maintenance such as compaction/optimization where supported and justified.

One oversized or fragmented table can affect the model-wide operating envelope. Guardrail checks belong in release/operations evidence, not a one-time design review.

## Cost and performance levers

| Lever | Benefit | Trade-off / evidence needed |
|---|---|---|
| Dependency-safe parallelism | Shorter critical path | Higher peak CU and contention risk |
| Partition-bounded rebuild | Lower recovery work | More metadata and correctness complexity |
| Materialize reused Silver logic | Reduce repeated compute | Storage, freshness and lifecycle cost |
| Gold pre-aggregation | Faster common queries | Additional reconciliation and less drill detail |
| File compaction/layout optimization | Better scan/model behavior | Maintenance compute and schedule |
| Schedule background work off peak | Protect interactive workload | Longer source-to-publish window |
| Capacity scale/autoscale | More headroom | Direct recurring or burst cost |
| Split shared semantic model | Isolate ownership/workload | Duplicate dimensions/measures and cross-model UX |

## Scale triggers

Investigate optimization or scale when any of these persist across representative windows:

- publication lag consumes more than 75% of the 120-minute objective;
- throttling or queue time contributes more than 20% of critical-path duration;
- representative query P95 exceeds five seconds after model/query tuning;
- backfills cannot complete without risking the next scheduled publication;
- a table approaches the declared Direct Lake guardrail headroom;
- monthly CU per successful publication rises materially without matching volume/complexity growth.

Percentages are proposed decision thresholds, not observed metrics.

## Cost governance

- Tag operations by domain, environment, run type, and release version where telemetry permits.
- Report engineering/background and interactive consumption separately.
- Require expected CU/runtime impact for large backfills and breaking model changes.
- Review unused duplicates, retained candidates, quarantine, and soft-deleted storage.
- Treat capacity increases as an ADR with measured baseline, options, expected benefit, and rollback/review date.

## Benchmark protocol

Use a fixed, synthetic-safe workload covering common overview queries, high-cardinality slices, period comparisons, and worst-case drill paths. Run cold and warm tests, record concurrency and capacity state, and compare against the same artifact/data snapshot. A performance result without workload, environment, and capacity context is not portable evidence.

## Reference points

- [Fabric Capacity Metrics app](https://learn.microsoft.com/fabric/enterprise/metrics-app)
- [How Direct Lake works](https://learn.microsoft.com/fabric/fundamentals/direct-lake-how-it-works)
- [Monitor Fabric Data Factory runs](https://learn.microsoft.com/fabric/data-factory/monitor-data-factory)
