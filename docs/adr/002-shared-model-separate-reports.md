# ADR 002: Share the semantic model and separate report experiences

- **Status:** Documented case-study decision
- **Evidence:** One shared model and two reports observed; trade-off analysis is inferred
- **Decision date:** 2026-08-01

## Context

Forecast Accuracy and Inventory Health reuse Calendar, Product, Warehouse, relationships, and governed metric conventions, but support distinct users and decision flows.

## Decision

Keep one shared semantic contract while maintaining separate report experiences. The model owns relationships, measures, formatting, security behavior, descriptions, and compatibility. Reports own navigation, hierarchy, interaction, and domain narrative.

## Alternatives considered

1. **Independent models:** stronger release/security isolation, but duplicated conformed logic and reconciliation burden.
2. **One combined report:** fewer artifacts, but a broader and less focused user journey.
3. **Composite/thin-report variants:** useful when ownership or scale changes, but add dependency and release complexity.

## Consequences

Positive: consistent KPIs and dimensions, lower duplication, cross-domain governance. Cost: a large measure surface, coordinated releases, and shared capacity/blast radius.

## Revisit trigger

Split when domain security cannot be expressed safely, ownership/release cadence diverges, model guardrails or query SLOs are repeatedly breached, or change failure in one domain unnecessarily blocks the other.
