"""
Unit Tests for Engine 5 (Triage and Queue Sorting).
Verifies deterministic multi-key sorting, tie-breaking by case_id, and
confidence band mapping (HIGH, LOW, UNCERTAIN) without exposing raw decimals.
"""

import pytest
from engines.triage import sort_triage_queue, get_confidence_display_band


def test_triage_queue_sorting_order():
    cases = [
        # Case 1: Category A, persistent (priority 3)
        {
            "case_id": "case_001",
            "category": "A",
            "urgency": "ROUTINE",
            "steroid_risk": 0,
            "age_hours": 2.0,
            "answers": {"returned_after_stopping": "YES"},
        },
        # Case 2: Category D (danger sign, priority 1)
        {
            "case_id": "case_002",
            "category": "D",
            "urgency": "EMERGENT",
            "steroid_risk": 0,
            "age_hours": 1.0,
            "answers": {},
        },
        # Case 3: Category B with spreading (priority 2)
        {
            "case_id": "case_003",
            "category": "B",
            "urgency": "ELEVATED",
            "steroid_risk": 4,
            "age_hours": 3.0,
            "answers": {"spread_despite_treatment": "YES"},
        },
        # Case 4: Category C uncertain (priority 4)
        {
            "case_id": "case_004",
            "category": "C",
            "urgency": "ROUTINE",
            "steroid_risk": 0,
            "age_hours": 4.0,
            "answers": {},
        },
    ]

    sorted_cases = sort_triage_queue(cases)
    # Expected ordering: Case 2 (Priority 1) -> Case 3 (Priority 2) -> Case 1 (Priority 3) -> Case 4 (Priority 4)
    ordered_ids = [c["case_id"] for c in sorted_cases]
    assert ordered_ids == ["case_002", "case_003", "case_001", "case_004"]


def test_triage_tie_breaking_by_case_id():
    # Two identical cases with identical priority, urgency, risk, age
    cases = [
        {"case_id": "case_Z", "category": "D", "urgency": "EMERGENT", "steroid_risk": 0, "age_hours": 1.0, "answers": {}},
        {"case_id": "case_A", "category": "D", "urgency": "EMERGENT", "steroid_risk": 0, "age_hours": 1.0, "answers": {}},
    ]
    sorted_cases = sort_triage_queue(cases)
    assert [c["case_id"] for c in sorted_cases] == ["case_A", "case_Z"]


def test_confidence_display_bands_only():
    # Abstention -> UNCERTAIN
    assert get_confidence_display_band(0.85, abstained=True) == "UNCERTAIN"
    # Low confidence -> LOW
    assert get_confidence_display_band(0.25, abstained=False) == "LOW"
    # Mid band -> UNCERTAIN
    assert get_confidence_display_band(0.55, abstained=False) == "UNCERTAIN"
    # High confidence -> HIGH
    assert get_confidence_display_band(0.75, abstained=False) == "HIGH"
