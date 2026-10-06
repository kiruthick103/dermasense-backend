# DermaSense Model Card: Skin-Condition Pattern Similarity Classifier

## Model Overview
- **Model Name:** DermaSense Lightweight Pattern Matcher (MobileNetV3-Small / EfficientNet-Lite0 int8 quantized export)
- **Model Type:** Multiclass Convolutional Neural Network with Conformal Prediction Sets & Calibrated Softmax
- **Framework:** PyTorch reference, exported to ONNX int8 (< 5 MB runtime size)
- **Primary Clinical Purpose:** Prototype screening and community referral decision aid. **Not a medical diagnostic tool.**

---

## Intended Use & Clinical Scope
- **Intended Users:** Community health workers (ASHAs/ANMs), pharmacists, triage nurses, and citizens seeking preliminary referral guidance.
- **Intended Context:** In-person screening or triage triage queues in rural/semi-urban Indian primary care settings (PHCs, CHCs).
- **Out of Scope & Prohibited Uses:**
  - Definitive clinical diagnosis of dermatological diseases.
  - Drug prescribing, dosage recommendations, or advice to start/stop medications.
  - Reassuring a patient ("you are fine" or "benign rash").
  - Autonomous clinical decision-making without clinician examination.

---

## Pattern Classes & Taxonomy
In compliance with clinical verification and licensed data availability, the model evaluates similarity against 5 discrete patterns:
1. `fungal_ring_pattern`: Compatible with superficial annular fungal patterns (tinea corporis/cruris/incognito).
2. `eczema_dermatitis_pattern`: Erythematous, ill-defined vesicular or lichenified eczema/dermatitis-like patterns.
3. `psoriasis_pattern`: Well-demarcated erythematous plaques with silvery micaceous scale patterns.
4. `bacterial_infection_pattern`: Honey-colored crusts (impetigo-like) or folliculitis patterns.
5. `other_unclear_pattern`: Atypical, polymorphic, out-of-distribution, or unresolvable patterns.

---

## Conformal Prediction & Strength Bands
To prevent overconfident false reassurances, the model outputs split conformal prediction sets achieving an empirical $1 - \alpha = 80\%$ coverage guarantee:
- **Strong:** Calibrated probability $\ge 0.75$, conformal prediction set size $= 1$, interpretable visual features (ring profile, redness contrast) agree, and photo quality is verified.
- **Moderate:** Calibrated probability $\ge 0.50$, conformal set size $\le 2$.
- **Weak:** Calibrated probability $\ge 0.30$, out-of-distribution check passed.
- **Not Enough to Say (Abstention):** Uncalibrated, high-entropy, poor lighting/focus, non-skin, or energy score $> -3.0$.

### Upload Quality Penalty
Photos submitted via file upload are subjected to automated artifact screening (FFT moire detection, JPEG compression blockiness, cartoon/flat entropy). If any upload artifact is detected, the maximum assignable strength is capped at **Moderate**.

---

## Training Data & Ethical Governance
- **Datasets:** Licensed clinical dermatology repositories (Fitzpatrick17k, DDI, SCIN) combined with consented Indian clinical cases under institutional ethics clearance.
- **Fairness & Skin-Tone Auditing:** Evaluated across Fitzpatrick skin phototypes (I through VI) using Individual Typology Angle (ITA):
  - Type I–II (Very Light, ITA $> 55^\circ$)
  - Type III (Light, ITA $41^\circ - 55^\circ$)
  - Type IV (Intermediate, ITA $28^\circ - 41^\circ$)
  - Type V (Tan/Brown, ITA $10^\circ - 28^\circ$)
  - Type VI (Dark, ITA $< 10^\circ$)
- **Data Minimization:** No personal identifiable information (PII) or biometric facial data is trained or persisted. All metadata and EXIF GPS tags are stripped prior to ingestion.

---

## Limitations & Cautions
- Does not replace dermoscopic, histopathological, or KOH mount microscopic confirmation.
- Ring-shaped lesions can occur in granuloma annulare, erythema annulare centrifugum, or subacute lupus erythematosus; similarity to fungal pattern is an indicator for referral, never a confirmation.
