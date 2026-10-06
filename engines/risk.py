"""
Engine 3: Questionnaire Risk Scoring and Contradiction Detection
Deterministic pure engine with no I/O, no network, and no mutable global state.
Evaluates clinical history, topical cream usage patterns, contradictions, and missing info.
"""

from typing import Any, Dict, List, Optional, Union


VALID_ANSWERS = {"YES", "NO", "NOT_SURE"}

DEFAULT_CONFIG = {
    "steroid_risk": {
        "unknown_or_unprescribed_cream": 2,
        "steroid_name_seen_or_label_match": 3,
        "spread_despite_treatment": 2,
        "returned_after_stopping": 1,
        "combination_wording": 1,
    },
    "fungal_pattern": {
        "model_confidence_hit": 2,
        "itchy_ring_or_scaly": 1,
        "duration_gt_1_week": 1,
    },
    "decision": {
        "model_high_confidence_threshold": 0.70,
    }
}


def normalize_answer(val: Optional[Union[str, bool]]) -> str:
    """Standardizes inputs to YES, NO, or NOT_SURE."""
    if val is None:
        return "NOT_SURE"
    if isinstance(val, bool):
        return "YES" if val else "NO"
    s = str(val).strip().upper()
    if s in ("YES", "Y", "TRUE", "1", ">1_WEEK", "MORE_THAN_1_WEEK"):
        return "YES"
    if s in ("NO", "N", "FALSE", "0", "<=1_WEEK", "1_WEEK_OR_LESS"):
        return "NO"
    return "NOT_SURE"


def detect_contradictions(answers: Dict[str, str]) -> List[str]:
    """
    Evaluates questionnaire answers for logical incompatibilities.
    Example: Reporting 'No cream used' while claiming spread despite cream treatment.
    """
    contradictions: List[str] = []
    used_cream = answers.get("used_any_cream", "NOT_SURE")

    if used_cream == "NO":
        if answers.get("spread_despite_treatment") == "YES":
            contradictions.append(
                "Reported no cream used, but answered that the rash spread despite cream treatment."
            )
        if answers.get("returned_after_stopping") == "YES":
            contradictions.append(
                "Reported no cream used, but answered that the rash returned after stopping treatment."
            )
        if answers.get("prescribed_by_clinician") == "YES":
            contradictions.append(
                "Reported no cream used, but answered that a cream was prescribed by a clinician."
            )
        if answers.get("steroid_name_visible") == "YES":
            contradictions.append(
                "Reported no cream used, but answered that a steroid name was visible on a cream label."
            )
        if answers.get("combination_wording") == "YES":
            contradictions.append(
                "Reported no cream used, but answered that combination wording was present on a cream package."
            )

    return contradictions


def calculate_risk(
    answers: Dict[str, Any],
    model_output: Optional[Dict[str, Any]] = None,
    label_match_output: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculates steroid risk and fungal pattern score deterministically.

    Parameters:
      answers: Dict containing answers to the 8 questions:
        - used_any_cream
        - prescribed_by_clinician
        - steroid_name_visible
        - combination_wording
        - returned_after_stopping
        - spread_despite_treatment
        - itchy_ring_or_scaly
        - duration (or duration_gt_1_week)
      model_output: Optional dictionary with 'confidence', 'abstained', 'label'
      label_match_output: Optional dictionary with 'status'
      config: Optional scoring weights overrides

    Returns:
      {
        "steroid_risk": int,
        "fungal_pattern": int,
        "rules_fired": List[Dict[str, Any]],
        "missing_information": List[str],
        "contradictions": List[str]
      }
    """
    cfg = config or DEFAULT_CONFIG
    s_cfg = cfg.get("steroid_risk", DEFAULT_CONFIG["steroid_risk"])
    f_cfg = cfg.get("fungal_pattern", DEFAULT_CONFIG["fungal_pattern"])
    d_cfg = cfg.get("decision", DEFAULT_CONFIG["decision"])
    model_thresh = float(d_cfg.get("model_high_confidence_threshold", 0.70))

    norm_answers: Dict[str, str] = {}
    expected_questions = [
        "used_any_cream",
        "prescribed_by_clinician",
        "steroid_name_visible",
        "combination_wording",
        "returned_after_stopping",
        "spread_despite_treatment",
        "itchy_ring_or_scaly",
        "duration",
    ]

    missing_information: List[str] = []
    for q in expected_questions:
        raw_val = answers.get(q)
        norm_val = normalize_answer(raw_val)
        norm_answers[q] = norm_val
        if norm_val == "NOT_SURE":
            missing_information.append(q)

    contradictions = detect_contradictions(norm_answers)

    rules_fired: List[Dict[str, Any]] = []
    steroid_risk = 0
    fungal_pattern = 0

    # 1. Steroid Risk Scoring
    # unknown_or_unprescribed_cream: +2
    if norm_answers["used_any_cream"] == "YES" and norm_answers["prescribed_by_clinician"] == "NO":
        pts = int(s_cfg.get("unknown_or_unprescribed_cream", 2))
        steroid_risk += pts
        rules_fired.append({
            "rule": "unknown_or_unprescribed_cream",
            "points": pts,
            "reason": "Topical cream was used without clinician prescription."
        })

    # steroid_name_seen OR label-match hit: +3
    label_status = (label_match_output or {}).get("status", "")
    label_hit = label_status == "POSSIBLE_STEROID_FOUND"
    steroid_seen = norm_answers["steroid_name_visible"] == "YES"
    if steroid_seen or label_hit:
        pts = int(s_cfg.get("steroid_name_seen_or_label_match", 3))
        steroid_risk += pts
        reason_desc = (
            "Steroid active ingredient detected on cream label."
            if label_hit
            else "User reported seeing a steroid name on the medication."
        )
        rules_fired.append({
            "rule": "steroid_name_seen_or_label_match",
            "points": pts,
            "reason": reason_desc
        })

    # spread_despite_treatment: +2
    if norm_answers["spread_despite_treatment"] == "YES":
        pts = int(s_cfg.get("spread_despite_treatment", 2))
        steroid_risk += pts
        rules_fired.append({
            "rule": "spread_despite_treatment",
            "points": pts,
            "reason": "Rash spread or worsened despite treatment application."
        })

    # returned_after_stopping: +1
    if norm_answers["returned_after_stopping"] == "YES":
        pts = int(s_cfg.get("returned_after_stopping", 1))
        steroid_risk += pts
        rules_fired.append({
            "rule": "returned_after_stopping",
            "points": pts,
            "reason": "Rash flared or returned after stopping topical cream."
        })

    # combination wording: +1
    if norm_answers["combination_wording"] == "YES":
        pts = int(s_cfg.get("combination_wording", 1))
        steroid_risk += pts
        rules_fired.append({
            "rule": "combination_wording",
            "points": pts,
            "reason": "Topical product described with multi-action or combination wording."
        })

    # 2. Fungal-pattern Scoring
    # Pattern model hit (Fungal-type with Moderate or Strong strength, or legacy compatible model): +2
    pattern_hit = False
    pattern_reason = ""
    
    if model_output and isinstance(model_output, dict):
        if "top_pattern" in model_output:
            # Pattern model engine
            top_pat = model_output.get("top_pattern", "")
            strength = model_output.get("strength", "")
            ens_comp = model_output.get("ensemble_compatible", False)
            if top_pat == "fungal_ring_pattern" and (strength in ("Strong", "Moderate") or ens_comp):
                pattern_hit = True
                pattern_reason = f"Pattern model: {model_output.get('top_display_name', 'Fungal-type')} ({strength} strength)."
        elif not model_output.get("abstained", False):
            lbl = model_output.get("label", "")
            conf = float(model_output.get("confidence", 0.0))
            if "compatible" in lbl.lower() and "not" not in lbl.lower() and conf >= model_thresh:
                pattern_hit = True
                pattern_reason = f"Visual model score ({round(conf, 2)}) compatible with superficial fungal pattern."

    if pattern_hit:
        pts = int(f_cfg.get("model_confidence_hit", f_cfg.get("pattern_model_fungal_hit", 2)))
        fungal_pattern += pts
        rules_fired.append({
            "rule": "pattern_model_fungal_hit",
            "points": pts,
            "reason": pattern_reason
        })

    # itchy/ring/scaly: +1
    if norm_answers["itchy_ring_or_scaly"] == "YES":
        pts = int(f_cfg.get("itchy_ring_or_scaly", 1))
        fungal_pattern += pts
        rules_fired.append({
            "rule": "itchy_ring_or_scaly",
            "points": pts,
            "reason": "Reported classic morphological cues (annular, scaly border, or itching)."
        })

    # duration > 1 week: +1
    if norm_answers["duration"] == "YES":
        pts = int(f_cfg.get("duration_gt_1_week", 1))
        fungal_pattern += pts
        rules_fired.append({
            "rule": "duration_gt_1_week",
            "points": pts,
            "reason": "Rash duration persists longer than one week."
        })

    return {
        "steroid_risk": steroid_risk,
        "fungal_pattern": fungal_pattern,
        "rules_fired": rules_fired,
        "missing_information": missing_information,
        "contradictions": contradictions
    }
