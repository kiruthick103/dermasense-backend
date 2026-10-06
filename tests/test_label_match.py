"""
Unit Tests for Engine 2 (Medicine Label Matcher).
Tests exact matches, case variations, OCR fuzzy typos, false-positive protection,
status constraints, and banned phrases ('steroid-free').
"""

import pytest
from engines.label_match import match_medicine_label


def test_exact_match_lowercase():
    res = match_medicine_label("Contains clobetasol propionate cream 0.05% w/w")
    assert res["status"] == "POSSIBLE_STEROID_FOUND"
    assert res["matched_term"] == "clobetasol"
    assert res["distance"] == 0
    assert res["confidence"] == 1.0
    assert "confirm the label" in res["advice"].lower()


def test_uppercase_and_mixed_case():
    res1 = match_medicine_label("MOMETASONE FUROATE TOPICAL SUSPENSION")
    assert res1["status"] == "POSSIBLE_STEROID_FOUND"
    assert res1["matched_term"] == "mometasone"

    res2 = match_medicine_label("HydroCortisone Acetate Skin Cream")
    assert res2["status"] == "POSSIBLE_STEROID_FOUND"
    assert res2["matched_term"] == "hydrocortisone"


def test_ocr_typo_fuzzy_match():
    # 'betamethason' missing final 'e' (length 12, dist 1)
    res = match_medicine_label("Active ingredients: betamethason dipropionate")
    assert res["status"] == "POSSIBLE_STEROID_FOUND"
    assert res["matched_term"] == "betamethasone"
    assert res["distance"] == 1

    # 'clobetazol' 'z' instead of 's' (length 10, dist 1)
    res2 = match_medicine_label("Apply clobetazol ointment twice daily")
    assert res2["status"] == "POSSIBLE_STEROID_FOUND"
    assert res2["matched_term"] == "clobetasol"
    assert res2["distance"] == 1


def test_combination_cues():
    res = match_medicine_label("Manufactured by ABC Pharma - Fourderm cream 15g")
    assert res["status"] == "POSSIBLE_STEROID_FOUND"
    assert res["matched_term"] == "fourderm"


def test_false_positive_words_not_matched():
    # Words like 'cut', 'lot', 'ster', 'beta' shouldn't trigger random steroid match
    res = match_medicine_label("Lot number 12345, cut skin with sterile gauze and moisturizing lotion")
    assert res["status"] == "NONE_FOUND_IN_VISIBLE_TEXT"
    assert res["matched_term"] == ""


def test_unreadable_text():
    res1 = match_medicine_label("")
    assert res1["status"] == "UNREADABLE"

    res2 = match_medicine_label("   ... ??? !!! ---   ")
    assert res2["status"] == "UNREADABLE"

    res3 = match_medicine_label("12")
    assert res3["status"] == "UNREADABLE"


def test_status_values_strictly_constrained():
    allowed_statuses = {"POSSIBLE_STEROID_FOUND", "NONE_FOUND_IN_VISIBLE_TEXT", "UNREADABLE"}
    samples = [
        "clobetasol 0.05%",
        "plain white petrolatum jelly",
        "???",
        "mometasone",
        "gentle skin cleanser aloe vera",
    ]
    for s in samples:
        res = match_medicine_label(s)
        assert res["status"] in allowed_statuses
        # Must never output "steroid-free"
        assert "steroid-free" not in str(res).lower()
        assert "Please confirm the label with a pharmacist or clinician." in res["advice"]
