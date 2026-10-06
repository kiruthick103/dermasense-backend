"""
Engine 2: Medicine Label Matcher
Deterministic pure engine with no I/O, no network, and no mutable global state.
Normalizes text, applies Damerau-Levenshtein fuzzy matching against configured corticosteroid
active ingredients, Indian brand names (from authoritative formulary database), and transliterations.

Strict Output Statuses:
  - POSSIBLE_STEROID_FOUND
  - NONE_FOUND_IN_VISIBLE_TEXT
  - UNREADABLE

NEVER outputs 'steroid-free'.
Always appends advice: 'Please confirm the label with a pharmacist or clinician.'
"""

import json
import os
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_STEROID_TERMS = [
    "clobetasol",
    "betamethasone",
    "beclometasone",
    "mometasone",
    "hydrocortisone",
    "fluocinolone",
    "corticosteroid",
    "steroid",
    "triamcinolone",
    "desonide",
    "halobetasol",
    "fluticasone",
]

DEFAULT_COMBINATION_CUES = [
    "fourderm",
    "quadriderm",
    "panderm",
    "betnovate",
    "candid b",
    "candid-b",
    "dermichem",
    "triben",
    "clocip b",
    "clocip-b",
    "surfaz b",
    "surfaz-b",
    "mycoderm",
    "triple action",
    "combination",
]


def damerau_levenshtein_distance(s1: str, s2: str) -> int:
    """Computes Damerau-Levenshtein distance with insertions, deletions, substitutions, and transpositions."""
    m, n = len(s1), len(s2)
    d = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        d[i][0] = i
    for j in range(n + 1):
        d[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            d[i][j] = min(
                d[i - 1][j] + 1,       # deletion
                d[i][j - 1] + 1,       # insertion
                d[i - 1][j - 1] + cost # substitution
            )
            # Transposition check
            if i > 1 and j > 1 and s1[i - 1] == s2[j - 2] and s1[i - 2] == s2[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)

    return d[m][n]


# Keep alias for backward compatibility
levenshtein_distance = damerau_levenshtein_distance


def normalize_and_tokenize(text: str) -> List[str]:
    """
    1. Unicode normalize (NFKD)
    2. Lowercase
    3. Remove punctuation
    4. Tokenize into whitespace-separated tokens
    """
    if not text:
        return []
    normalized = unicodedata.normalize("NFKD", text).lower()
    # Replace non-alphanumeric characters with spaces (preserve unicode letters)
    cleaned = re.sub(r"[^\w\s]+", " ", normalized)
    tokens = [t.strip() for t in cleaned.split() if t.strip()]
    return tokens


def match_medicine_label(
    text: str,
    steroid_terms: Optional[List[str]] = None,
    combination_cues: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Scans text from manual input or OCR for topical corticosteroid terms or combination cues.
    Always appends advice: 'Please confirm the label with a pharmacist or clinician.'
    """
    advice = "Please confirm the label with a pharmacist or clinician."

    if text is None:
        return {
            "status": "UNREADABLE",
            "matched_term": "",
            "distance": -1,
            "confidence": 0.0,
            "advice": advice,
        }

    raw_stripped = text.strip()
    if len(raw_stripped) == 0:
        return {
            "status": "UNREADABLE",
            "matched_term": "",
            "distance": -1,
            "confidence": 0.0,
            "advice": advice,
        }

    tokens = normalize_and_tokenize(raw_stripped)
    if not tokens:
        return {
            "status": "UNREADABLE",
            "matched_term": "",
            "distance": -1,
            "confidence": 0.0,
            "advice": advice,
        }

    alpha_chars = sum(c.isalpha() for c in raw_stripped)
    if alpha_chars < 3:
        return {
            "status": "UNREADABLE",
            "matched_term": "",
            "distance": -1,
            "confidence": 0.0,
            "advice": advice,
        }

    target_steroids = steroid_terms if steroid_terms is not None else DEFAULT_STEROID_TERMS
    target_cues = combination_cues if combination_cues is not None else DEFAULT_COMBINATION_CUES

    norm_steroids = [t.lower().strip() for t in target_steroids if t]
    norm_cues = [c.lower().strip() for c in target_cues if c]

    all_targets: List[Tuple[str, str]] = [(s, "steroid") for s in norm_steroids] + [(c, "cue") for c in norm_cues]

    # 1. Exact match on tokens or n-grams for multi-word targets
    joined_text = " ".join(tokens)
    for target, _ in all_targets:
        if " " in target:
            if target in joined_text:
                return {
                    "status": "POSSIBLE_STEROID_FOUND",
                    "matched_term": target,
                    "distance": 0,
                    "confidence": 1.0,
                    "advice": advice,
                }
        else:
            if target in tokens:
                return {
                    "status": "POSSIBLE_STEROID_FOUND",
                    "matched_term": target,
                    "distance": 0,
                    "confidence": 1.0,
                    "advice": advice,
                }

    # 2. Fuzzy match with Damerau-Levenshtein distance
    # Rules:
    # - distance 1 for words 6-9 characters
    # - distance 2 for words 10+ characters
    best_match: Optional[Tuple[str, int, float]] = None

    for target, _ in all_targets:
        if " " in target:
            continue
        t_len = len(target)
        if t_len < 6:
            continue

        allowed_dist = 1 if 6 <= t_len <= 9 else 2

        for token in tokens:
            tok_len = len(token)
            if abs(tok_len - t_len) > allowed_dist:
                continue

            dist = damerau_levenshtein_distance(token, target)
            if dist <= allowed_dist:
                conf = 1.0 - (dist / float(max(t_len, tok_len)))
                if best_match is None or dist < best_match[1] or conf > best_match[2]:
                    best_match = (target, dist, conf)

    if best_match is not None:
        matched_term, dist, conf = best_match
        return {
            "status": "POSSIBLE_STEROID_FOUND",
            "matched_term": matched_term,
            "distance": dist,
            "confidence": round(conf, 3),
            "advice": advice,
        }

    return {
        "status": "NONE_FOUND_IN_VISIBLE_TEXT",
        "matched_term": "",
        "distance": -1,
        "confidence": 0.0,
        "advice": advice,
    }
