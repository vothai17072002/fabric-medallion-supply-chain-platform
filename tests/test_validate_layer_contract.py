from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.validate_layer_contract import validate_semantics, validate_with_jsonschema


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "architecture" / "layer-contracts.json"
SCHEMA_PATH = ROOT / "architecture" / "layer-contracts.schema.json"


class LayerContractValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw_text = CONTRACT_PATH.read_text(encoding="utf-8")
        cls.contract = json.loads(cls.raw_text)
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_canonical_contract_passes_structural_and_semantic_validation(self) -> None:
        schema_errors = [
            message
            for message in validate_with_jsonschema(self.contract, self.schema)
            if not message.startswith("INFO:")
        ]
        self.assertEqual([], schema_errors)
        self.assertEqual([], validate_semantics(self.contract, self.raw_text))

    def test_dependency_cycle_fails(self) -> None:
        contract = copy.deepcopy(self.contract)
        by_layer = {item["layer"]: item for item in contract["targetContracts"]}
        by_layer["brz"]["inputLayers"] = ["consumption"]
        by_layer["consumption"]["consumers"] = ["brz"]

        errors = validate_semantics(contract, json.dumps(contract))

        self.assertTrue(any("dependency cycle" in error for error in errors))

    def test_missing_blocking_release_control_fails(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["releaseControls"] = [
            item for item in contract["releaseControls"] if item["id"] != "data_quality_gate"
        ]

        errors = validate_semantics(contract, json.dumps(contract))

        self.assertTrue(any("missing required blocking" in error for error in errors))

    def test_public_safety_flag_must_fail_closed(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["portfolioSafety"]["containsCredentials"] = True

        errors = validate_semantics(contract, json.dumps(contract))

        self.assertTrue(any("containsCredentials must be false" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
