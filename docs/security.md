# DermaSense Security Architecture & Threat Model

## 1. Authentication & Role-Based Access Control (RBAC)

DermaSense enforces strict server-side authorization on every administrative and clinical endpoint using session bearer tokens:

| Role | Permitted Access | Prohibited Endpoints / Actions | Data Access Boundaries |
| :--- | :--- | :--- | :--- |
| **Patient** | Start screening, view own past device checks, wipe own records | All staff dashboards, other patient records, analytics | Only unconsented or own consented cases |
| **Health Worker (ASHA)** | Consented triage queue for assigned PHC, triage status update, referral notes | Pharmacist label tool, raw system audit log, demo reset | Consented patient records only |
| **Pharmacist** | Cream label verification tool, corticosteroid advisory sheet | **Blocked from `/api/cases` (HTTP 403)** | **Never sees patient photos or records** |
| **Doctor** | Referred patient consultations, clinical assessment notes for feedback | Analyst CSV export, system user administration | Consented cases referred for clinical evaluation |
| **Analyst** | Aggregated epidemiology metrics, CSV export | Individual patient cases, photos, clinical notes | Aggregates only; cohorts $< 5$ suppressed |
| **Admin** | Security audit log, demo dataset reset | **Patient case content and photographs** | System logs only; no medical record access |

---

## 2. Password & Credential Security
- **Hashing:** Staff passwords stored using PBKDF2 with SHA-256 and unique per-user cryptographic salts (minimum 100,000 iterations).
- **Session Lifecycle:** Cryptographically random 256-bit URL-safe tokens (`secrets.token_urlsafe(32)`).
- **Idle Expiration:** Inactivity timeout enforced at 15 minutes (900 seconds). Expired tokens return `401 Unauthorized`.
- **Demo Mode Isolation:** Controlled by `DEMO_MODE=true`. Demo accounts (`patient.demo`, `asha.demo`, etc.) and the fixed OTP (`123456`) are completely rejected when `DEMO_MODE=false`.

---

## 3. Image Security & Sanitization
- **Metadata Stripping:** Client-side canvas normalization and backend OpenCV decoding automatically strip all EXIF tags, IPTC metadata, and GPS geolocations before image processing.
- **Upload Artifact Screening:**
  - Fast Fourier Transform (FFT) high-frequency analysis detects moire patterns and screen photography.
  - Blockiness estimation identifies heavily re-compressed lossy artifacts.
  - Low-resolution rejection blocks photos under 320x320 pixels.
- **Buffer Safety:** Uploaded files checked for magic number headers (`image/jpeg`, `image/png`, `image/webp`). Max file size capped at 15 MB with client-side downscaling.

---

## 4. Audit Logging & Non-Repudiation
- All authentication events, role logins, case reviews, CSV exports, and administrative actions generate structured audit entries in `AUDIT_LOG`.
- **Zero PII in Audit Logs:** Log entries contain only timestamps, event actions (e.g. `LOGIN`, `CASE_REVIEW`, `CSV_EXPORT`), authenticated roles, and non-sensitive identifiers. Patient names, mobile numbers, and clinical details are never recorded in audit files.

---

## 5. Security Headers & Network Controls
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy`: Restricts scripts, images, and styles to authorized origins.
- `Strict-Transport-Security` (HSTS) on production Vercel deployment.
