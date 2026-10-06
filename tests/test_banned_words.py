"""
Safety String-Scan Test Suite: Banned Reassuring & Diagnostic Words.
Enforces that user-facing text never reassures ("you are fine") or diagnoses
("confirmed", "diagnosed", "you have", "suffering from") across English, Hindi, and Kannada.
"""

import os
import re
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML = os.path.join(ROOT_DIR, "web", "index.html")

BANNED_PHRASES = {
    "en": [
        "you are fine",
        "nothing to worry about",
        "looks normal",
        "healthy skin",
        "you have",
        "suffering from",
        "confirmed diagnosis",
        "diagnosed with"
    ],
    "hi": [
        "आप ठीक हैं",
        "चिंता की कोई बात नहीं",
        "आपको बीमारी है"
    ],
    "kn": [
        "ನೀವು ಚೆನ್ನಾಗಿದ್ದೀರಿ",
        "ಚಿಂತಿಸಬೇಕಾಗಿಲ್ಲ"
    ]
}


def test_banned_words_not_in_index_html():
    with open(INDEX_HTML, "r", encoding="utf-8") as f:
        html = f.read().lower()

    for lang, phrases in BANNED_PHRASES.items():
        for phrase in phrases:
            # Check phrase does not appear in user-facing html content
            matches = [m.start() for m in re.finditer(re.escape(phrase.lower()), html)]
            assert len(matches) == 0, f"Found banned phrase '{phrase}' ({lang}) in web/index.html"


def test_decision_engine_never_reassures():
    from engines.decide import make_decision
    import yaml

    rules_path = os.path.join(ROOT_DIR, "config", "rules.yaml")
    with open(rules_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Test all categories
    for cat in ["A", "B", "C", "D"]:
        dec = make_decision(
            danger_signs=["fever"] if cat == "D" else [],
            contradictions=["contr"] if cat == "C" else [],
            steroid_risk=4 if cat == "B" else 0,
            fungal_pattern=3 if cat == "A" else 0,
            quality_findings={"acceptable": True},
            config=cfg
        )
        action_text = (dec.get("recommended_action") or "").lower()
        desc_text = (dec.get("category_description") or "").lower()

        for phrase in BANNED_PHRASES["en"]:
            assert phrase not in action_text, f"Banned phrase '{phrase}' found in Category {cat} action"
            assert phrase not in desc_text, f"Banned phrase '{phrase}' found in Category {cat} description"
