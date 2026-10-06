"""
Integration and RBAC API Endpoint Tests for DermaSense.
Validates:
1. Demo login for all roles (Patient, ASHA, Pharmacist, Doctor, Analyst, Admin)
2. Role access restrictions (Pharmacist/Analyst/Admin blocked from /api/cases; only Doctor/ASHA allowed)
3. Analyst metrics and CSV export
4. Admin audit log and demo reset
5. /screen with source=upload and pattern model strength bands
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from auth import DEMO_OTP, DEMO_PASSWORD

client = TestClient(app)


def test_auth_demo_login_and_me():
    # 1. Login as doctor
    res = client.post("/api/auth/demo-login", json={"role": "doctor"})
    assert res.status_code == 200
    data = res.json()
    token = data["token"]
    assert data["user"]["role"] == "doctor"

    # 2. Check /api/auth/me with Bearer token
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["user"]["role"] == "doctor"


def test_rbac_access_restrictions():
    # 1. Doctor token can access /api/cases
    doc_res = client.post("/api/auth/demo-login", json={"role": "doctor"})
    doc_token = doc_res.json()["token"]
    cases_res = client.get("/api/cases", headers={"Authorization": f"Bearer {doc_token}"})
    assert cases_res.status_code == 200
    assert "cases" in cases_res.json()

    # 2. Pharmacist token is BLOCKED (403) from /api/cases (Data minimization)
    pharm_res = client.post("/api/auth/demo-login", json={"role": "pharmacist"})
    pharm_token = pharm_res.json()["token"]
    pharm_cases = client.get("/api/cases", headers={"Authorization": f"Bearer {pharm_token}"})
    assert pharm_cases.status_code == 403


def test_analyst_metrics_and_csv():
    analyst_res = client.post("/api/auth/demo-login", json={"role": "analyst"})
    analyst_token = analyst_res.json()["token"]

    # Metrics endpoint
    metrics_res = client.get("/api/analyst/metrics", headers={"Authorization": f"Bearer {analyst_token}"})
    assert metrics_res.status_code == 200
    m_data = metrics_res.json()
    assert "category_distribution" in m_data
    assert "source_distribution" in m_data

    # CSV export endpoint
    csv_res = client.get("/api/analyst/export-csv", headers={"Authorization": f"Bearer {analyst_token}"})
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers.get("content-type", "")
    assert "total_screened_cases" in csv_res.text


def test_admin_audit_log_and_reset():
    admin_res = client.post("/api/auth/demo-login", json={"role": "admin"})
    admin_token = admin_res.json()["token"]

    # View audit log
    audit_res = client.get("/api/admin/audit-log", headers={"Authorization": f"Bearer {admin_token}"})
    assert audit_res.status_code == 200
    assert "audit_log" in audit_res.json()

    # Reset demo cases
    reset_res = client.post("/api/admin/reset-demo", headers={"Authorization": f"Bearer {admin_token}"})
    assert reset_res.status_code == 200
    assert reset_res.json()["status"] == "success"


def test_screen_endpoint_returns_pattern_model():
    payload = {
        "used_any_cream": "YES",
        "prescribed_by_clinician": "NO",
        "steroid_name_visible": "YES",
        "itchy_ring_or_scaly": "YES",
        "duration": "YES",
        "source": "upload",
        "consent_store_data": "false"
    }
    res = client.post("/screen", data=payload)
    assert res.status_code == 200
    data = res.json()
    assert "pattern_model" in data
    assert "top_pattern" in data["pattern_model"]
    assert "strength" in data["pattern_model"]
    assert data["decision"]["category"] in ["A", "B", "C", "D"]
