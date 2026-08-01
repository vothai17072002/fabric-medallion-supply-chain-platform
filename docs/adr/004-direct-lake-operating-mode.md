# ADR 004: Make Direct Lake mode an explicit release decision

- **Status:** Decision framework; target setting not observed
- **Evidence:** Direct Lake model observed; detailed mode, guardrails, and fallback settings not verified
- **Decision date:** 2026-08-01

## Context

Direct Lake can reduce duplicate import-refresh movement, but operating behavior depends on the selected Direct Lake path, capacity guardrails, file layout, framing, security, and fallback/failure settings.

## Decision

Keep Direct Lake as the intended consumption pattern, but require every environment manifest to declare:

- Direct Lake mode/path;
- framing or automatic-update behavior;
- permitted fallback or fail behavior;
- security enforcement path;
- file/row-group/row guardrail checks;
- representative performance test and capacity context.

No repo statement should claim a specific unobserved setting.

## Alternatives considered

1. **Import:** predictable cached performance but duplicates data and requires refresh capacity/window.
2. **DirectQuery:** current source results but more source latency/concurrency dependency.
3. **Hybrid/composite design:** workload flexibility but greater semantic and test complexity.

## Consequences

Positive: low-latency governed consumption with explicit operating evidence. Cost: ongoing guardrail, capacity, security, and query monitoring.

## Revisit trigger

Revisit on repeated fallback/failure, guardrail pressure, P95 breach, security incompatibility, unacceptable capacity cost, or a workload that benefits from deliberate import/aggregation.
