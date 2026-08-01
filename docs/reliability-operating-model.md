# Reliability and operating model

## Status

This is a **proposed target operating model**. Numeric objectives are design starting points for stakeholder approval and measurement; they are not observed production achievements.

## Reliability objectives

| Service-level objective | Proposed target | Measurement window | Primary response on breach |
|---|---:|---|---|
| Scheduled Gold publication success | ≥ 99% | Calendar month | Error-budget review and recurring-failure remediation |
| Publication lag after planned source readiness | ≤ 120 minutes for 95% of runs | Rolling 30 days | Critical-path, source-delay, and capacity analysis |
| Blocking DQ contract coverage at publish | 100% | Every candidate | Fail closed; candidate cannot publish |
| Critical report query latency | P95 ≤ 5 seconds on representative workload | Weekly benchmark and release gate | Model/file-layout/capacity investigation |
| Dev/Prod artifact and binding drift | 0 unapproved differences | Every release and daily audit | Block release or open time-bound exception |

The publication-success error budget is 1% of expected monthly scheduled runs. Source outages and approved maintenance are reported separately, not silently removed; exclusion rules require owner approval so the SLO cannot be gamed.

## Recovery objectives

| Objective | Proposed target | Design dependency |
|---|---:|---|
| RPO for replayable batch data | ≤ one scheduled batch / 24 hours | Retained BRZ input, durable watermarks, versioned artifacts |
| RTO for critical trusted consumption | ≤ 4 hours | Last-known-good Gold version, binding rollback, tested runbooks |
| Containment of rejected candidate | Immediate—no trusted publication change | Separate candidate and publication states |
| Recovery from wrong report/model binding | ≤ 2 hours after detection | Parameterized binding manifest and post-deploy test |

RPO applies to recoverability of accepted source changes, not source-system retention outside the platform's control. RTO begins when the incident is detected and ends when trusted consumption and verification are restored.

## Operating roles

These are accountabilities, not claims about current team titles.

| Role | Accountable for |
|---|---|
| Data Platform Lead | End-to-end reliability, capacity, release policy, cross-domain incident command |
| Domain Data Owner | Business grain, reconciliation tolerance, exception acceptance, data correctness |
| Data Engineering Owner | BRZ/SIL implementation, idempotency, watermark, dependency and recovery behavior |
| Analytics Engineering Owner | Gold dimensional contracts, publication mechanism, downstream compatibility |
| Semantic Model Owner | Relationships, measures, security roles, performance and semantic regression |
| BI Product Owner | Report acceptance, audience, business freshness expectation, decision workflow |
| Release Owner | Artifact manifest, promotion evidence, binding verification and rollback readiness |
| Security/Governance Owner | Least privilege, classification, audit, access review and incident participation |

One person may hold multiple roles in a small team, but no control should have ambiguous accountability.

## RACI for critical changes

| Change | A | R | C | I |
|---|---|---|---|---|
| Source/grain/key contract | Domain Data Owner | Data Engineering | Analytics/Semantic Owners | BI Product Owner |
| Gold publication logic | Analytics Engineering Owner | Analytics Engineering | Data Engineering, Domain Owner | Release Owner |
| Measure behavior | Semantic Model Owner | Semantic Engineering | Domain Owner, BI Product Owner | Report consumers |
| Report/model binding | Release Owner | BI/Semantic Engineering | Platform Lead | BI Product Owner |
| RLS/OLS/access policy | Security/Governance Owner | Semantic/Platform Engineering | Domain and BI Owners | Affected audience |
| Capacity change | Data Platform Lead | Capacity Administrator | Engineering owners | BI Product Owner |
| DQ exception | Domain Data Owner | Owning engineer | Platform Lead | BI Product Owner, Release Owner |

## Incident model

1. **Detect:** alert includes impact, business dates, last-known-good version, owner, and runbook.
2. **Contain:** freeze publication/binding when correctness or authorization is uncertain.
3. **Restore:** prefer scoped rerun or last-known-good rollback over a full rebuild.
4. **Prove:** rerun DQ, reconciliation, binding, access, and representative-query checks.
5. **Learn:** document root cause, contributing controls, SLO impact, owner, and due date.

### Severity guide

- **SEV-1:** unauthorized or materially incorrect data is actively consumable.
- **SEV-2:** critical publication unavailable or freshness likely to exceed RTO/SLO.
- **SEV-3:** candidate failed while last-known-good consumption remains within objective.

## Change and release policy

- Breaking layer, grain, key, or measure changes require an ADR and migration plan.
- Every release is tied to immutable artifact and contract versions.
- Pull-request evidence includes contract validation, dependency/drift result, test outcome, security impact, and rollback path.
- Production deployment requires named Release Owner and Domain/Semantic acceptance for affected contracts.
- An emergency change is followed by the same evidence and review within the next business day.

## Review cadence

| Cadence | Review |
|---|---|
| Per run | DQ coverage, publication state, freshness, critical-path duration |
| Weekly | Recurring failures, query benchmark, capacity/throttling, unresolved quarantine |
| Monthly | SLO/error budget, access exceptions, Dev/Prod drift, remediation roadmap |
| Quarterly | RTO/RPO exercise, capacity forecast, contract ownership and ADR revisit triggers |

An SLO is useful only when measurement, ownership, and a decision triggered by breach are all defined.
