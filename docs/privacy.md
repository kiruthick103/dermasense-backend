# DermaSense Privacy Policy & Data Minimization Charter

## 1. Core Privacy Philosophy
DermaSense operates under the Digital Personal Data Protection (DPDP) Act principles of **purpose limitation**, **data minimization**, and **storage limitation**.

Screening is completely accessible **without registering or logging into an account**.

---

## 2. Default Zero-Retention Architecture
- **In-Memory Processing:** When a citizen checks a rash, photographs, questionnaire inputs, and image analysis results exist exclusively in the volatile memory of their browser or execution container.
- **Opt-In Storage:**
  - *Save this case on this device:* Defaults to **OFF**. When enabled, records are saved only in the user's browser `localStorage`.
  - *Share with a health worker:* Defaults to **OFF**. When enabled, encrypted screening metrics are transmitted to the local Primary Health Centre (PHC) triage queue.
- If both consent toggles remain off, zero case data is retained upon navigating away from the page or closing the browser tab.

---

## 3. Metadata & Biometric Protection
- **No Face Recognition:** Rash segmentation targets only affected lesion boundaries; facial recognition is completely disabled.
- **Immediate EXIF & GPS Removal:** All geolocation coordinates, camera serial numbers, and device timestamps embedded in photo files are stripped immediately upon selection.
- **Aggregated Analytics & Cohort Masking:** Epidemiological analytics displayed to analysts automatically mask small cell sizes ($< 5$ cases) to prevent re-identification of patients in sparsely populated villages or wards.

---

## 4. Right to Erasure (Complete Data Deletion)
DermaSense provides instant, unconditional data deletion:
- **Client-Side:** The "Permanently Erase All My Stored Data" button in the Privacy view purges all cached cases, questionnaire responses, and session tokens from local device storage.
- **Server-Side:** Administrators and patients can trigger complete data purging via the `/history` DELETE API or administrative dashboard.
