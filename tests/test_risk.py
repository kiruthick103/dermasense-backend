"""
Unit and Property Tests for Engine 3 (Questionnaire Risk and Contradictions).
Verifies scoring values, missing information tracking, and contradiction detection.
"""

import itertools
import pytest
from engines.risk import calculate_risk, detect_contradictions


def test_steroid_risk_reference_scoring():
    # Case with unprescribed cream (+2) + steroid visible (+3) + spread (+2) + returned (+1) + combination (+1) = 9
    answers = {
        "used_any_cream": "YES",
        "prescribed_by_clinician": "NO",
        "steroid_name_visible": "YES",
        "combination_wording": "YES",
        "returned_after_stopping": "YES",
        "spread_despite_treatment": "YES",
        "itchy_ring_or_scaly": "NO",
        "duration": "NO",
    }
    res = calculate_risk(answers)
    assert res["steroid_risk"] == 9
    assert len(res["rules_fired"]) == 5
    assert len(res["contradictions"]) == 0


def test_fungal_pattern_reference_scoring():
    # Model hit (+2) + itchy_ring_or_scaly (+1) + duration > 1w (+1) = 4
    answers = {
        "used_any_cream": "NO",
        "prescribed_by_clinician": "NO",
        "steroid_name_visible": "NO",
        "combination_wording": "NO",
        "returned_after_stopping": "NO",
        "spread_despite_treatment": "NO",
        "itchy_ring_or_scaly": "YES",
        "duration": "YES",
    }
    model_output = {
        "label": "compatible with a superficial fungal pattern",
        "confidence": 0.85,
        "abstained": False
    }
    res = calculate_risk(answers, model_output=model_output)
    assert res["fungal_pattern"] == 4
    assert res["steroid_risk"] == 0
    assert len(res["rules_fired"]) == 3


def test_not_sure_never_adds_points():
    answers_all_not_sure = {
        "used_any_cream": "NOT_SURE",
        "prescribed_by_clinician": "NOT_SURE",
        "steroid_name_visible": "NOT_SURE",
        "combination_wording": "NOT_SURE",
        "returned_after_stopping": "NOT_SURE",
        "spread_despite_treatment": "NOT_SURE",
        "itchy_ring_or_scaly": "NOT_SURE",
        "duration": "NOT_SURE",
    }
    res = calculate_risk(answers_all_not_sure)
    assert res["steroid_risk"] == 0
    assert res["fungal_pattern"] == 0
    assert len(res["rules_fired"]) == 0
    assert len(res["missing_information"]) == 8


def test_contradictions_detected():
    # 1. No cream used + spread despite treatment
    c1 = detect_contradictions({"used_any_cream": "NO", "spread_despite_treatment": "YES"})
    assert len(c1) > 0

    # 2. No cream used + returned after stopping
    c2 = detect_contradictions({"used_any_cream": "NO", "returned_after_stopping": "YES"})
    assert len(c2) > 0

    # 3. No cream used + prescribed by clinician
    c3 = detect_contradictions({"used_any_cream": "NO", "prescribed_by_clinician": "YES"})
    assert len(c3) > 0

    # 4. No cream used + steroid name visible
    c4 = detect_contradictions({"used_any_cream": "NO", "steroid_name_visible": "YES"})
    assert len(c4) > 0

    # 5. No cream used + combination wording
    c5 = detect_contradictions({"used_any_cream": "NO", "combination_wording": "YES"})
    assert len(c5) > 0


def test_truth_table_exhaustive_answers_no_crash():
    """Exhaustive check on subsets of questions to verify stability and non-negative scores."""
    keys = ["used_any_cream", "spread_despite_treatment", "itchy_ring_or_scaly", "duration"]
    for combo in itertools.product(["YES", "NO", "NOT_SURE"], repeat=len(keys)):
        ans = dict(zip(keys, combo))
        res = calculate_risk(ans)
        assert res["steroid_risk"] >= 0
        assert res["fungal_pattern"] >= 0
        assert isinstance(res["contradictions"], list)
        assert isinstance(res["missing_information"], list)
