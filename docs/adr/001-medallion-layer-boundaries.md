# ADR 001: Treat BRZ, SIL, and GLD as contracts

- **Status:** Documented case-study decision
- **Evidence:** Layer topology observed; rationale and controls are architectural analysis
- **Decision date:** 2026-08-01

## Context

The inspected platform separates a source-aligned lakehouse, processing warehouse, and serving warehouse. Layer names alone do not prevent duplicated logic, unstable grain, or unclear ownership.

## Decision

Keep the three boundaries only where each owns a distinct contract:

- BRZ: replayable source grain and ingestion evidence;
- SIL: governed keys, history, snapshots, and reusable domain rules;
- GLD: versioned dimensional publication for consumption.

Promotion across a boundary requires declared grain, keys, load semantics, quality, freshness, classification, and owner role.

## Alternatives considered

1. **BRZ directly to semantic model:** fewer objects, but source volatility and metric coupling move into consumption.
2. **Single transformation/serving warehouse:** simpler deployment, but reusable history and report-serving changes share one blast radius.
3. **More domain-specific layers:** stronger isolation, but unnecessary operational overhead until ownership or scale proves the need.

## Consequences

Positive: replayability, reusable history, stable marts, clearer failure containment. Cost: more artifacts, deployment ordering, reconciliation, and contract governance.

## Revisit trigger

Revisit a boundary when it is a pure pass-through, duplicates another layer's logic, cannot meet RTO, or has independent ownership/security/scale needs that justify a split.
