# Security and governance architecture

## Status and scope

This document defines a **proposed control model** for the sanitized architecture. The metadata assessment did not verify tenant policies, actual classifications, network configuration, identities, or RLS/OLS definitions; those remain deployment-time evidence requirements.

## Security principles

- Human collaboration permissions and workload identities are separate.
- Admin/Member/Contributor workspace roles are not report-audience roles.
- Grant the narrowest workspace, item, table/folder, row, column, and export access supported by the selected Fabric path.
- Apply policy at the earliest enforceable boundary and test it through every supported query/export path.
- Secrets and environment IDs live in managed connections or deployment configuration, never source artifacts.
- A failed or unknown access test blocks promotion of the affected data product.

## Identity and access matrix

| Persona/identity | Target access | Explicit restriction |
|---|---|---|
| Ingestion workload identity | Write BRZ landing boundary and run audit | No report access or semantic authoring |
| Transformation workload identity | Read declared BRZ inputs; write owned SIL targets | No cross-domain write outside manifest |
| Publication workload identity | Read approved SIL; write Gold candidate/control state | Cannot change DQ contracts or self-approve exceptions |
| Semantic deployment identity | Deploy model and target binding | No broad source-data browsing |
| Analyst/report consumer | App/report plus governed semantic permissions | No workspace Contributor role solely for consumption |
| Platform administrator | Time-bound administration and incident access | Privileged activity logged and reviewed |

Use Entra groups or nonhuman security principals for repeatable assignment. Avoid direct per-user grants except documented, expiring exceptions.

## Data-plane and semantic controls

1. Classify domains and columns before deciding the access mechanism.
2. Validate how workspace/item permissions interact with OneLake or SQL-path controls in the selected architecture.
3. Apply row, column, or object security at the governed boundary and verify every consumer path.
4. Keep semantic-model roles and user-to-role mappings versioned and regression tested.
5. Test “deny” cases as well as allowed cases, including exports and downstream reports.

Direct Lake security behavior depends on the selected mode and underlying access path. SQL endpoint security, OneLake security, and semantic security are not interchangeable; ADR 004 requires the release manifest to declare the chosen model.

## Classification and protection

| Classification | Example handling pattern |
|---|---|
| Public | May appear in sanitized documentation after review |
| Internal | Authenticated workforce access; no public export |
| Confidential | Named business purpose, least privilege, sensitivity label, export review |
| Restricted | Fine-grained access, explicit owner approval, enhanced audit and incident path |

The public repo is constrained to synthetic examples and aggregate architecture counts. Automated validation rejects GUID-like identifiers, credentials, and internal URL patterns in the canonical contract.

## Secrets and deployment configuration

- Managed connections or approved secret stores own credentials.
- Separate identities and bindings exist per environment.
- Rotation is tested without code change.
- CI logs redact connection material and do not echo tokens.
- Deployment manifests refer to logical environment aliases, not public tenant/workspace IDs.

## Governance evidence

Each release should retain:

- source-to-report lineage and affected consumers;
- contract and artifact versions;
- classification/sensitivity decision;
- role and deny-case test results;
- semantic/report binding evidence;
- exception owner, reason, expiry, and compensating control;
- privileged deployment identity and audit correlation ID.

## Security review gates

| Change | Required review |
|---|---|
| New source or sensitive column | Classification, purpose, minimization, retention, access paths |
| New shortcut/query path | Producer and consumer authorization behavior |
| RLS/OLS/CLS change | Positive/negative role matrix and performance regression |
| Report export/share change | Audience and downstream protection |
| Git/deployment integration | Inbound/outbound network policy and workload identity scope |
| Public portfolio update | Secret/identifier scan and human confidentiality review |

## Incident response

If unauthorized or incorrect restricted data is consumable: remove or contain audience access, freeze publication, preserve audit evidence, notify the accountable security/data owners, restore the prior trusted state, and complete a documented impact assessment. Correctness and access incidents share the same release correlation IDs so data and security timelines can be reconstructed.

## Reference points

- [Microsoft Fabric security overview](https://learn.microsoft.com/fabric/security/security-overview)
- [Secure data in OneLake](https://learn.microsoft.com/fabric/onelake/security/best-practices-secure-data-in-onelake)
- [Microsoft Fabric lineage](https://learn.microsoft.com/fabric/governance/lineage)
- [Fabric CI/CD network security](https://learn.microsoft.com/fabric/cicd/cicd-security)

Feature availability and limitations must be revalidated against the target tenant at implementation time.
