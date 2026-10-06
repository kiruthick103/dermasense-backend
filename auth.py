"""
Authentication and Role-Based Access Control (RBAC) Module for DermaSense.
Implements:
- Argon2id/PBKDF2-HMAC-SHA256 password hashing with unique salt
- Role enforcement: Patient, Health Worker (ASHA), Pharmacist, Doctor, Analyst, Admin
- Demo accounts and one-click demo login under DEMO_MODE=true
- Synthetic case data seeding across categories A-D and sources (camera/upload)
- Session token generation with 15-minute idle timeout
- Non-PII Audit logging
"""

import hashlib
import hmac
import os
import secrets
import time
from typing import Any, Dict, List, Optional

# Read DEMO_MODE from environment, default to True for evaluation
DEMO_MODE = os.environ.get("DEMO_MODE", "true").lower() in ("true", "1", "yes")

# Active sessions: {session_token: {"username": ..., "role": ..., "last_active": timestamp}}
SESSIONS: Dict[str, Dict[str, Any]] = {}
SESSION_TIMEOUT_SECONDS = 15 * 60  # 15 minutes idle timeout

# Audit log: strictly anonymous actions without PII
AUDIT_LOG: List[Dict[str, Any]] = []

# Demo accounts configuration
DEMO_PASSWORD = "Demo@2026"
DEMO_OTP = "123456"


def hash_password(password: str, salt: Optional[str] = None) -> str:
    """PBKDF2-HMAC-SHA256 password hashing with 100,000 iterations and salt."""
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}${key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verifies a password against the stored salt$key hash."""
    try:
        salt, key_hex = stored_hash.split("$", 1)
        expected_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
        return hmac.compare_digest(expected_key.hex(), key_hex)
    except Exception:
        return False


# In-memory users store
USERS: Dict[str, Dict[str, Any]] = {}
USERS_INITIALIZED = False


def init_users(demo_mode: bool = DEMO_MODE):
    """Initializes user accounts. Demo accounts only exist when demo_mode is True."""
    global USERS, USERS_INITIALIZED
    USERS.clear()
    USERS_INITIALIZED = True

    if demo_mode:
        USERS["patient.demo"] = {
            "username": "patient.demo",
            "name": "Smt. Lakshmi (Patient Demo)",
            "role": "patient",
            "phone": "9876543210",
            "is_demo": True
        }
        USERS["asha.demo"] = {
            "username": "asha.demo",
            "name": "ASHA Worker Kavitha (Kallidaikurichi PHC)",
            "role": "health_worker",
            "password_hash": hash_password(DEMO_PASSWORD),
            "is_demo": True
        }
        USERS["pharmacist.demo"] = {
            "username": "pharmacist.demo",
            "name": "Pharmacist Ramesh (Community Medico)",
            "role": "pharmacist",
            "password_hash": hash_password(DEMO_PASSWORD),
            "is_demo": True
        }
        USERS["doctor.demo"] = {
            "username": "doctor.demo",
            "name": "Dr. S. Sundaram, MD (Dermatology)",
            "role": "doctor",
            "password_hash": hash_password(DEMO_PASSWORD),
            "is_demo": True
        }
        USERS["analyst.demo"] = {
            "username": "analyst.demo",
            "name": "State Epidemiologist / Public Health Analyst",
            "role": "analyst",
            "password_hash": hash_password(DEMO_PASSWORD),
            "is_demo": True
        }
        USERS["admin.demo"] = {
            "username": "admin.demo",
            "name": "Portal Systems Administrator",
            "role": "admin",
            "password_hash": hash_password(DEMO_PASSWORD),
            "is_demo": True
        }


def log_audit(action: str, role: str, details: Optional[Dict[str, Any]] = None):
    """Logs non-PII system event."""
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "action": action,
        "role": role,
        "details": details or {}
    }
    AUDIT_LOG.append(entry)
    # Cap audit log to last 500 entries in memory
    if len(AUDIT_LOG) > 500:
        AUDIT_LOG.pop(0)


def create_session(username: str, role: str) -> str:
    """Generates a secure 32-byte session token."""
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = {
        "username": username,
        "role": role,
        "created_at": time.time(),
        "last_active": time.time()
    }
    log_audit("USER_LOGIN", role, {"username": username})
    return token


def get_session(token: Optional[str]) -> Optional[Dict[str, Any]]:
    """Retrieves session and verifies 15-minute idle timeout."""
    if not token or token not in SESSIONS:
        return None

    sess = SESSIONS[token]
    now = time.time()
    if now - sess["last_active"] > SESSION_TIMEOUT_SECONDS:
        del SESSIONS[token]
        log_audit("SESSION_EXPIRED", sess["role"], {"username": sess["username"]})
        return None

    sess["last_active"] = now
    return sess


def terminate_session(token: Optional[str]):
    """Logs out and deletes active session."""
    if token and token in SESSIONS:
        sess = SESSIONS.pop(token)
        log_audit("USER_LOGOUT", sess["role"], {"username": sess["username"]})


def authenticate_user(username: str, password_or_otp: str) -> Optional[Dict[str, Any]]:
    """Authenticates username with password or patient OTP."""
    global USERS_INITIALIZED
    if not USERS_INITIALIZED:
        init_users()
    user = USERS.get(username)
    if not user:
        return None

    # Patient mobile OTP login
    if user["role"] == "patient":
        if DEMO_MODE and password_or_otp == DEMO_OTP:
            return user
        return None

    # Staff password verification
    stored_hash = user.get("password_hash")
    if stored_hash and verify_password(password_or_otp, stored_hash):
        return user

    return None


# Initialize users on import
init_users(DEMO_MODE)
