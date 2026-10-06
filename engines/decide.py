"""
Engine 4: Decision Engine
Deterministic pure engine with no I/O, no network, and no mutable global state.
Synthesizes danger signs, contradictions, quality assessments, risk scores, and vulnerable
status into an audit-logged Category decision and urgency rating.
"""

from typing import Any, Dict, List, Optional


DEFAULT_CONFIG = {
    "decision": {
        "steroid_risk_threshold": 3,
        "fungal_pattern_threshold": 3,
    },
    "categories": {
        "A": "Possible fungal pattern, clinical review recommended.",
        "B": "Possible steroid-modified or treatment-resistant rash.",
        "C": "Image or answers uncertain, clinical assessment recommended.",
        "D": "Seek urgent in-person care now.",
    },
    "safety": {
        "disclaimer": (
            "DermaSense is an investigational screening prototype. "
            "It does not provide medical diagnoses, clinical determinations, or treatment prescriptions. "
            "All observations require verification by a qualified healthcare professional."
        ),
        "prototype_status": "prototype_not_clinically_validated",
    }
}


def make_decision(
    danger_signs: List[str],
    contradictions: List[str],
    steroid_risk: int,
    fungal_pattern: int,
    quality_findings: Dict[str, Any],
    model_output: Optional[Dict[str, Any]] = None,
    vulnerable_flags: Optional[List[str]] = None,
    rules_fired: Optional[List[Dict[str, Any]]] = None,
    user_reported_facts: Optional[List[str]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Executes the DermaSense deterministic decision ladder in strict order:
      1. ANY danger sign -> Category D (returns immediately, omitting model output)
      2. Contradictory answers -> Category C
      3. steroid_risk >= configured threshold -> Category B (persists even if image poor/uncertain)
      4. Poor image quality -> Category C
      5. fungal_pattern >= configured threshold -> Category A
      6. Otherwise -> Category C

    Vulnerable group flags can only elevate urgency.
    """
    cfg = config or DEFAULT_CONFIG
    d_cfg = cfg.get("decision", DEFAULT_CONFIG["decision"])
    cat_cfg = cfg.get("categories", DEFAULT_CONFIG["categories"])
    safe_cfg = cfg.get("safety", DEFAULT_CONFIG["safety"])

    steroid_thresh = int(d_cfg.get("steroid_risk_threshold", 3))
    fungal_thresh = int(d_cfg.get("fungal_pattern_threshold", 3))
    disclaimer_text = safe_cfg.get("disclaimer", DEFAULT_CONFIG["safety"]["disclaimer"])
    status_text = safe_cfg.get("prototype_status", DEFAULT_CONFIG["safety"]["prototype_status"])

    active_vulnerable = [v for v in (vulnerable_flags or []) if v]
    facts = list(user_reported_facts or [])
    rule_trace: List[str] = []
    reasons: List[str] = []

    # Step 1: ANY danger sign -> Category D immediately
    active_danger = [d for d in (danger_signs or []) if d]
    if len(active_danger) > 0:
        rule_trace.append(f"Danger sign triggered: {', '.join(active_danger)}")
        reasons.append(
            f"Urgent medical warning signs noted: {', '.join(active_danger)}."
        )
        return {
            "category": "D",
            "urgency": "EMERGENT",
            "category_description": cat_cfg["D"],
            "reasons": reasons,
            "rule_trace": rule_trace,
            "user_reported_facts": facts,
            "quality_findings": quality_findings or {},
            "model_output": {
                "status": status_text,
                "note": "Visual model bypassed due to emergency indicators."
            },
            "recommended_action": "Seek immediate in-person evaluation at an emergency clinic or hospital.",
            "disclaimer": disclaimer_text,
        }

    # Step 2: Contradictory answers -> Category C
    if len(contradictions) > 0:
        rule_trace.append(f"Contradictions detected: {'; '.join(contradictions)}")
        reasons.append("Reported questionnaire responses contain contradictory clinical statements.")
        urgency = "ELEVATED" if len(active_vulnerable) > 0 else "ROUTINE"
        if len(active_vulnerable) > 0:
            reasons.append(f"Urgency elevated due to vulnerable profile: {', '.join(active_vulnerable)}.")
        sanitized_model = dict(model_output or {})
        sanitized_model["status"] = status_text
        return {
            "category": "C",
            "urgency": urgency,
            "category_description": cat_cfg["C"],
            "reasons": reasons,
            "rule_trace": rule_trace,
            "user_reported_facts": facts,
            "quality_findings": quality_findings or {},
            "model_output": sanitized_model,
            "recommended_action": "Schedule an in-person clinical review to clarify clinical details.",
            "disclaimer": disclaimer_text,
        }

    # Step 3: steroid_risk >= configured threshold -> Category B
    # (Remains B even if image quality is poor)
    if steroid_risk >= steroid_thresh:
        rule_trace.append(
            f"Steroid risk score ({steroid_risk}) reached or exceeded threshold ({steroid_thresh})."
        )
        reasons.append(
            "History suggests potential topical steroid exposure or refractory progression."
        )
        urgency = "HIGH" if len(active_vulnerable) > 0 else "ELEVATED"
        if len(active_vulnerable) > 0:
            reasons.append(f"Urgency elevated due to vulnerable profile: {', '.join(active_vulnerable)}.")
        sanitized_model = dict(model_output or {})
        sanitized_model["status"] = status_text
        return {
            "category": "B",
            "urgency": urgency,
            "category_description": cat_cfg["B"],
            "reasons": reasons,
            "rule_trace": rule_trace,
            "user_reported_facts": facts,
            "quality_findings": quality_findings or {},
            "model_output": sanitized_model,
            "recommended_action": "Consult a dermatologist or qualified physician for examination and treatment review.",
            "disclaimer": disclaimer_text,
        }

    # Step 4: Poor image quality -> Category C
    image_acceptable = (quality_findings or {}).get("acceptable", True)
    if not image_acceptable:
        quality_reasons = (quality_findings or {}).get("reasons", ["IMAGE_QUALITY_DEFICIENT"])
        rule_trace.append(f"Photo quality check failed: {', '.join(quality_reasons)}.")
        reasons.append(f"Uploaded photograph did not meet quality standards ({', '.join(quality_reasons)}).")
        urgency = "ELEVATED" if len(active_vulnerable) > 0 else "ROUTINE"
        if len(active_vulnerable) > 0:
            reasons.append(f"Urgency elevated due to vulnerable profile: {', '.join(active_vulnerable)}.")
        sanitized_model = dict(model_output or {})
        sanitized_model["status"] = status_text
        return {
            "category": "C",
            "urgency": urgency,
            "category_description": cat_cfg["C"],
            "reasons": reasons,
            "rule_trace": rule_trace,
            "user_reported_facts": facts,
            "quality_findings": quality_findings or {},
            "model_output": sanitized_model,
            "recommended_action": "Retake the photograph under clear lighting or consult a healthcare professional in person.",
            "disclaimer": disclaimer_text,
        }

    # Step 5: fungal_pattern >= configured threshold -> Category A
    if fungal_pattern >= fungal_thresh:
        rule_trace.append(
            f"Fungal pattern score ({fungal_pattern}) reached or exceeded threshold ({fungal_thresh})."
        )
        reasons.append("Visual or clinical features show characteristics consistent with a fungal rash pattern.")
        urgency = "ELEVATED" if len(active_vulnerable) > 0 else "ROUTINE"
        if len(active_vulnerable) > 0:
            reasons.append(f"Urgency elevated due to vulnerable profile: {', '.join(active_vulnerable)}.")
        sanitized_model = dict(model_output or {})
        sanitized_model["status"] = status_text
        return {
            "category": "A",
            "urgency": urgency,
            "category_description": cat_cfg["A"],
            "reasons": reasons,
            "rule_trace": rule_trace,
            "user_reported_facts": facts,
            "quality_findings": quality_findings or {},
            "model_output": sanitized_model,
            "recommended_action": "Consult a healthcare professional for in-person inspection and appropriate skin assessment.",
            "disclaimer": disclaimer_text,
        }

    # Step 6: Otherwise -> Category C
    rule_trace.append("Findings do not meet specific Category A or B thresholds; assigned to default uncertainty review.")
    reasons.append("Clinical features or image confidence were inconclusive.")
    urgency = "ELEVATED" if len(active_vulnerable) > 0 else "ROUTINE"
    if len(active_vulnerable) > 0:
        reasons.append(f"Urgency elevated due to vulnerable profile: {', '.join(active_vulnerable)}.")
    sanitized_model = dict(model_output or {})
    sanitized_model["status"] = status_text

    return {
        "category": "C",
        "urgency": urgency,
        "category_description": cat_cfg["C"],
        "reasons": reasons,
        "rule_trace": rule_trace,
        "user_reported_facts": facts,
        "quality_findings": quality_findings or {},
        "model_output": sanitized_model,
        "recommended_action": "Have the affected skin evaluated directly by a clinician.",
        "disclaimer": disclaimer_text,
    }
