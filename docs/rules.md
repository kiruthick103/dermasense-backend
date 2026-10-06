# Rules and thresholds

> **PROTOTYPE RULES, NOT CLINICAL STANDARDS**
> Every threshold below is an illustrative default for hackathon demonstration.
> None of these values have been validated by a clinical trial.

## 1. Photo quality

| Check | How it works | Threshold | Output |
|:------|:-------------|:----------|:-------|
| Blur | Laplacian variance of greyscale image | < 100 = blurry | `BLUR` reason code |
| Brightness | Mean pixel intensity | < 50 = too dark, > 220 = too bright | `DARK` / `BRIGHT` |
| Glare | Fraction of pixels with high value + low saturation | > 15 % = glare | `GLARE` |
| Skin coverage | Fraction of skin-tone pixels in frame | < 10 % = too far or obstructed | `TOO_FAR` / `OBSTRUCTED` |

Quality never affects severity. A poor photo only routes to Category C ("more information needed").

## 2. Label matcher

Normalise text (lowercase, strip whitespace) then fuzzy-match against:

- clobetasol, betamethasone, beclometasone, mometasone, hydrocortisone, "steroid", "corticosteroid"
- Typo tolerance: Levenshtein ≤ 1 for 6-9 letter words, ≤ 2 for 10+ letter words

### Output (one of three, never "steroid-free"):
1. **Possible steroid ingredient detected** + "Please confirm the label with a pharmacist or clinician."
2. **No steroid ingredient detected in visible text** + same advice
3. **Label unreadable or uncertain** + same advice

## 3. Risk scoring

Answers are YES / NO / NOT_SURE. NOT_SURE adds zero points and widens the confidence band.

### Steroid risk score

| Rule | Points | Fires when |
|:-----|:-------|:-----------|
| Unknown or unprescribed cream | +2 | `used_any_cream` = YES AND `prescribed_by_clinician` ≠ YES |
| Steroid name seen or label hit | +3 | `steroid_name_visible` = YES OR label matcher = POSSIBLE_STEROID_FOUND |
| Spread despite treatment | +2 | `spread_despite_treatment` = YES |
| Returned after stopping | +1 | `returned_after_stopping` = YES |
| Combination wording | +1 | `combination_wording` = YES |

### Fungal pattern score

| Rule | Points | Fires when |
|:-----|:-------|:-----------|
| Model confidence above threshold | +2 | ONNX model label = "compatible" AND confidence ≥ 0.4 |
| Clinical pattern cues | +1 | `itchy_ring_or_scaly` = YES |
| Duration over 1 week | +1 | `duration` = YES |

## 4. Decision ladder (evaluated in this exact order)

| Priority | Condition | Category | Description |
|:---------|:----------|:---------|:------------|
| 1 | Any danger sign checked | **D** | Seek care now (Emergent) |
| 2 | Contradictory answers | **C** | More information needed |
| 3 | Steroid risk ≥ 3 | **B** | Cream history needs review |
| 4 | Poor image quality / Non-skin | **C** | More information needed |
| 5 | Fungal pattern ≥ 2 | **A** | Pattern worth checking |
| 6 | Otherwise | **C** | More information needed |

### Emergency Danger Signs (Immediate Category D Escalation):
1. **High fever or chills**
2. **Rapidly spreading rash within hours**
3. **Severe pain, blistering, or skin peeling off**
4. **Rash involving eyes or inside the mouth**
5. **Genital involvement with severe pain or swelling**
6. **Newborn or young infant (< 3 months) with widespread rash**
7. **Black or purple skin patches**

- Any ticked emergency sign immediately escalates to **Category D**.
- Image vision findings and model inference are strictly suppressed/bypassed to avoid reassuring patients in emergencies.
- Vulnerable status (infant, pregnancy, immunocompromised) elevates urgency (e.g. from ROUTINE to ELEVATED), never lowering it.

## 5. Visual model

Interface: `predict(image, config) → {label, confidence, isPlaceholder}`

- Labels: "compatible", "not clearly compatible", "uncertain"
- Always shown with: "Prototype model output, not clinically validated"
- Placeholder model returns `{isPlaceholder: true}` with no accuracy claims

## 6. Triage ordering

1. Danger signs first
2. Possible steroid-modified spreading rash
3. Persistent rash
4. Uncertain image
5. Education-only

Ties broken by newest case first, then by case ID (stable sort).

## 7. Forbidden outputs

The system must never output any of these words/phrases to users:
- "confirmed", "diagnosed", "tinea", "you have"
- Any phrase that reassures ("you are fine", "nothing to worry about", "looks normal")
- Accuracy figures for a placeholder model
- Dosing, prescribing, or advice to start/stop/change medication
