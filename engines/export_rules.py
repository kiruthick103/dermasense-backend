"""
Generates config/rules.json and tests/golden_vectors.json from config/rules.yaml.
Ensures perfect deterministic parity between Python and JavaScript rule engines.
"""

import json
import os
import yaml

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_YAML = os.path.join(ROOT_DIR, "config", "rules.yaml")
CONFIG_JSON = os.path.join(ROOT_DIR, "config", "rules.json")
GOLDEN_VECTORS_JSON = os.path.join(ROOT_DIR, "tests", "golden_vectors.json")


def export_rules():
    with open(CONFIG_YAML, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    with open(CONFIG_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Exported rules to {CONFIG_JSON}")
    return data


def generate_golden_vectors(cfg):
    """
    Creates comprehensive golden test cases covering:
    - Danger signs -> Category D
    - Contradictions -> Category C
    - Steroid risk >= 3 -> Category B
    - Poor image / non-skin -> Category C
    - Fungal pattern >= 2 -> Category A
    - Default fallback -> Category C
    - Vulnerable flags elevating urgency
    - Pattern model strength bands (Strong, Moderate, Weak, Abstain)
    """
    vectors = [
        {
            "id": "vector_01_danger_fever",
            "name": "Single danger sign (fever) escalates to D immediately",
            "input": {
                "danger_signs": ["fever_feeling_very_unwell"],
                "used_any_cream": "YES",
                "prescribed_by_clinician": "NO",
                "steroid_name_visible": "YES",
                "pattern_model": {"top_class": "fungal_ring_pattern", "strength": "Strong", "prob": 0.88},
                "image_quality": {"acceptable": True}
            },
            "expected": {
                "category": "D",
                "urgency": "EMERGENT",
                "bypassed_model": True
            }
        },
        {
            "id": "vector_02_contradiction",
            "name": "Contradiction (no cream, but steroid seen) defaults to C",
            "input": {
                "danger_signs": [],
                "used_any_cream": "NO",
                "prescribed_by_clinician": "NOT_SURE",
                "steroid_name_visible": "YES",
                "pattern_model": {"top_class": "fungal_ring_pattern", "strength": "Strong", "prob": 0.88},
                "image_quality": {"acceptable": True}
            },
            "expected": {
                "category": "C",
                "urgency": "ROUTINE",
                "has_contradiction": True
            }
        },
        {
            "id": "vector_03_steroid_risk_high",
            "name": "Unprescribed cream (+2) + steroid seen (+3) = Category B",
            "input": {
                "danger_signs": [],
                "used_any_cream": "YES",
                "prescribed_by_clinician": "NO",
                "steroid_name_visible": "YES",
                "spread_despite_treatment": "YES",
                "pattern_model": {"top_class": "fungal_ring_pattern", "strength": "Strong", "prob": 0.90},
                "image_quality": {"acceptable": True}
            },
            "expected": {
                "category": "B",
                "urgency": "ELEVATED",
                "min_steroid_risk": 7
            }
        },
        {
            "id": "vector_04_poor_image_quality",
            "name": "Inadequate photo quality routes to Category C",
            "input": {
                "danger_signs": [],
                "used_any_cream": "NO",
                "pattern_model": {"top_class": "fungal_ring_pattern", "strength": "Weak", "prob": 0.40},
                "image_quality": {"acceptable": False, "reasons": ["BLUR"]}
            },
            "expected": {
                "category": "C",
                "urgency": "ROUTINE"
            }
        },
        {
            "id": "vector_05_fungal_pattern_hit",
            "name": "Fungal pattern model (+2) + itchy (+1) + duration > 1 week (+1) = Category A",
            "input": {
                "danger_signs": [],
                "used_any_cream": "NO",
                "itchy_ring_or_scaly": "YES",
                "duration": "YES",
                "pattern_model": {"top_class": "fungal_ring_pattern", "strength": "Moderate", "prob": 0.65},
                "image_quality": {"acceptable": True}
            },
            "expected": {
                "category": "A",
                "urgency": "ROUTINE",
                "min_fungal_points": 4
            }
        },
        {
            "id": "vector_06_vulnerable_elevation",
            "name": "Vulnerable flag (infant / pregnancy) elevates Category A urgency to ELEVATED",
            "input": {
                "danger_signs": [],
                "used_any_cream": "NO",
                "itchy_ring_or_scaly": "YES",
                "duration": "YES",
                "vulnerable_flags": ["infant"],
                "pattern_model": {"top_class": "fungal_ring_pattern", "strength": "Strong", "prob": 0.85},
                "image_quality": {"acceptable": True}
            },
            "expected": {
                "category": "A",
                "urgency": "ELEVATED"
            }
        },
        {
            "id": "vector_07_not_sure_no_points",
            "name": "All NOT_SURE answers add zero points -> Category C fallback",
            "input": {
                "danger_signs": [],
                "used_any_cream": "NOT_SURE",
                "prescribed_by_clinician": "NOT_SURE",
                "steroid_name_visible": "NOT_SURE",
                "combination_wording": "NOT_SURE",
                "spread_despite_treatment": "NOT_SURE",
                "returned_after_stopping": "NOT_SURE",
                "itchy_ring_or_scaly": "NOT_SURE",
                "duration": "NOT_SURE",
                "pattern_model": {"top_class": "other_unclear_pattern", "strength": "Not enough to say", "prob": 0.20},
                "image_quality": {"acceptable": True}
            },
            "expected": {
                "category": "C",
                "urgency": "ROUTINE",
                "steroid_risk": 0,
                "fungal_points": 0
            }
        }
    ]

    with open(GOLDEN_VECTORS_JSON, "w", encoding="utf-8") as f:
        json.dump(vectors, f, indent=2)

    print(f"Generated {len(vectors)} golden vectors in {GOLDEN_VECTORS_JSON}")


if __name__ == "__main__":
    cfg = export_rules()
    generate_golden_vectors(cfg)
