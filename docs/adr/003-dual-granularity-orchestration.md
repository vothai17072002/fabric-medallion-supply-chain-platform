# ADR 003: One dependency manifest, two orchestration views

- **Status:** Target-state recommendation based on observed pipelines
- **Evidence:** 9-step wrapper and 45-activity graph observed
- **Decision date:** 2026-08-01

## Context

A coarse wrapper is easy to operate; a table-level graph improves isolation, parallelism, and scoped recovery. Maintaining them independently creates drift.

## Decision

Retain both views but generate or validate them from one versioned dependency manifest. The wrapper is the supported operator entry point; the fine graph is the execution and recovery truth.

## Alternatives considered

1. **Wrapper only:** simple but broad reruns and weak diagnostics.
2. **Fine graph only:** precise but harder for operators and domain coordination.
3. **Dynamic orchestration without manifest validation:** flexible but difficult to review and reproduce.

## Consequences

Positive: simple operation, targeted recovery, dependency-safe parallelism. Cost: manifest tooling, graph validation, and stable activity contracts.

## Revisit trigger

Revisit when graph generation becomes more complex than the workload, activity overhead dominates runtime, or independent domain schedules require separate orchestration products.
