# DermaSense Clinical Safety and Governance Architecture

## 1. Core Safety Principles
DermaSense is designed around clinical harm reduction, specifically addressing the widespread misuse of over-the-counter topical corticosteroids and multi-action creams for fungal dermatoses (which causes steroid-modified dermatophytosis / *tinea incognito*).

---

## 2. Invariant Safety Guardrails
1. **Danger Signs Override Everything**:
   - Any danger sign (`facial_involvement`, `severe_pain`, `systemic_symptoms`, `rapid_spreading_hours`, `blistering_or_skin_peeling`, `pus_or_foul_discharge`, `signs_of_anaphylaxis`) immediately halts all downstream processing and routes the case to **Category D** (`EMERGENT`).
   - The AI vision model is intentionally bypassed to avoid delaying urgent care.
2. **Steroid Exposure Memory**:
   - If a patient reports or a label confirms topical steroid exposure with refractory progression (`steroid_risk >= 3`), the case is assigned **Category B** ("Possible steroid-modified rash").
   - This assignment persists **even if the uploaded photo is blurry or inconclusive**, ensuring patients are warned about steroid hazards regardless of camera quality.
3. **Contradiction Failsafe**:
   - Conflicting questionnaire answers (e.g. "No cream used" + "Rash spread despite treatment") drop the case into **Category C** ("Image or answers uncertain").
4. **Vulnerable Profile Monotonicity**:
   - Vulnerable patient flags (`infant`, `pregnancy`, `immunocompromised`) can **only increase urgency** (e.g. ROUTINE -> ELEVATED, ELEVATED -> HIGH).
   - They can **never** lower category, create reassurance, or override a danger sign.

---

## 3. Strict Language Banning (`tests/test_safety.py`)
To prevent over-reliance and unauthorized practice of medicine, the following terms are strictly banned in all generated user-facing outputs:
- `"confirmed"`
- `"diagnosed"`
- `"tinea"`
- `"you have"`
- `"steroid-free"` (banned in medicine label matcher to avoid false security)
- Reassuring terms like `"harmless"`, `"safe to ignore"`, or `"all clear"` are completely prohibited.

Every clinical output is appended with the mandatory safety disclaimer:
> *"DermaSense is an investigational screening prototype. It does not provide medical diagnoses, clinical determinations, or treatment prescriptions. All observations require verification by a qualified healthcare professional."*

---

## 4. No Prescriptions or Medication Instructions
DermaSense strictly enforces:
- **No dosage recommendations** (e.g. mg, frequency, duration).
- **No prescription generation**.
- **No medication alteration instructions** (patients are instructed to consult their physician before stopping or starting any steroid regimen).

---

## 5. Privacy and Data Sovereignty
- **Zero Identification**: No names, telephone numbers, emails, or personal identifiers are collected.
- **Anonymous Case IDs**: All cases receive randomized pseudonymous identifiers (e.g. `case_a1b2c3d4`).
- **In-Memory Processing**: Photos are held strictly in volatile RAM for execution and immediately discarded unless the user explicitly toggles the consent checkbox.
- **DELETE ALL DATA**: An explicit endpoint (`DELETE /history`) allows immediate permanent eradication of all stored screening records.
