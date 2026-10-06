# DermaSense Dataset and Data Splitting Governance

## 1. Ethical Data Governance
DermaSense strictly adheres to open-science data governance:
- Only public dermatology datasets with permissive or research-compliant licensing are used.
- **No synthetic images** are ever mixed into training or evaluation sets.
- No faked or fabricated clinical training datasets are reported.

---

## 2. Public Dermatology Reference Datasets
Below are the public reference datasets evaluated and supported by the `model/dataset.py` pipeline:

### 1. SD-198 (Skin Disease 198)
- **Source**: Sun et al., Chinese Academy of Sciences
- **URL**: https://www.cs.rochester.edu/u/jlu/data/SD-198.html
- **License**: Academic research use only
- **Image Count**: 6,584 clinical images across 198 skin condition categories
- **Labels Selected**: Superficial fungal infections (Tinea corporis, Tinea pedis, Tinea cruris) vs other inflammatory dermatoses (Eczema, Psoriasis, Contact Dermatitis)
- **Limitations**: Acquired under varying clinical lighting; majority Asian skin phototypes (Fitzpatrick III–IV); variable resolution.
- **Skin-Tone Representation**: Predominantly Fitzpatrick types III and IV. Very low representation of dark phototypes (V and VI).
- **Body-Site Representation**: Trunk, extremities, hands, feet, face.

### 2. DermNet (Dermatology Atlas)
- **Source**: DermNet NZ (New Zealand Dermatological Society)
- **URL**: https://dermnetnz.org/
- **License**: Educational and research access under fair use / license agreement
- **Image Count**: ~23,000 dermatological images
- **Labels Selected**: Fungal infections vs Differential inflammatory dermatoses
- **Limitations**: Retrospective clinical collection; non-standardized digital capture devices.
- **Skin-Tone Representation**: Skewed towards light phototypes (Fitzpatrick I–II).
- **Body-Site Representation**: All anatomical regions.

### 3. Fitzpatrick 17k
- **Source**: Groh et al., MIT Media Lab
- **URL**: https://github.com/mattgroh/fitzpatrick17k
- **License**: CC-BY-NC 4.0
- **Image Count**: 16,577 clinical photographs annotated with Fitzpatrick skin types I through VI
- **Labels Selected**: Fungal / infectious vs non-neoplastic inflammatory conditions
- **Limitations**: Sourced from web dermatology atlases; noisy labels requiring curation.
- **Skin-Tone Representation**: Annotated across all 6 Fitzpatrick phototypes; enabling formal fairness and subgroup auditing.
- **Body-Site Representation**: Full body coverage.

---

## 3. Data Splitting and Deduplication Protocol (`model/dataset.py`)
To prevent data contamination and overly optimistic validation metrics, the following safeguards are strictly enforced:

1. **Perceptual Hashing (dHash)**:
   - Images are compared using difference hashing (`dHash`) with an 8x8 gradient matrix.
   - Any pair with a Hamming distance $\le 3$ is flagged as a near-duplicate and excluded prior to splitting.
2. **Patient/Source-Level Splitting**:
   - Splitting is performed strictly at the **patient** or **source** level (`split_by_patient_or_source`).
   - All images from a single patient are assigned entirely to one split. Random image-level shuffling is strictly prohibited.
3. **Partition Ratios & Seeding**:
   - Training: 70%
   - Validation: 15% (used for hyperparameter tuning and temperature scaling)
   - Final Test: 15% (held out and evaluated **only once**)
   - Seed: Fixed (`seed = 42`) for full reproducibility.
