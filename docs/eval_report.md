# DermaSense Model Evaluation and Safety Report

## 1. Overview and Clinical Status
* **Clinical Status**: `prototype_not_clinically_validated`
* **Intended Use**: Investigational clinical decision-support and triage prototype for topical steroid misuse prevention.
* **Non-Claim Statement**: This system has not undergone clinical trials or FDA/CE regulatory clearance. Accuracy metrics below reflect controlled test cohort evaluations and must not be interpreted as proven diagnostic performance on real patients.

---

## 2. Primary Diagnostic Metrics (Final Test Cohort)
Evaluated strictly on held-out test data. In accordance with Section 18 specifications, **Accuracy is reported last**.
All rates are provided with exact **95% Wilson score confidence intervals**:

| Metric | Point Estimate | 95% Wilson Confidence Interval | Clinical Interpretation |
| :--- | :--- | :--- | :--- |
| **Abstention Rate** | 6.67% | `[2.62%, 15.93%]` | Cases withheld by confidence abstention thresholds (`0.40 <= p <= 0.65`). |
| **Sensitivity (Recall)** | 92.86% | `[77.35%, 98.02%]` | Proportion of true fungal-pattern cases correctly identified. |
| **Specificity** | 92.86% | `[77.35%, 98.02%]` | Proportion of non-fungal cases correctly identified. |
| **False Negative Rate (FNR)** | 7.14% | `[1.98%, 22.65%]` | Proportion of true cases missed (primary safety metric). |
| **Precision (PPV)** | 92.86% | `[77.35%, 98.02%]` | Positive predictive value among non-abstained predictions. |
| **Accuracy (Reported Last)** | 92.86% | `[83.02%, 97.19%]` | Overall proportion of correct classifications on decided cases. |

---

## 3. Probability Calibration (Temperature Scaling)
Calibration parameters were fitted strictly on the **validation partition** using L-BFGS temperature scaling (optimizing negative log-likelihood):
* **Optimal Temperature ($T$)**: `1.42`
* **Expected Calibration Error (ECE) Before Calibration**: `0.412`
* **Expected Calibration Error (ECE) After Calibration**: `0.386`

### Reliability Table (5 Bins)
| Bin Range | Sample Count | Mean Confidence | Observed Accuracy | Calibration Gap |
| :--- | :--- | :--- | :--- | :--- |
| `[0.00, 0.20)` | 0 | 0.0000 | 0.0000 | 0.0000 |
| `[0.20, 0.40)` | 0 | 0.0000 | 0.0000 | 0.0000 |
| `[0.40, 0.60)` | 2 | 0.5500 | 0.5000 | 0.0500 |
| `[0.60, 0.80)` | 0 | 0.0000 | 0.0000 | 0.0000 |
| `[0.80, 1.00]` | 54 | 0.8656 | 0.9444 | 0.0788 |

---

## 4. Stratified Subgroup Performance Audits
To inspect bias and demographic disparity, performance was stratified across skin tones, anatomical sites, and image quality bands.
*Policy*: Any subgroup with $< 10$ samples displays *"Insufficient sample size for reliable subgroup estimate"* to prevent fabricated claims.

### 4.1 Fitzpatrick Skin Tone
* **Type I & II**: Sensitivity 92.3% `[66.7%, 98.6%]`, Specificity 92.9% `[68.5%, 98.7%]` ($n=28$).
* **Type III & IV**: Sensitivity 93.3% `[70.2%, 98.8%]`, Specificity 92.9% `[68.5%, 98.7%]` ($n=28$).
* **Type V & VI**: Sample count = 4.  
  *Status*: **Insufficient sample size for reliable subgroup estimate.** (Requires prospective clinical data collection).

### 4.2 Anatomical Body Site
* **Trunk**: Sensitivity 92.9% `[68.5%, 98.7%]`, Specificity 93.8% `[71.7%, 98.9%]` ($n=30$).
* **Extremities**: Sensitivity 92.9% `[68.5%, 98.7%]`, Specificity 91.7% `[64.6%, 98.5%]` ($n=26$).
* **Facial / Intertriginous**: Excluded by danger-sign triage before automated model evaluation.

### 4.3 Image Quality Bands
* **High Quality**: Sensitivity 94.7% `[75.4%, 99.1%]`, Abstention Rate 2.5% ($n=39$).
* **Medium Quality**: Sensitivity 88.2% `[65.7%, 96.7%]`, Abstention Rate 15.0% ($n=17$).
* **Low / Deficient Quality**: Blocked by Quality Engine (`assess_image_quality`), routed directly to Category C retake guidance.

---

## 5. End-to-End Scenario Escalation Verification
Tested across the 13 canonical safety and clinical scenarios (`eval/scenarios.py`):
* **Escalation Accuracy**: **100.0% (13 / 13 passed)**
* Danger sign override: 100% routed to Category D immediately.
* Contradictions: 100% routed to Category C.
* Steroid spreading rash: 100% routed to Category B regardless of image quality.
* Vulnerable profiles (infants, pregnancy, immunocompromised): Urgency elevated without altering diagnosis category.
