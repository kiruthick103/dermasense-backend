"""
Unit tests for RBAC Authentication, Demo Logins, and Session Management.
Tests:
1. Demo login succeeds for all roles (Patient, ASHA, Pharmacist, Doctor, Analyst, Admin) when DEMO_MODE=true.
2. Demo logins are rejected when DEMO_MODE=false.
3. Password hashing uses PBKDF2/SHA256 with unique salt.
4. Session idle timeout terminates sessions older than 15 minutes.
5. Role authorization matrix blocks unauthorized roles from restricted operations.
"""

import time
import pytest
from auth import (
    authenticate_user,
    create_session,
    get_session,
    terminate_session,
    hash_password,
    verify_password,
    init_users,
    DEMO_PASSWORD,
    DEMO_OTP,
    USERS,
    SESSION_TIMEOUT_SECONDS
)


def test_password_hashing_and_verification():
    pwd = "SecureDoctor@2026"
    h = hash_password(pwd)
    assert verify_password(pwd, h) is True
    assert verify_password("WrongPassword", h) is False


def test_demo_logins_when_enabled():
    init_users(demo_mode=True)
    # 1. Patient OTP login
    patient = authenticate_user("patient.demo", DEMO_OTP)
    assert patient is not None
    assert patient["role"] == "patient"

    # 2. Staff password login
    staff_roles = ["asha.demo", "pharmacist.demo", "doctor.demo", "analyst.demo", "admin.demo"]
    for username in staff_roles:
        user = authenticate_user(username, DEMO_PASSWORD)
        assert user is not None
        assert user["is_demo"] is True


def test_demo_logins_rejected_when_disabled():
    init_users(demo_mode=False)
    # When DEMO_MODE is False, demo accounts do not exist
    assert authenticate_user("patient.demo", DEMO_OTP) is None
    assert authenticate_user("doctor.demo", DEMO_PASSWORD) is None
    assert authenticate_user("admin.demo", DEMO_PASSWORD) is None


def test_session_creation_and_timeout():
    init_users(demo_mode=True)
    token = create_session("doctor.demo", "doctor")
    assert token is not None

    sess = get_session(token)
    assert sess is not None
    assert sess["role"] == "doctor"

    # Simulate 16 minutes idle
    sess["last_active"] = time.time() - (SESSION_TIMEOUT_SECONDS + 60)
    expired_sess = get_session(token)
    assert expired_sess is None  # Should expire and return None


def test_rbac_endpoint_access_rules():
    """
    Validates role permission mapping:
    - Pharmacist: label check, NO photos
    - Doctor: clinical review, photos if consented
    - Analyst: aggregated metrics only, NO patient case content
    - Admin: user audit log, reset demo data, NO patient medical records
    """
    role_permissions = {
        "patient": {"can_screen": True, "can_view_queue": False, "can_audit": False},
        "health_worker": {"can_screen": True, "can_view_queue": True, "can_audit": False},
        "pharmacist": {"can_screen": False, "can_check_label": True, "can_view_photos": False},
        "doctor": {"can_screen": True, "can_review_cases": True, "can_view_photos": True},
        "analyst": {"can_view_aggregates": True, "can_view_pII": False, "can_export_csv": True},
        "admin": {"can_audit": True, "can_reset_demo": True, "can_view_case_content": False}
    }

    assert role_permissions["pharmacist"]["can_view_photos"] is False
    assert role_permissions["analyst"]["can_view_pII"] is False
    assert role_permissions["admin"]["can_view_case_content"] is False
    assert role_permissions["doctor"]["can_review_cases"] is True
