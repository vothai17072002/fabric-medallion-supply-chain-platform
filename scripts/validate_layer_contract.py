#!/usr/bin/env python3
"""Validate the public-safe Fabric layer contract.

The JSON Schema checks structure when the optional ``jsonschema`` dependency is
available. The standard-library semantic checks always run and enforce graph,
release-control, evidence, and portfolio-confidentiality invariants.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any


REQUIRED_LAYERS = ["brz", "sil", "gld", "semantic", "consumption"]
REQUIRED_BLOCKING_CONTROLS = {
    "database_object_manifest",
    "data_quality_gate",
    "schema_drift_check",
    "semantic_binding_check",
    "report_binding_check",
    "security_access_check",
}
SAFETY_FLAGS = {
    "containsRealData",
    "containsCredentials",
    "containsInternalEndpoints",
    "containsTenantOrWorkspaceIdentifiers",
    "containsOrganizationBranding",
}
PROHIBITED_PATTERNS = {
    "GUID-like identifier": re.compile(
        r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b"
    ),
    "Power BI workspace URL": re.compile(r"(?i)app\.powerbi\.com/groups/"),
    "Fabric SQL endpoint": re.compile(
        r"(?i)\b[a-z0-9-]+\.(?:datawarehouse|sql)\.fabric\.microsoft\.com\b"
    ),
    "OneLake endpoint": re.compile(r"(?i)onelake\.dfs\.fabric\.microsoft\.com"),
    "credential assignment": re.compile(
        r"(?i)(?:client_secret|access_token|refresh_token|password)\s*[:=]\s*[^\s,}\]]+"
    ),
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be a JSON object")
    return value


def validate_with_jsonschema(contract: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """Use the standard JSON Schema implementation when installed."""
    try:
        import jsonschema
    except ImportError:
        return ["INFO: optional jsonschema package not installed; semantic checks still ran"]

    try:
        validator_cls = jsonschema.validators.validator_for(schema)
        validator_cls.check_schema(schema)
        validator = validator_cls(schema, format_checker=jsonschema.FormatChecker())
        errors = sorted(validator.iter_errors(contract), key=lambda error: list(error.path))
    except Exception as exc:  # pragma: no cover - protects CI diagnostics
        return [f"JSON Schema validator error: {exc}"]

    return [
        "schema " + "/".join(str(part) for part in error.absolute_path) + f": {error.message}"
        for error in errors
    ]


def validate_acyclic(layer_map: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    state: dict[str, int] = {layer: 0 for layer in layer_map}

    def visit(layer: str, path: list[str]) -> None:
        if state[layer] == 1:
            cycle_start = path.index(layer) if layer in path else 0
            errors.append("dependency cycle: " + " -> ".join(path[cycle_start:] + [layer]))
            return
        if state[layer] == 2:
            return
        state[layer] = 1
        for dependency in layer_map[layer].get("inputLayers", []):
            if dependency in layer_map:
                visit(dependency, path + [layer])
        state[layer] = 2

    for name in layer_map:
        visit(name, [])
    return errors


def validate_semantics(contract: dict[str, Any], raw_text: str) -> list[str]:
    errors: list[str] = []

    if not re.fullmatch(r"\d+\.\d+\.\d+", str(contract.get("contractVersion", ""))):
        errors.append("contractVersion must be semantic version X.Y.Z")

    try:
        date.fromisoformat(contract["evidence"]["snapshotDate"])
    except (KeyError, TypeError, ValueError):
        errors.append("evidence.snapshotDate must be an ISO calendar date")

    targets = contract.get("targetContracts")
    if not isinstance(targets, list):
        errors.append("targetContracts must be an array")
        targets = []

    names = [item.get("layer") for item in targets if isinstance(item, dict)]
    if names != REQUIRED_LAYERS:
        errors.append(f"targetContracts layer order must be {REQUIRED_LAYERS}; found {names}")
    if len(names) != len(set(names)):
        errors.append("targetContracts contains duplicate layer names")

    layer_map = {
        item["layer"]: item
        for item in targets
        if isinstance(item, dict) and item.get("layer") in REQUIRED_LAYERS
    }
    for layer, item in layer_map.items():
        dependencies = item.get("inputLayers", [])
        consumers = item.get("consumers", [])
        for dependency in dependencies:
            if dependency not in layer_map:
                errors.append(f"{layer}: unknown input layer {dependency!r}")
            elif layer not in layer_map[dependency].get("consumers", []):
                errors.append(f"{layer}: input {dependency!r} does not declare {layer!r} as consumer")
        for consumer in consumers:
            if consumer not in layer_map:
                errors.append(f"{layer}: unknown consumer {consumer!r}")
            elif layer not in layer_map[consumer].get("inputLayers", []):
                errors.append(f"{layer}: consumer {consumer!r} does not declare {layer!r} as input")

        freshness = item.get("freshness", {})
        if not str(freshness.get("basis", "")).startswith("proposed_"):
            errors.append(f"{layer}: freshness basis must be explicitly proposed")
        if not isinstance(freshness.get("maximumLagMinutes"), int) or freshness.get("maximumLagMinutes", 0) <= 0:
            errors.append(f"{layer}: freshness.maximumLagMinutes must be a positive integer")
        recovery = item.get("recovery", {})
        for objective in ("rpoHours", "rtoHours"):
            value = recovery.get(objective)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
                errors.append(f"{layer}: recovery.{objective} must be positive")

    errors.extend(validate_acyclic(layer_map))

    controls = contract.get("releaseControls", [])
    control_ids = [item.get("id") for item in controls if isinstance(item, dict)]
    if len(control_ids) != len(set(control_ids)):
        errors.append("releaseControls contains duplicate IDs")
    blocking = {
        item.get("id")
        for item in controls
        if isinstance(item, dict) and item.get("blocking") is True
    }
    missing = REQUIRED_BLOCKING_CONTROLS - blocking
    if missing:
        errors.append("missing required blocking release controls: " + ", ".join(sorted(missing)))

    declared = set(contract.get("validationPolicy", {}).get("requiredBlockingReleaseControls", []))
    if declared != REQUIRED_BLOCKING_CONTROLS:
        errors.append("validationPolicy.requiredBlockingReleaseControls differs from validator policy")

    safety = contract.get("portfolioSafety", {})
    if set(safety) != SAFETY_FLAGS:
        errors.append("portfolioSafety keys must exactly match the required safety flags")
    for flag in SAFETY_FLAGS:
        if safety.get(flag) is not False:
            errors.append(f"portfolioSafety.{flag} must be false for this public artifact")

    for label, pattern in PROHIBITED_PATTERNS.items():
        if pattern.search(raw_text):
            errors.append(f"public contract contains prohibited {label}")

    return errors


def main() -> int:
    repository_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "contract",
        type=Path,
        nargs="?",
        default=repository_root / "architecture" / "layer-contracts.json",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=repository_root / "architecture" / "layer-contracts.schema.json",
    )
    parser.add_argument(
        "--require-jsonschema",
        action="store_true",
        help="Fail when the optional jsonschema package is unavailable",
    )
    args = parser.parse_args()

    try:
        raw_text = args.contract.read_text(encoding="utf-8")
        contract = json.loads(raw_text)
        schema = load_json(args.schema)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    schema_results = validate_with_jsonschema(contract, schema)
    info = [message for message in schema_results if message.startswith("INFO:")]
    errors = [message for message in schema_results if not message.startswith("INFO:")]
    if args.require_jsonschema and info:
        errors.append("jsonschema package is required but unavailable")
    errors.extend(validate_semantics(contract, raw_text))

    for message in info:
        print(message)
    if errors:
        for message in errors:
            print(f"ERROR: {message}", file=sys.stderr)
        return 1

    print(
        f"OK: {args.contract.name} validates against schema and semantic policy "
        f"({len(contract['targetContracts'])} layers, {len(contract['releaseControls'])} release controls)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
