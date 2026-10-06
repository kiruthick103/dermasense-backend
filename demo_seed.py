"""
Synthetic Seed Data Generator for DermaSense Demo Mode.
Populates realistic, anonymized demonstration cases across Categories A, B, C, and D,
with balanced camera vs. upload sources, triage priorities, and case statuses.
"""

from typing import Any, Dict, List
import uuid
import time


def generate_seed_cases() -> List[Dict[str, Any]]:
    """Generates synthetic patient cases for demonstration dashboards."""
    cases = [
        {
            "case_id": "CASE_A101_ANNULAR",
            "timestamp": "2026-10-04T08:15:00Z",
            "category": "A",
            "urgency": "ROUTINE",
            "body_area": "groin",
            "duration": "YES",
            "source": "camera",
            "status": "New",
            "steroid_risk": 0,
            "fungal_points": 3,
            "patient_age_group": "adult",
            "pattern_model": {
                "top_class": "fungal_ring_pattern",
                "display_name": "Fungal-type ring pattern",
                "strength": "Strong",
                "prob": 0.84,
                "conformal_set": ["fungal_ring_pattern"]
            },
            "quality": {
                "acceptable": True,
                "blurScore": 128.4,
                "brightnessMean": 132.0,
                "skinCoveragePct": 58.2
            },
            "findings": {
                "affectedAreaPct": 14.5,
                "ringScore": 0.82,
                "rednessContrast": 14.2
            },
            "reviewer_notes": "",
            "clinician_assessment": None,
            "patient_consent_share": True
        },
        {
            "case_id": "CASE_B202_STEROID",
            "timestamp": "2026-10-04T07:45:00Z",
            "category": "B",
            "urgency": "ELEVATED",
            "body_area": "face_neck",
            "duration": "YES",
            "source": "upload",
            "status": "Contacted",
            "steroid_risk": 7,
            "fungal_points": 2,
            "patient_age_group": "adult",
            "pattern_model": {
                "top_class": "eczema_dermatitis_pattern",
                "display_name": "Eczema or dermatitis-like",
                "strength": "Moderate",
                "prob": 0.62,
                "conformal_set": ["eczema_dermatitis_pattern", "fungal_ring_pattern"]
            },
            "cream_info": {
                "used_cream": "YES",
                "who_prescribed": "pharmacy",
                "cream_name": "Betnovate-C",
                "spread_despite_treatment": "YES",
                "returned_after_stopping": "YES"
            },
            "quality": {
                "acceptable": True,
                "blurScore": 96.0,
                "brightnessMean": 118.0,
                "skinCoveragePct": 42.0
            },
            "reviewer_notes": "Patient contacted by phone. Advised to bring the Betnovate tube to Monday PHC OPD.",
            "clinician_assessment": "Suspected tinea incognito masked by fluorinated topical steroid.",
            "patient_consent_share": True
        },
        {
            "case_id": "CASE_D303_EMERGENT",
            "timestamp": "2026-10-04T09:10:00Z",
            "category": "D",
            "urgency": "EMERGENT",
            "body_area": "trunk_back",
            "duration": "NO",
            "source": "camera",
            "status": "Referred",
            "steroid_risk": 0,
            "fungal_points": 0,
            "patient_age_group": "child",
            "danger_signs": ["fever_feeling_very_unwell", "rapid_spreading_hours", "skin_peeling_large_blisters"],
            "pattern_model": {
                "top_class": "other_unclear_pattern",
                "display_name": "Bypassed due to emergency",
                "strength": "Not enough to say",
                "prob": 0.0,
                "conformal_set": []
            },
            "quality": {
                "acceptable": True,
                "bypassed": True
            },
            "reviewer_notes": "High priority emergency: High fever with blisters. Immediately dispatched 108 Ambulance referral to District Hospital.",
            "clinician_assessment": "Referred under emergency protocol.",
            "patient_consent_share": True
        },
        {
            "case_id": "CASE_C404_UNCERTAIN",
            "timestamp": "2026-10-03T16:20:00Z",
            "category": "C",
            "urgency": "ROUTINE",
            "body_area": "arms",
            "duration": "NO",
            "source": "upload",
            "status": "Closed",
            "steroid_risk": 0,
            "fungal_points": 0,
            "patient_age_group": "adult",
            "pattern_model": {
                "top_class": "other_unclear_pattern",
                "display_name": "Other / unclear",
                "strength": "Weak",
                "prob": 0.38,
                "conformal_set": ["other_unclear_pattern", "eczema_dermatitis_pattern"]
            },
            "quality": {
                "acceptable": True,
                "blurScore": 84.0,
                "brightnessMean": 105.0,
                "skinCoveragePct": 30.0
            },
            "reviewer_notes": "Mild transient erythema. Resolved spontaneously without topical agents after 48h.",
            "clinician_assessment": "Non-specific irritant contact dermatitis, resolved.",
            "patient_consent_share": True
        },
        {
            "case_id": "CASE_A505_SCALY_RING",
            "timestamp": "2026-10-03T11:05:00Z",
            "category": "A",
            "urgency": "ROUTINE",
            "body_area": "legs_thighs",
            "duration": "YES",
            "source": "camera",
            "status": "Referred",
            "steroid_risk": 0,
            "fungal_points": 3,
            "patient_age_group": "older_adult",
            "pattern_model": {
                "top_class": "fungal_ring_pattern",
                "display_name": "Fungal-type ring pattern",
                "strength": "Strong",
                "prob": 0.81,
                "conformal_set": ["fungal_ring_pattern"]
            },
            "quality": {
                "acceptable": True,
                "blurScore": 142.0,
                "brightnessMean": 145.0,
                "skinCoveragePct": 65.0
            },
            "reviewer_notes": "Patient referred to Sub-District Hospital for KOH mount examination.",
            "clinician_assessment": "Clinical appearance consistent with tinea corporis. Prescribed topical antifungal alone.",
            "patient_consent_share": True
        }
    ]
    return cases
