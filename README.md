# DermaSense — Indian Government Hospital Skin Rash Screening & Referral Portal

> **Prototype Notice:** Prototype screening aid. Not an official government or hospital service.  
> DermaSense is a screening and referral decision aid. It **NEVER** diagnoses, prescribes, gives dosages, or instructs anyone to start, stop, or change medications. No result may ever reassure ("you are fine").

DermaSense is an accessible, official-style public health portal designed for community skin screening, corticosteroid misuse monitoring, and structured triage referral across India. Built strictly with Vanilla HTML/CSS/JavaScript and deterministic Python reference engines — **zero heavy frameworks**. Works 100% offline via Service Worker.

---

## Live Deployment & Local Server

- **Production URL:** [https://dermaclean.vercel.app](https://dermaclean.vercel.app)
- **Local Dev Server:** `http://127.0.0.1:8008`

### Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch FastAPI server on port 8008
python -m uvicorn main:app --host 127.0.0.1 --port 8008

# 3. Open browser at http://127.0.0.1:8008
```

---

## Official Government Hospital Portal Design System

- **Tricolour Accent Strip:** Thin decorative Indian saffron (#ff9933), white (#ffffff), and green (#138808) header line.
- **Utility Bar:**
  - Skip to main content link (WCAG 2.1 AA / GIGW 3.0 conformance).
  - Text size adjustment (`A-`, `A`, `A+` buttons scaling from 14px to 20px).
  - High-contrast toggle (black/white high-visibility palette with $> 7:1$ contrast ratios).
  - Trilingual language switcher: English (EN), Hindi (हिं), Kannada (ಕ).
- **Aesthetic Guidelines:**
  - Curated Indian hospital palette: Navy primary `#123a6f`, Clinical Green `#1c7c3c`, Saffron accent `#e07b00`, Danger Red `#c0182b`.
  - Clean surfaces: White `#ffffff` and pale blue-grey `#f4f6f9`.
  - Crisp 6px border radii, thin borders, zero gradients, zero emojis (pure inline-SVG line icons).
  - Modern typography: Noto Sans, Noto Sans Devanagari, and Noto Sans Kannada.
- **Emergency 108 Strip:** Prominent advisory banner linking directly to `tel:108` (National Ambulance Service) and `112`.

---

## 7-Step Offline Patient Screening Flow

The screening flow operates offline without requiring any account login:
1. **Welcome & Consent:** Clear disclaimers and separate toggles for *"save this case on this device"* and *"share with a health worker"* (both **OFF** by default). Next disabled until the user acknowledges the advisory.
2. **About the Person:** Age group selection (Infant, Child, Adult, Older Adult); pregnancy and immunocompromised flags.
3. **About the Rash:** Body location, duration tier, and separate checkboxes for itchy, ring-shaped, and scaly characteristics.
4. **Photos (Dual Inputs):** Both Close-up and Wider view slots with equal **Camera** and **Upload** buttons feeding the automatic analysis pipeline.
5. **Cream History:** Comprehensive history of topical cream usage, prescriber type (doctor / pharmacist / friend / not sure), steroid keyword recognition, combination formulations, and spread/recurrence history.
6. **Safety Check (10 Danger Signs):** Multi-select checklist for breathing distress, skin peeling, eye involvement, severe pain, fever, pus/black skin, or infant rash. **Any positive sign routes immediately to Category D (Emergent) BEFORE any image or pattern result is evaluated.**
7. **Result & Actionable Referral:**
   - Color-coded Category Card (A, B, C, or D) with textual urgency badges.
   - Actionable referral instructions ("What to do next").
   - Explicit clinical boundaries ("What this app cannot tell you").
   - Translucent rash outline with toggle on user photos.
   - **"Looks similar to (not a diagnosis)"** pattern comparison panel with strength rating.
   - Expandable clinical rationale trace ("How we reached this result").
   - PDF referral summary print/download, copy summary, follow-up reminder, and emergency locator fallback.

---

## Photo Pipeline: Dual Input & Automatic Analysis

Both live camera and uploaded photos feed into an identical analysis pipeline:

### 1. WebRTC Live Camera (`camera.js`)
- `navigator.mediaDevices.getUserMedia` with environment-facing preference (`ideal: 1920x1080`).
- Live quality evaluation ring (~5 fps) measuring blur, brightness, glare, and skin obstruction with real-time tips (*"Hold steady"*, *"More light needed"*, *"Move closer"*).
- Flip camera, torch support, and graceful error handlers for `NotAllowedError`, `NotFoundError`, and `OverconstrainedError`.

### 2. Photo Upload & Artifact Verification
- Accepts JPEG, PNG, WebP, and HEIC (automatic in-browser JPEG conversion).
- Automatic EXIF orientation correction and **immediate metadata/GPS stripping**.
- Advanced upload artifact detection:
  - Fast Fourier Transform (FFT) moire/screen photography detection.
  - JPEG compression blockiness estimation.
  - Low-resolution rejection ($< 320\text{ px}$).
  - Cartoon/drawing detection.
- **Upload Quality Flag Penalty:** Any detected upload defect caps pattern model strength at **Moderate**.

### 3. Automatic 6-Stage Analysis Progress
Screen-reader announced progress sequence:
1. Checking photo quality
2. Finding skin
3. Measuring the rash area
4. Comparing patterns
5. Combining your answers
6. Preparing your result

---

## Skin-Condition Pattern Model & Strength Bands

The pattern matching engine evaluates similarity across 5 clinician-verified patterns:
1. `fungal_ring_pattern` (Fungal-type ring pattern)
2. `eczema_dermatitis_pattern` (Eczema or dermatitis-like)
3. `psoriasis_pattern` (Psoriasis-like)
4. `bacterial_infection_pattern` (Bacterial-infection-like)
5. `other_unclear_pattern` (Other / unclear)

### Strength Rating Bands
- **Strong:** Calibrated probability $\ge 0.75$, conformal prediction set size $= 1$, interpretable visual features agree, good photo quality.
- **Moderate:** Calibrated probability $\ge 0.50$, conformal set size $\le 2$.
- **Weak:** Calibrated probability $\ge 0.30$, passes out-of-distribution check.
- **Not Enough to Say:** Out-of-distribution, non-skin, or low quality (model abstains).

### Strict Safety Constraints
- Panel title is strictly: **"Looks similar to (not a diagnosis)"**.
- Wording disclaimer: *"Only a clinician who examines the skin can tell what it is."*
- Banned words enforced: *"diagnosed"*, *"confirmed"*, *"you have"*, and *"suffering from"* are prohibited across the entire portal in all languages.
- Conservative ensemble: A fungal pattern counts toward scoring points **only when the network and interpretable ring features agree**.

---

## Role-Based Login & Demo Accounts

Controlled by `DEMO_MODE=true` in environment configuration:

| Role | Username | Password / OTP | Key Dashboard Capabilities |
| :--- | :--- | :--- | :--- |
| **Patient** | `patient.demo` | OTP: `123456` | Start check, view past local checks, delete own data |
| **Health Worker (ASHA)** | `asha.demo` | `Demo@2026` | Community triage queue, case referral notes, printable referral slips |
| **Pharmacist** | `pharmacist.demo` | `Demo@2026` | Formulation brand/steroid verifier tool. **Never sees photos or patient cases (HTTP 403)** |
| **Doctor** | `doctor.demo` | `Demo@2026` | Referred patient consultations, records clinician assessment notes |
| **Analyst** | `analyst.demo` | `Demo@2026` | State/district aggregate metrics, steroid misuse rates, CSV export ($< 5$ cohorts masked) |
| **Admin** | `admin.demo` | `Demo@2026` | Security audit trail, reset demo data. **Cannot access clinical cases** |

---

## Test Suites & Parity Verification

```bash
# 1. Run complete Python test suite (60 unit & integration tests)
python -m pytest tests/

# 2. Run JavaScript Vision Engine tests (Node.js)
node tests/test_vision_engine.js

# 3. Run Golden Vector Parity tests (verifies 100% JS-Python parity)
node tests/test_golden_parity.js

# 4. Run API & RBAC endpoint health checks
python check_api.py
```

### Test Coverage Highlights
- **Decision Ladder:** Every path to Category A, B, C, and D verified.
- **Danger Sign Isolation:** Any danger sign routes directly to Category D with pattern panel hidden.
- **Golden Vectors:** 7 comprehensive test vectors pass in both Python and JavaScript with identical outputs.
- **RBAC Matrix:** Data minimization proven (Pharmacist blocked from patient cases, Analyst limited to aggregates, Admin limited to logs).
- **String Scans:** Automated scanner confirms zero banned reassuring or diagnostic words in English, Hindi, and Kannada.

---

## Documentation Directory

- [`docs/rules.md`](docs/rules.md): Complete specification of rules ladder, risk scoring points, and triage thresholds.
- [`docs/quality.md`](docs/quality.md): Image quality engine thresholds, ITA formulas, and upload artifact algorithms.
- [`docs/data.md`](docs/data.md): Training dataset provenance, licensed subsets, and class distributions.
- [`docs/eval_report.md`](docs/eval_report.md): Calibration metrics, sensitivity/specificity, ECE curves, and subgroup analysis.
- [`docs/model_card.md`](docs/model_card.md): Detailed model card for the pattern similarity classifier.
- [`docs/safety.md`](docs/safety.md): Clinical boundaries, banned words enforcement, and emergency referral protocols.
- [`docs/security.md`](docs/security.md): RBAC matrix, token lifecycle, password hashing, and audit logging.
- [`docs/privacy.md`](docs/privacy.md): Zero default retention, DPDP compliance, and right-to-erasure workflows.
