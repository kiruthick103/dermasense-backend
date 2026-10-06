"""
Engine 5: Triage and Queue Prioritization
Deterministic pure engine with no I/O, no network, and no mutable global state.
Sorts cases into a prioritized clinical review queue and maps confidence values to
discrete categories (HIGH, LOW, UNCERTAIN) without exposing raw decimal numbers.
"""

from typing import Any, Dict, List, Tuple


URGENCY_RANK = {
    "EMERGENT": 4,
    "HIGH": 3,
    "ELEVATED": 2,
    "ROUTINE": 1,
}


def get_confidence_display_band(
    confidence: float,
    abstained: bool = False,
    low_thresh: float = 0.40,
    high_thresh: float = 0.65,
) -> str:
    """
    Transforms continuous model confidence into strict discrete bands:
      - HIGH
      - LOW
      - UNCERTAIN

    Raw floating-point probabilities are never displayed to users.
    """
    if abstained:
        return "UNCERTAIN"
    if confidence >= high_thresh:
        return "HIGH"
    if confidence < low_thresh:
        return "LOW"
    return "UNCERTAIN"


def assign_case_priority(case: Dict[str, Any]) -> int:
    """
    Calculates primary triage queue priority:
      1: Danger signs (Category D)
      2: Possible steroid-modified spreading rash
      3: Persistent/recurrent rash
      4: Uncertain image or answers (Category C)
      5: Routine / educational
    """
    decision = case.get("decision", {})
    category = decision.get("category", case.get("category", "C"))
    answers = case.get("answers", {})

    # 1. Danger signs
    if category == "D":
        return 1

    # 2. Possible steroid-modified spreading rash
    spreading = answers.get("spread_despite_treatment") in ("YES", True)
    if category == "B" and spreading:
        return 2

    # 3. Persistent or recurrent rash
    recurrent = answers.get("returned_after_stopping") in ("YES", True)
    long_duration = answers.get("duration") in ("YES", True, ">1_WEEK")
    if category == "B" or (category == "A" and (recurrent or long_duration)):
        return 3

    # 4. Uncertain image or clinical ambiguity
    if category == "C":
        return 4

    # 5. Education-only / routine
    return 5


def sort_triage_queue(cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deterministic clinical triage sort.
    Orders cases strictly by:
      (priority_tier, -urgency_rank, -steroid_risk, -age_of_case, case_id)
    Ties are deterministically broken by case_id string comparison.
    """
    def sort_key(case: Dict[str, Any]) -> Tuple[int, int, int, float, str]:
        priority = assign_case_priority(case)
        decision = case.get("decision", {})
        urgency_str = decision.get("urgency", case.get("urgency", "ROUTINE"))
        urgency_val = URGENCY_RANK.get(urgency_str, 1)

        risk_data = case.get("risk_data", {})
        steroid_risk = int(risk_data.get("steroid_risk", case.get("steroid_risk", 0)))
        age_of_case = float(case.get("age_hours", case.get("age_of_case", 0.0)))
        case_id = str(case.get("case_id", ""))

        # (priority ascending, -urgency descending, -steroid_risk descending, -age descending, case_id ascending)
        return (priority, -urgency_val, -steroid_risk, -age_of_case, case_id)

    return sorted(cases, key=sort_key)
