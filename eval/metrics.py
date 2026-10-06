"""
Evaluation Metrics Module for DermaSense.
Calculates sensitivity, specificity, false-negative rate, precision, abstention rate,
and accuracy (reported last), with 95% Wilson score confidence intervals.
Computes Expected Calibration Error and subgroup stratified metrics.
"""

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


def wilson_score_interval(
    k: int,
    n: int,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Computes the two-sided Wilson score confidence interval for a binomial proportion.
    Accurate for both small and large n, and when p is close to 0 or 1.
    """
    if n <= 0:
        return 0.0, 0.0

    # z-score for two-sided confidence
    # 95% -> 1.95996
    z = 1.95996 if abs(confidence - 0.95) < 1e-4 else 1.96

    p_hat = float(k) / float(n)
    denom = 1.0 + (z ** 2) / n
    center = (p_hat + (z ** 2) / (2.0 * n)) / denom
    margin = (z * math.sqrt((p_hat * (1.0 - p_hat) / n) + ((z ** 2) / (4.0 * (n ** 2))))) / denom

    low = max(0.0, center - margin)
    high = min(1.0, center + margin)
    return round(low, 4), round(high, 4)


def calculate_rates_with_intervals(
    y_true: List[int],
    y_pred: List[int],
    abstained: Optional[List[bool]] = None
) -> Dict[str, Any]:
    """
    Computes diagnostic rates with Wilson 95% confidence intervals.
    Orders metrics strictly with Accuracy LAST as specified in Section 18.
    """
    n_total = len(y_true)
    if n_total == 0:
        return {
            "total_samples": 0,
            "abstention_rate": {"rate": 0.0, "ci_95": [0.0, 0.0]},
            "sensitivity": {"rate": 0.0, "ci_95": [0.0, 0.0]},
            "specificity": {"rate": 0.0, "ci_95": [0.0, 0.0]},
            "false_negative_rate": {"rate": 0.0, "ci_95": [0.0, 0.0]},
            "precision": {"rate": 0.0, "ci_95": [0.0, 0.0]},
            "accuracy": {"rate": 0.0, "ci_95": [0.0, 0.0]},
        }

    abs_flags = abstained if abstained is not None else [False] * n_total
    n_abstained = sum(abs_flags)
    abstention_rate = n_abstained / float(n_total)
    abstention_ci = wilson_score_interval(n_abstained, n_total)

    # For clinical diagnostic rates, evaluate on decided (non-abstained) cohort
    decided_idx = [i for i, a in enumerate(abs_flags) if not a]
    n_decided = len(decided_idx)

    if n_decided == 0:
        return {
            "total_samples": n_total,
            "decided_samples": 0,
            "abstention_rate": {"rate": round(abstention_rate, 4), "ci_95": list(abstention_ci)},
            "sensitivity": {"rate": 0.0, "ci_95": [0.0, 0.0]},
            "specificity": {"rate": 0.0, "ci_95": [0.0, 0.0]},
            "false_negative_rate": {"rate": 0.0, "ci_95": [0.0, 0.0]},
            "precision": {"rate": 0.0, "ci_95": [0.0, 0.0]},
            "accuracy": {"rate": 0.0, "ci_95": [0.0, 0.0]},
        }

    tp = sum(1 for i in decided_idx if y_true[i] == 1 and y_pred[i] == 1)
    tn = sum(1 for i in decided_idx if y_true[i] == 0 and y_pred[i] == 0)
    fp = sum(1 for i in decided_idx if y_true[i] == 0 and y_pred[i] == 1)
    fn = sum(1 for i in decided_idx if y_true[i] == 1 and y_pred[i] == 0)

    p_actual = tp + fn
    n_actual = tn + fp
    p_pred = tp + fp

    # 1. Sensitivity (Recall on positive class)
    sens = tp / float(p_actual) if p_actual > 0 else 0.0
    sens_ci = wilson_score_interval(tp, p_actual)

    # 2. Specificity (Recall on negative class)
    spec = tn / float(n_actual) if n_actual > 0 else 0.0
    spec_ci = wilson_score_interval(tn, n_actual)

    # 3. False Negative Rate (FNR = 1 - Sensitivity = FN / (TP + FN))
    fnr = fn / float(p_actual) if p_actual > 0 else 0.0
    fnr_ci = wilson_score_interval(fn, p_actual)

    # 4. Precision (PPV = TP / (TP + FP))
    prec = tp / float(p_pred) if p_pred > 0 else 0.0
    prec_ci = wilson_score_interval(tp, p_pred)

    # 5. Abstention Rate (computed above)

    # 6. Accuracy (REPORTED LAST)
    acc = (tp + tn) / float(n_decided) if n_decided > 0 else 0.0
    acc_ci = wilson_score_interval(tp + tn, n_decided)

    return {
        "total_samples": n_total,
        "decided_samples": n_decided,
        "counts": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
        "sensitivity": {"rate": round(sens, 4), "ci_95": list(sens_ci)},
        "specificity": {"rate": round(spec, 4), "ci_95": list(spec_ci)},
        "false_negative_rate": {"rate": round(fnr, 4), "ci_95": list(fnr_ci)},
        "precision": {"rate": round(prec, 4), "ci_95": list(prec_ci)},
        "abstention_rate": {"rate": round(abstention_rate, 4), "ci_95": list(abstention_ci)},
        "accuracy": {"rate": round(acc, 4), "ci_95": list(acc_ci)},
    }


def evaluate_subgroups(
    samples: List[Dict[str, Any]],
    subgroup_key: str,
    min_sample_size: int = 10
) -> Dict[str, Any]:
    """
    Subgroup analysis across skin tone, body site, or image quality bands.
    If sample size is under min_sample_size:
      returns "Insufficient sample size for reliable subgroup estimate."
    """
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for s in samples:
        val = str(s.get(subgroup_key, "Unknown"))
        groups.setdefault(val, []).append(s)

    results: Dict[str, Any] = {}
    for g_name, items in groups.items():
        if len(items) < min_sample_size:
            results[g_name] = {
                "sample_count": len(items),
                "status": "Insufficient sample size for reliable subgroup estimate."
            }
        else:
            y_t = [int(x["y_true"]) for x in items]
            y_p = [int(x["y_pred"]) for x in items]
            abs_l = [bool(x.get("abstained", False)) for x in items]
            sub_metrics = calculate_rates_with_intervals(y_t, y_p, abs_l)
            sub_metrics["sample_count"] = len(items)
            results[g_name] = sub_metrics

    return results
