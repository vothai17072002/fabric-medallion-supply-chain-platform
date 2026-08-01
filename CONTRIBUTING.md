# Contribution and change governance

This public case study is managed as an architecture product. Changes should make a decision, contract, test, or evidence boundary clearer rather than add volume.

1. Classify material claims as `Observed`, `Inferred`, `Illustrative`, or `Proposed` and date observed snapshots.
2. Record structural decisions and rejected alternatives in an ADR before changing a published contract.
3. Update data, orchestration, security, test, and recovery contracts together when their behavior changes.
4. Preserve backward compatibility or document the consumer migration and rollback path.
5. Use synthetic content only; never commit tenant IDs, endpoints, real values, screenshots, exports, or BI binaries.
6. Run `python -m pip install -r requirements-dev.txt`, `python scripts/validate_portfolio.py`, and `python scripts/validate_layer_contract.py` before requesting review.

Approval is based on decision clarity, operational safety, test evidence, and confidentiality—not document length.
