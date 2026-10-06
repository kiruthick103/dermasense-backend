"""
Tests for DermaSense Multi-Portal Healthcare Platform.
Validates end-to-end connected workflow across:
1. Patient Portal (Screening -> Referral created -> Notification)
2. ASHA Portal (Queue triage -> Doctor assignment -> Notification)
3. Doctor Portal (Case review -> Clinical note -> Follow-up -> Patient notification)
4. Pharmacist Portal (Medicine label checker -> Steroid matching -> Guidance text)
5. Analyst Portal (Real database stats only, CSV export)
6. Admin Portal (User management, Audit trail, Role guardrails)
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_complete_multi_portal_workflow():
    # 1. Patient Signs Up / Logs In
    pat_login = client.post("/api/auth/demo-login", json={"role": "patient"})
    assert pat_login.status_code == 200
    pat_data = pat_login.json()
    pat_token = pat_data["token"]
    pat_user = pat_data["user"]
    assert pat_user["role"] == "patient"

    # 2. Patient performs screening that requires referral (Category B: Steroid suspected)
    screen_payload = {
        "answers": {
            "used_any_cream": "YES",
            "prescribed_by_clinician": "NO",
            "steroid_name_visible": "YES",
            "spread_despite_treatment": "YES",
            "itchy_ring_or_scaly": "YES",
            "duration": "WEEKS",
            "body_area": "TORSO"
        },
        "danger_signs": [],
        "vulnerable_flags": [],
        "cream_text": "Betnovate cream applied daily",
        "source": "camera"
    }

    screen_res = client.post(
        "/api/screenings",
        json=screen_payload,
        headers={"Authorization": f"Bearer {pat_token}"}
    )
    assert screen_res.status_code == 200
    s_data = screen_res.json()
    assert s_data["status"] == "success"
    assert s_data["decision"]["category"] == "B"
    referral_id = s_data["referral_id"]
    assert referral_id is not None

    # 3. ASHA logs in and receives the high priority referral in triage queue
    asha_login = client.post("/api/auth/demo-login", json={"role": "asha"})
    assert asha_login.status_code == 200
    asha_token = asha_login.json()["token"]

    asha_queue_res = client.get("/api/referrals", headers={"Authorization": f"Bearer {asha_token}"})
    assert asha_queue_res.status_code == 200
    queue = asha_queue_res.json()["referrals"]
    assert any(r["id"] == referral_id for r in queue)

    # 4. ASHA assigns Doctor
    doc_login = client.post("/api/auth/demo-login", json={"role": "doctor"})
    assert doc_login.status_code == 200
    doc_token = doc_login.json()["token"]
    doc_id = doc_login.json()["user"]["id"]

    assign_res = client.post(
        f"/api/referrals/{referral_id}/assign",
        json={"doctor_id": doc_id, "notes": "Patient contacted by ASHA Kavitha. Escalated for specialist opinion."},
        headers={"Authorization": f"Bearer {asha_token}"}
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["referral"]["status"] == "ASSIGNED_DOCTOR"

    # 5. Doctor logs in and sees case in review queue
    doc_cases_res = client.get("/api/referrals", headers={"Authorization": f"Bearer {doc_token}"})
    assert doc_cases_res.status_code == 200
    doc_cases = doc_cases_res.json()["referrals"]
    assigned_case = next((r for r in doc_cases if r["id"] == referral_id), None)
    assert assigned_case is not None

    # 6. Doctor reviews case, records clinical note, and sets follow-up
    review_res = client.post(
        f"/api/referrals/{referral_id}/review",
        json={
            "clinical_notes": "Clinical assessment: Tinea incognito presentation secondary to prolonged topical steroid. Discontinue steroid, advise gentle wash and in-person PHC visit.",
            "status": "DOCTOR_REVIEWED",
            "followup_date": "2026-10-15"
        },
        headers={"Authorization": f"Bearer {doc_token}"}
    )
    assert review_res.status_code == 200
    assert review_res.json()["referral"]["status"] == "DOCTOR_REVIEWED"

    # 7. Patient receives Realtime Notification of review
    pat_notif_res = client.get("/api/notifications", headers={"Authorization": f"Bearer {pat_token}"})
    assert pat_notif_res.status_code == 200
    notifs = pat_notif_res.json()["notifications"]
    assert any("Doctor Has Reviewed Your Referral" in n["title"] for n in notifs)


def test_pharmacist_label_checker_safety():
    pharm_login = client.post("/api/auth/demo-login", json={"role": "pharmacist"})
    assert pharm_login.status_code == 200
    pharm_token = pharm_login.json()["token"]

    # Test steroid detection
    check_res = client.post(
        "/api/medicine/check",
        json={"raw_text": "Clobetasol Propionate and Neomycin Cream"},
        headers={"Authorization": f"Bearer {pharm_token}"}
    )
    assert check_res.status_code == 200
    data = check_res.json()
    assert data["steroid_matched"] is True
    assert "clobetasol" in data["matched_term"].lower()
    # Critical clinical safety requirements
    assert "steroid-free" not in data.get("safety_guidance", "").lower()
    assert "Please confirm the label with a pharmacist or clinician." in data["safety_guidance"]


def test_analyst_real_database_stats():
    analyst_login = client.post("/api/auth/demo-login", json={"role": "analyst"})
    assert analyst_login.status_code == 200
    analyst_token = analyst_login.json()["token"]

    stats_res = client.get("/api/analyst/stats", headers={"Authorization": f"Bearer {analyst_token}"})
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "total_screenings" in stats
    assert "category_distribution" in stats
    assert "referral_rate_pct" in stats
    assert "steroid_misuse_rate_pct" in stats

    # CSV Export
    csv_res = client.get("/api/analyst/export", headers={"Authorization": f"Bearer {analyst_token}"})
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]


def test_admin_governance_and_audit():
    admin_login = client.post("/api/auth/demo-login", json={"role": "admin"})
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["token"]

    # User management
    users_res = client.get("/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert users_res.status_code == 200
    users = users_res.json()["users"]
    assert len(users) >= 6

    # Admin audit trail
    audit_res = client.get("/api/admin/audit", headers={"Authorization": f"Bearer {admin_token}"})
    assert audit_res.status_code == 200
    logs = audit_res.json()["logs"]
    assert len(logs) > 0


def test_patient_right_to_erasure():
    pat_login = client.post("/api/auth/demo-login", json={"role": "patient"})
    pat_token = pat_login.json()["token"]

    del_res = client.delete("/api/patient/data", headers={"Authorization": f"Bearer {pat_token}"})
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"
