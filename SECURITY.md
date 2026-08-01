# Security and confidentiality policy

## Supported content

The `main` branch is the supported public portfolio version. This repository contains synthetic controls and sanitized architecture documentation only; it is not a production deployment package.

## Reporting a concern

Report a suspected credential, confidential identifier, unsafe example, or repository vulnerability privately through GitHub's security-reporting channel when available. If private reporting is unavailable, contact the repository owner through GitHub without including sensitive details in a public issue.

Include the affected path, risk, safe reproduction detail, and suggested containment. Do not copy real data, secrets, internal URLs, tenant/workspace identifiers, or employer material into the report.

## Portfolio confidentiality boundary

Public content must not include:

- real company or personal data;
- credentials, tokens, connection strings, or private endpoints;
- tenant, workspace, item, request, or correlation identifiers;
- organization branding or proprietary expressions/artifact exports;
- `.pbix`, `.pbit`, `.bim`, `.abf`, or production Fabric definitions.

The CI validator performs fail-closed checks for common sensitive patterns and forbidden BI artifacts. Automated scanning complements, but does not replace, human confidentiality review.

## Public-release checklist

Before publication, follow [`CONTRIBUTING.md`](CONTRIBUTING.md) and the repository [pull-request checklist](.github/pull_request_template.md). Run both the general portfolio validator and the architecture-contract validator; a passing scan is required evidence, not permission to publish material whose ownership or confidentiality is uncertain.

## Architecture security

The target identity, least-privilege, data-plane, semantic, classification, release, and incident controls are documented in [`docs/security-governance.md`](docs/security-governance.md). They are proposed controls unless accompanied by target-environment deployment evidence.
