"""
End-to-End Decision Engine Scenario Evaluation.
Evaluates clinical case scenarios across fungal patterns, steroid modification,
contradictions, photo blur, danger signs, and vulnerable groups.
"""

import os
import sys
from typing import Any, Dict, List, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engines.decide import make_decision
from engines.risk import calculate_risk


def build_scenario_cases() -> List[Dict[str, Any]]:
    """Defines the 7 required canonical test scenarios from Section 19."""
    scenarios: List[Dict[str, Any]] = [
        # Scenario 1: Clear fungal-like image + no cream -> A
        {
            "id": "scenario_1_clear_fungal_no_cream",
            "name": "Clear fungal-like image with no prior cream use",
            "danger_signs": [],
            "answers": {
                "used_any_cream": "NO",
                "prescribed_by_clinician": "NO",
                "steroid_name_visible": "NO",
                "combination_wording": "NO",
                "returned_after_stopping": "NO",
                "spread_despite_treatment": "NO",
                "itchy_ring_or_scaly": "YES",
                "duration": "YES",  # > 1 week
            },
            "quality_findings": {"acceptable": True, "reasons": []},
            "model_output": {
                "label": "compatible with a superficial fungal pattern",
                "confidence": 0.85,
                "abstained": False,
            },
            "vulnerable_flags": [],
            "expected_category": "A",
        },
        # Scenario 2: Blurry image -> C
        {
            "id": "scenario_2_blurry_image",
            "name": "Blurry image with no steroid history",
            "danger_signs": [],
            "answers": {
                "used_any_cream": "NO",
                "prescribed_by_clinician": "NO",
                "steroid_name_visible": "NO",
                "combination_wording": "NO",
                "returned_after_stopping": "NO",
                "spread_despite_treatment": "NO",
                "itchy_ring_or_scaly": "YES",
                "duration": "NO",
            },
            "quality_findings": {"acceptable": False, "reasons": ["BLUR"]},
            "model_output": {
                "label": "uncertain",
                "confidence": 0.50,
                "abstained": True,
            },
            "vulnerable_flags": [],
            "expected_category": "C",
        },
        # Scenario 3: Unknown combination cream + spreading rash + uncertain image -> B
        # Steroid risk: unprescribed cream (+2) + spread despite (+2) + combination (+1) = 5 (>= 3)
        {
            "id": "scenario_3_steroid_spreading_rash",
            "name": "Unknown combination cream with spreading rash and uncertain image",
            "danger_signs": [],
            "answers": {
                "used_any_cream": "YES",
                "prescribed_by_clinician": "NO",
                "steroid_name_visible": "NOT_SURE",
                "combination_wording": "YES",
                "returned_after_stopping": "YES",
                "spread_despite_treatment": "YES",
                "itchy_ring_or_scaly": "YES",
                "duration": "YES",
            },
            "quality_findings": {"acceptable": False, "reasons": ["BLUR"]},  # Remains B even if image poor
            "model_output": {
                "label": "uncertain",
                "confidence": 0.50,
                "abstained": True,
            },
            "vulnerable_flags": [],
            "expected_category": "B",
        },
        # Scenario 4: Weak signals -> C
        {
            "id": "scenario_4_weak_signals",
            "name": "Weak signals with inconclusive answers",
            "danger_signs": [],
            "answers": {
                "used_any_cream": "NOT_SURE",
                "prescribed_by_clinician": "NOT_SURE",
                "steroid_name_visible": "NO",
                "combination_wording": "NO",
                "returned_after_stopping": "NO",
                "spread_despite_treatment": "NO",
                "itchy_ring_or_scaly": "NO",
                "duration": "NO",
            },
            "quality_findings": {"acceptable": True, "reasons": []},
            "model_output": {
                "label": "not clearly compatible",
                "confidence": 0.60,
                "abstained": False,
            },
            "vulnerable_flags": [],
            "expected_category": "C",
        },
        # Scenario 5: Danger signs individually -> D
        # Test 5a: Facial involvement
        {
            "id": "scenario_5a_danger_facial",
            "name": "Individual danger sign: facial involvement",
            "danger_signs": ["facial_involvement"],
            "answers": {
                "used_any_cream": "NO",
                "prescribed_by_clinician": "NO",
                "steroid_name_visible": "NO",
                "combination_wording": "NO",
                "returned_after_stopping": "NO",
                "spread_despite_treatment": "NO",
                "itchy_ring_or_scaly": "YES",
                "duration": "YES",
            },
            "quality_findings": {"acceptable": True, "reasons": []},
            "model_output": {
                "label": "compatible with a superficial fungal pattern",
                "confidence": 0.90,
                "abstained": False,
            },
            "vulnerable_flags": [],
            "expected_category": "D",
        },
        # Test 5b: Severe pain
        {
            "id": "scenario_5b_danger_severe_pain",
            "name": "Individual danger sign: severe pain",
            "danger_signs": ["severe_pain"],
            "answers": {"used_any_cream": "NO"},
            "quality_findings": {"acceptable": True, "reasons": []},
            "model_output": {"label": "uncertain", "confidence": 0.5, "abstained": True},
            "vulnerable_flags": [],
            "expected_category": "D",
        },
        # Test 5c: Rapid spreading in hours
        {
            "id": "scenario_5c_danger_rapid_spreading",
            "name": "Individual danger sign: rapid spreading",
            "danger_signs": ["rapid_spreading_hours"],
            "answers": {"used_any_cream": "NO"},
            "quality_findings": {"acceptable": True, "reasons": []},
            "model_output": {},
            "vulnerable_flags": [],
            "expected_category": "D",
        },
        # Test 5d: Systemic fever
        {
            "id": "scenario_5d_danger_systemic",
            "name": "Individual danger sign: systemic symptoms",
            "danger_signs": ["systemic_symptoms"],
            "answers": {"used_any_cream": "NO"},
            "quality_findings": {"acceptable": True, "reasons": []},
            "model_output": {},
            "vulnerable_flags": [],
            "expected_category": "D",
        },
        # Test 5e: Blistering or peeling
        {
            "id": "scenario_5e_danger_blistering",
            "name": "Individual danger sign: blistering or skin peeling",
            "danger_signs": ["blistering_or_skin_peeling"],
            "answers": {"used_any_cream": "NO"},
            "quality_findings": {"acceptable": True, "reasons": []},
            "model_output": {},
            "vulnerable_flags": [],
            "expected_category": "D",
        },
        # Test 5f: Pus or foul discharge
        {
            "id": "scenario_5f_danger_pus",
            "name": "Individual danger sign: pus or foul discharge",
            "danger_signs": ["pus_or_foul_discharge"],
            "answers": {"used_any_cream": "NO"},
            "quality_findings": {"acceptable": True, "reasons": []},
            "model_output": {},
            "vulnerable_flags": [],
            "expected_category": "D",
        },
        # Test 5g: Signs of anaphylaxis
        {
            "id": "scenario_5g_danger_anaphylaxis",
            "name": "Individual danger sign: signs of anaphylaxis",
            "danger_signs": ["signs_of_anaphylaxis"],
            "answers": {"used_any_cream": "NO"},
            "quality_findings": {"acceptable": True, "reasons": []},
            "model_output": {},
            "vulnerable_flags": [],
            "expected_category": "D",
        },
        # Scenario 6: Contradictory answers -> C
        {
            "id": "scenario_6_contradictions",
            "name": "Contradictory answers (no cream used, but spread despite treatment)",
            "danger_signs": [],
            "answers": {
                "used_any_cream": "NO",
                "prescribed_by_clinician": "NO",
                "steroid_name_visible": "NO",
                "combination_wording": "NO",
                "returned_after_stopping": "NO",
                "spread_despite_treatment": "YES",  # Contradiction with NO cream!
                "itchy_ring_or_scaly": "YES",
                "duration": "YES",
            },
            "quality_findings": {"acceptable": True, "reasons": []},
            "model_output": {
                "label": "compatible with a superficial fungal pattern",
                "confidence": 0.88,
                "abstained": False,
            },
            "vulnerable_flags": [],
            "expected_category": "C",
        },
        # Scenario 7: Vulnerable group -> urgency may increase, category never less urgent
        {
            "id": "scenario_7_vulnerable_infant",
            "name": "Vulnerable group: Infant with Category A pattern (urgency elevated)",
            "danger_signs": [],
            "answers": {
                "used_any_cream": "NO",
                "prescribed_by_clinician": "NO",
                "steroid_name_visible": "NO",
                "combination_wording": "NO",
                "returned_after_stopping": "NO",
                "spread_despite_treatment": "NO",
                "itchy_ring_or_scaly": "YES",
                "duration": "YES",
            },
            "quality_findings": {"acceptable": True, "reasons": []},
            "model_output": {
                "label": "compatible with a superficial fungal pattern",
                "confidence": 0.85,
                "abstained": False,
            },
            "vulnerable_flags": ["infant"],
            "expected_category": "A",
            "expected_urgency": "ELEVATED",
        }
    ]
    return scenarios


def run_scenario_evaluations() -> Dict[str, Any]:
    """Runs all scenarios through risk and decision engines, verifying escalation accuracy."""
    scenarios = build_scenario_cases()
    results = []
    correct_count = 0

    for sc in scenarios:
        risk_res = calculate_risk(
            answers=sc.get("answers", {}),
            model_output=sc.get("model_output"),
        )

        dec_res = make_decision(
            danger_signs=sc.get("danger_signs", []),
            contradictions=risk_res.get("contradictions", []),
            steroid_risk=risk_res.get("steroid_risk", 0),
            fungal_pattern=risk_res.get("fungal_pattern", 0),
            quality_findings=sc.get("quality_findings", {}),
            model_output=sc.get("model_output"),
            vulnerable_flags=sc.get("vulnerable_flags", []),
        )

        actual_cat = dec_res.get("category")
        actual_urg = dec_res.get("urgency")
        exp_cat = sc.get("expected_category")
        exp_urg = sc.get("expected_urgency")

        cat_match = actual_cat == exp_cat
        urg_match = (exp_urg is None) or (actual_urg == exp_urg)
        passed = cat_match and urg_match

        if passed:
            correct_count += 1

        results.append({
            "id": sc["id"],
            "name": sc["name"],
            "passed": passed,
            "expected_category": exp_cat,
            "actual_category": actual_cat,
            "expected_urgency": exp_urg,
            "actual_urgency": actual_urg,
            "rule_trace": dec_res.get("rule_trace", []),
        })

    escalation_accuracy = (correct_count / float(len(scenarios))) * 100.0 if scenarios else 0.0

    return {
        "total_scenarios": len(scenarios),
        "passed_scenarios": correct_count,
        "escalation_accuracy_percent": round(escalation_accuracy, 2),
        "details": results
    }


if __name__ == "__main__":
    report = run_scenario_evaluations()
    print(f"Scenario Evaluation: {report['passed_scenarios']}/{report['total_scenarios']} passed ({report['escalation_accuracy_percent']}%)")
