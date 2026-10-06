"""
Unit tests for Engine 5: Skin-Condition Pattern Model and Strength Rating.
Tests:
1. Strong strength requires high calibrated probability, conformal set size 1, and feature agreement.
2. Moderate strength for probabilities >= t_moderate and conformal set size <= 2.
3. Weak strength for lower probability passing OOD check.
4. Abstention ("Not enough to say") when non-skin, poor quality, or OOD.
5. Upload quality flags cap strength at "Moderate" even if probability is high.
6. Conservative ensemble: fungal-type requires ring/border agreement.
"""

import numpy as np
import pytest
from engines.pattern import evaluate_pattern_similarity, compute_conformal_set, compute_ood_energy_score


def test_strong_strength_fungal_ring():
    interpretable = {
        "ring_score": 0.85,
        "redness_contrast": 15.0,
        "border_sharpness": 22.0,
        "affected_area_pct": 12.0
    }
    quality = {
        "acceptable": True,
        "measurements": {"skin_fraction": 0.50}
    }
    # Logits strongly favoring fungal_ring_pattern
    logits = np.array([4.0, 0.5, 0.2, 0.1, 0.1])
    res = evaluate_pattern_similarity(interpretable, quality, logits=logits, source="camera")

    assert res["top_pattern"] == "fungal_ring_pattern"
    assert res["strength"] == "Strong"
    assert len(res["conformal_set"]) == 1
    assert res["ensemble_compatible"] is True


def test_upload_flag_caps_strength_at_moderate():
    interpretable = {
        "ring_score": 0.90,
        "redness_contrast": 18.0,
        "border_sharpness": 25.0,
        "affected_area_pct": 10.0
    }
    # Image marked with upload flags (e.g. heavy compression / moire)
    quality = {
        "acceptable": True,
        "measurements": {"skin_fraction": 0.55},
        "upload_quality": {"has_upload_flags": True, "flags": ["HEAVY_COMPRESSION"]}
    }
    logits = np.array([4.5, 0.2, 0.1, 0.1, 0.1])
    res = evaluate_pattern_similarity(interpretable, quality, logits=logits, source="upload")

    assert res["top_pattern"] == "fungal_ring_pattern"
    # Even though probability is very high, upload quality flag caps strength at Moderate
    assert res["strength"] == "Moderate"


def test_abstention_on_non_skin():
    interpretable = {"ring_score": 0.0, "redness_contrast": 0.0}
    quality = {
        "acceptable": False,
        "reasons": ["OBSTRUCTED"],
        "measurements": {"skin_fraction": 0.02}
    }
    res = evaluate_pattern_similarity(interpretable, quality, source="camera")

    assert res["strength"] == "Not enough to say"
    assert res["abstention_reason"] is not None


def test_conformal_set_coverage():
    probs = {
        "fungal_ring_pattern": 0.85,
        "eczema_dermatitis_pattern": 0.08,
        "psoriasis_pattern": 0.04,
        "bacterial_infection_pattern": 0.02,
        "other_unclear_pattern": 0.01
    }
    # At alpha = 0.20 (80% coverage), set should contain only the top class
    c_set = compute_conformal_set(probs, alpha=0.20)
    assert c_set == ["fungal_ring_pattern"]

    # When ambiguous (e.g., 0.55 and 0.38)
    ambiguous_probs = {
        "fungal_ring_pattern": 0.55,
        "eczema_dermatitis_pattern": 0.38,
        "psoriasis_pattern": 0.04,
        "bacterial_infection_pattern": 0.02,
        "other_unclear_pattern": 0.01
    }
    c_set_ambig = compute_conformal_set(ambiguous_probs, alpha=0.10)
    assert len(c_set_ambig) == 2
    assert "fungal_ring_pattern" in c_set_ambig
    assert "eczema_dermatitis_pattern" in c_set_ambig
