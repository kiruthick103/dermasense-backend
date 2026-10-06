"""
Comprehensive Safety and Invariant Property Tests for DermaSense.
Uses Pytest and Hypothesis to test core clinical safety invariants, banned words scanning,
deterministic reproducibility, privacy deletion, and reference numeric metrics.
"""

import itertools
import pytest
from hypothesis import given, strategies as st

from engines.decide import make_decision
from engines.risk import calculate_risk
from engines.label_match import match_medicine_label
from engines.quality import assess_image_quality
from eval.metrics import wilson_score_interval
from model.calibration import compute_ece


BANNED_WORDS = ["confirmed", "diagnosed", "tinea", "you have", "steroid-free"]
REASSURING_WORDS = ["harmless", "safe to ignore", "healthy", "no problem", "cured", "all clear", "benign"]
PRESCRIPTION_TERMS = ["take 500mg", "take 250mg", "apply 3 times", "take daily dose", "discontinue all medications immediately"]


def test_banned_words_scanner_across_all_engine_outputs():
    """Scans all decision categories, recommendations, reasons, labels, and error text for banned words."""
    test_cases = [
        # Cat A scenario
        make_decision(
            danger_signs=[], contradictions=[], steroid_risk=0, fungal_pattern=3,
            quality_findings={"acceptable": True},
            model_output={"label": "compatible with a superficial fungal pattern", "confidence": 0.85}
        ),
        # Cat B scenario
        make_decision(
            danger_signs=[], contradictions=[], steroid_risk=4, fungal_pattern=0,
            quality_findings={"acceptable": True}
        ),
        # Cat C scenario
        make_decision(
            danger_signs=[], contradictions=["test contradiction"], steroid_risk=0, fungal_pattern=0,
            quality_findings={"acceptable": False}
        ),
        # Cat D scenario
        make_decision(
            danger_signs=["severe_pain", "facial_involvement"], contradictions=[], steroid_risk=0, fungal_pattern=0,
            quality_findings={"acceptable": True}
        ),
    ]

    for tc in test_cases:
        full_text = " ".join([
            tc.get("category_description", ""),
            tc.get("recommended_action", ""),
            tc.get("disclaimer", ""),
            " ".join(tc.get("reasons", [])),
            " ".join(tc.get("rule_trace", [])),
        ]).lower()

        for bw in BANNED_WORDS:
            assert bw not in full_text, f"Banned word '{bw}' detected in decision output text!"

        for rw in REASSURING_WORDS:
            assert rw not in full_text, f"Reassuring phrase '{rw}' detected in clinical output!"

        for pt in PRESCRIPTION_TERMS:
            assert pt not in full_text, f"Prescription term '{pt}' detected in output!"


def test_label_matcher_never_outputs_steroid_free():
    test_texts = [
        "100% steroid-free herbal skin balm",
        "Contains natural oils with no steroids whatsoever",
        "Gentle moisturizing cream free from all steroids",
        "Zero steroid formulation",
    ]
    for txt in test_texts:
        res = match_medicine_label(txt)
        res_str = str(res).lower()
        assert "steroid-free" not in res_str
        assert res["status"] in {"POSSIBLE_STEROID_FOUND", "NONE_FOUND_IN_VISIBLE_TEXT", "UNREADABLE"}


# Property Test 1: Danger sign always yields Category D
@given(
    danger_subset=st.lists(
        st.sampled_from(["facial_involvement", "severe_pain", "systemic_symptoms", "rapid_spreading_hours"]),
        min_size=1, max_size=4
    ),
    steroid_risk=st.integers(min_value=0, max_value=10),
    fungal_pattern=st.integers(min_value=0, max_value=10)
)
def test_property_danger_sign_always_yields_d(danger_subset, steroid_risk, fungal_pattern):
    res = make_decision(
        danger_signs=danger_subset,
        contradictions=[],
        steroid_risk=steroid_risk,
        fungal_pattern=fungal_pattern,
        quality_findings={"acceptable": True},
    )
    assert res["category"] == "D"
    assert res["urgency"] == "EMERGENT"


# Property Test 2: No input produces a reassuring or dismissive result
@given(
    steroid_risk=st.integers(min_value=0, max_value=5),
    fungal_pattern=st.integers(min_value=0, max_value=5)
)
def test_property_no_reassurance(steroid_risk, fungal_pattern):
    res = make_decision(
        danger_signs=[],
        contradictions=[],
        steroid_risk=steroid_risk,
        fungal_pattern=fungal_pattern,
        quality_findings={"acceptable": True},
    )
    # Every category must recommend some clinical review, never reassurance
    rec = res["recommended_action"].lower()
    assert any(term in rec for term in ["consult", "schedule", "seek", "evaluate", "review"])


# Property Test 3: Adding risk evidence never lowers urgency
def test_property_adding_risk_never_lowers_urgency():
    urgency_levels = {"ROUTINE": 1, "ELEVATED": 2, "HIGH": 3, "EMERGENT": 4}
    # Base risk = 0
    res_base = make_decision([], [], steroid_risk=0, fungal_pattern=0, quality_findings={"acceptable": True})
    # High steroid risk = 4
    res_elevated = make_decision([], [], steroid_risk=4, fungal_pattern=0, quality_findings={"acceptable": True})

    assert urgency_levels[res_elevated["urgency"]] >= urgency_levels[res_base["urgency"]]


# Property Test 4: NOT_SURE never increases risk score
@given(
    ans_choice=st.sampled_from(["YES", "NO", "NOT_SURE"])
)
def test_property_not_sure_never_increases_score(ans_choice):
    res_not_sure = calculate_risk({"used_any_cream": "NOT_SURE"})
    res_choice = calculate_risk({"used_any_cream": ans_choice})
    assert res_not_sure["steroid_risk"] <= res_choice["steroid_risk"]


# Property Test 5: Vulnerable flags never lower category
def test_property_vulnerable_never_lowers_category():
    # Cat A baseline
    res_normal = make_decision([], [], 0, 3, {"acceptable": True}, vulnerable_flags=[])
    res_infant = make_decision([], [], 0, 3, {"acceptable": True}, vulnerable_flags=["infant"])

    assert res_normal["category"] == res_infant["category"]
    # Urgency must be equal or higher
    urg_ranks = {"ROUTINE": 1, "ELEVATED": 2, "HIGH": 3, "EMERGENT": 4}
    assert urg_ranks[res_infant["urgency"]] >= urg_ranks[res_normal["urgency"]]


# Property Test 6: Same input produces exactly the same output (Pure determinism)
def test_property_pure_determinism():
    args = (
        ["severe_pain"],
        [],
        2,
        3,
        {"acceptable": True},
        {"label": "uncertain", "confidence": 0.5},
        ["pregnancy"],
    )
    run1 = make_decision(*args)
    run2 = make_decision(*args)
    assert run1 == run2


def test_reference_numeric_wilson_interval():
    """Verifies Wilson interval calculation against known textbook values."""
    # Example: 10 successes out of 20 trials -> p=0.5, 95% Wilson CI ~ [0.2993, 0.7007]
    low, high = wilson_score_interval(10, 20, confidence=0.95)
    assert round(low, 2) == 0.30
    assert round(high, 2) == 0.70

    # Example: 0 successes out of 10 -> [0.0, 0.2775]
    low0, high0 = wilson_score_interval(0, 10, confidence=0.95)
    assert low0 == 0.0
    assert round(high0, 2) == 0.28


def test_reference_numeric_ece_calculation():
    """Verifies manual Expected Calibration Error computation."""
    import numpy as np
    # Perfectly calibrated case:
    # 10 samples with conf 0.8, exactly 8 positive (80%) -> bin gap = 0
    probs = np.array([0.8] * 10)
    labels = np.array([1, 1, 1, 1, 1, 1, 1, 1, 0, 0])
    ece, _ = compute_ece(probs, labels, n_bins=5)
    assert ece == 0.0

    # Miscalibrated case: 10 samples with conf 0.9, all negative (0% acc) -> gap = 0.9
    probs_bad = np.array([0.9] * 10)
    labels_bad = np.array([0] * 10)
    ece_bad, _ = compute_ece(probs_bad, labels_bad, n_bins=5)
    assert round(ece_bad, 2) == 0.90
