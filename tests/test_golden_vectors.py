"""
Golden Vectors Parity Test Suite.
Validates that Python risk and decision engines match the golden vector specifications exactly.
"""

import json
import os
import pytest
from engines.risk import calculate_risk
from engines.decide import make_decision
import yaml

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN_PATH = os.path.join(ROOT_DIR, "tests", "golden_vectors.json")
RULES_PATH = os.path.join(ROOT_DIR, "config", "rules.yaml")


def load_fixtures():
    with open(GOLDEN_PATH, "r", encoding="utf-8") as f:
        vectors = json.load(f)
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return vectors, cfg


def test_golden_vectors_parity():
    vectors, cfg = load_fixtures()

    for v in vectors:
        inp = v["input"]
        exp = v["expected"]

        # Run risk calculation
        risk_res = calculate_risk(
            answers={
                "used_any_cream": inp.get("used_any_cream", "NOT_SURE"),
                "prescribed_by_clinician": inp.get("prescribed_by_clinician", "NOT_SURE"),
                "steroid_name_visible": inp.get("steroid_name_visible", "NOT_SURE"),
                "combination_wording": inp.get("combination_wording", "NOT_SURE"),
                "returned_after_stopping": inp.get("returned_after_stopping", "NOT_SURE"),
                "spread_despite_treatment": inp.get("spread_despite_treatment", "NOT_SURE"),
                "itchy_ring_or_scaly": inp.get("itchy_ring_or_scaly", "NOT_SURE"),
                "duration": inp.get("duration", "NOT_SURE")
            },
            model_output={
                "top_pattern": inp.get("pattern_model", {}).get("top_class", ""),
                "strength": inp.get("pattern_model", {}).get("strength", ""),
                "ensemble_compatible": inp.get("pattern_model", {}).get("strength") in ("Strong", "Moderate")
            },
            config=cfg.get("risk_scoring")
        )

        dec = make_decision(
            danger_signs=inp.get("danger_signs", []),
            contradictions=risk_res["contradictions"],
            steroid_risk=risk_res["steroid_risk"],
            fungal_pattern=risk_res["fungal_pattern"],
            quality_findings=inp.get("image_quality", {"acceptable": True}),
            vulnerable_flags=inp.get("vulnerable_flags", []),
            config=cfg
        )

        assert dec["category"] == exp["category"], f"Vector {v['id']} category mismatch"
        assert dec["urgency"] == exp["urgency"], f"Vector {v['id']} urgency mismatch"
