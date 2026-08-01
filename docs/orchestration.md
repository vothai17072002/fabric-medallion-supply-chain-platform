# Orchestration design

## Domain wrapper pipeline

The coarse-grained pipeline provides a simple operational runbook:

1. Refresh shared references.
2. Build Forecast Silver across three dependency waves.
3. Publish Forecast Gold.
4. Build Inventory Silver across three dependency waves.
5. Publish Inventory Gold.

This path is easy to operate but mostly sequential, so it favors clarity and dependency safety over maximum runtime parallelism.

## Per-table pipeline

The fine-grained pipeline expands the same graph into 45 activities. Independent reference tables start together; downstream facts wait for required dimensions and upstream histories. It supports:

- targeted reruns;
- table-level failure isolation;
- explicit dependency review;
- finer runtime and SLA measurement;
- controlled parallelism within each wave.

## Load patterns

| Pattern | Best fit | Required controls |
|---|---|---|
| Full refresh | Small dimensions and deterministic aggregates | Atomic publish or swap |
| Incremental append | Immutable event/snapshot data | Watermark and duplicate protection |
| Date-range replace | Late-arriving facts | Bounded delete/merge and reconciliation |
| Metadata-driven table load | Repeated view-to-table materialization | Validated dictionary and audit log |

## Recovery model

- Each activity records run ID, target object, start/end time, row count, and status.
- Reruns are idempotent at the declared load boundary.
- Gold publication waits for Silver completeness and quality gates.
- A failed Gold publish leaves the last trusted version consumable.
- Target environment and semantic/report bindings are validated after deployment.

## CI/CD controls

1. Compare required schemas, views, tables, and procedures between environments.
2. Deploy database objects before pipelines that call them.
3. Validate connections without embedding endpoints in source.
4. Run DQ and reconciliation checks.
5. Validate semantic model table bindings.
6. Validate report-to-semantic-model bindings.
