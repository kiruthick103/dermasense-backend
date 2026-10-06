"""
Unit Tests for Engine 4 (Decision Engine).
Verifies strict hierarchical evaluation ladder:
  1. Danger signs -> D
  2. Contradictions -> C
  3. Steroid risk >= threshold -> B (even if image is poor)
  4. Poor image -> C
  5. Fungal pattern >= threshold -> A
  6. Otherwise -> C
And verifies vulnerable flags can only elevate urgency, never lowering categories.
"""

import pytest
from engines.decide import make_decision


def test_danger_sign_triggers_d_immediately():
    res = make_decision(
        danger_signs=["facial_involvement"],
        contradictions=[],
        steroid_risk=0,
        fungal_pattern=4,
        quality_findings={"acceptable": True},
        model_output={"label": "compatible with a superficial fungal pattern", "confidence": 0.95},
        vulnerable_flags=[],
    )
    assert res["category"] == "D"
    assert res["urgency"] == "EMERGENT"
    assert "facial_involvement" in res["rule_trace"][0]
    # Model output is not evaluated
    assert "bypassed" in res["model_output"]["note"].lower()


def test_contradictions_trigger_c():
    res = make_decision(
        danger_signs=[],
        contradictions=["Reported no cream used, but answered rash spread despite treatment."],
        steroid_risk=0,
        fungal_pattern=4,
        quality_findings={"acceptable": True},
        model_output={"label": "compatible with a superficial fungal pattern", "confidence": 0.90},
        vulnerable_flags=[],
    )
    assert res["category"] == "C"
    assert "contradictory" in res["reasons"][0].lower()


def test_steroid_risk_triggers_b_even_with_poor_image():
    # Steroid risk >= 3 triggers B even when photo quality check failed
    res = make_decision(
        danger_signs=[],
        contradictions=[],
        steroid_risk=4,
        fungal_pattern=1,
        quality_findings={"acceptable": False, "reasons": ["BLUR", "DARK"]},
        model_output={"label": "uncertain", "confidence": 0.50, "abstained": True},
        vulnerable_flags=[],
    )
    assert res["category"] == "B"
    assert "steroid" in res["reasons"][0].lower()


def test_poor_image_triggers_c_when_steroid_risk_low():
    res = make_decision(
        danger_signs=[],
        contradictions=[],
        steroid_risk=0,
        fungal_pattern=4,
        quality_findings={"acceptable": False, "reasons": ["BLUR"]},
        model_output={"label": "uncertain", "confidence": 0.50, "abstained": True},
        vulnerable_flags=[],
    )
    assert res["category"] == "C"
    assert "quality" in res["reasons"][0].lower()


def test_fungal_pattern_triggers_a():
    res = make_decision(
        danger_signs=[],
        contradictions=[],
        steroid_risk=0,
        fungal_pattern=3,
        quality_findings={"acceptable": True, "reasons": []},
        model_output={"label": "compatible with a superficial fungal pattern", "confidence": 0.85},
        vulnerable_flags=[],
    )
    assert res["category"] == "A"
    assert res["urgency"] == "ROUTINE"


def test_vulnerable_flags_only_elevate_urgency():
    # Baseline Category A
    base = make_decision(
        danger_signs=[],
        contradictions=[],
        steroid_risk=0,
        fungal_pattern=3,
        quality_findings={"acceptable": True},
        model_output={"label": "compatible with a superficial fungal pattern", "confidence": 0.85},
        vulnerable_flags=[],
    )
    assert base["category"] == "A"
    assert base["urgency"] == "ROUTINE"

    # With infant flag
    with_infant = make_decision(
        danger_signs=[],
        contradictions=[],
        steroid_risk=0,
        fungal_pattern=3,
        quality_findings={"acceptable": True},
        model_output={"label": "compatible with a superficial fungal pattern", "confidence": 0.85},
        vulnerable_flags=["infant"],
    )
    # Category MUST remain A (never lowered or changed)
    assert with_infant["category"] == "A"
    # Urgency must be elevated
    assert with_infant["urgency"] == "ELEVATED"


def test_safety_disclaimer_present():
    res = make_decision(
        danger_signs=[],
        contradictions=[],
        steroid_risk=0,
        fungal_pattern=0,
        quality_findings={"acceptable": True},
    )
    assert "disclaimer" in res
    assert "investigational screening prototype" in res["disclaimer"]
    assert res["model_output"]["status"] == "prototype_not_clinically_validated"
