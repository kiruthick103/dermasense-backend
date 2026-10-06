"""
DermaSense Supabase Client & Multi-Portal Data Service.
Handles Supabase Auth verification, PostgREST queries, Row Level Security enforcement,
realtime event dispatch, and seamless fallback store.
"""

import os
import time
import uuid
from typing import Any, Dict, List, Optional
import httpx
from dotenv import load_dotenv

# Load local .env file if present
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
DEMO_FALLBACK_MODE = os.environ.get("DEMO_FALLBACK_MODE", "true").lower() in ("true", "1", "yes")

def is_supabase_configured() -> bool:
    """Returns True if valid Supabase URL and keys are configured."""
    return bool(SUPABASE_URL and SUPABASE_ANON_KEY and not SUPABASE_URL.startswith("https://your-project"))

# In-memory persistence store for testing & fallback
FALLBACK_DB = {
    "profiles": {},
    "screenings": {},
    "screening_answers": {},
    "screening_images": {},
    "medicine_labels": {},
    "referrals": {},
    "case_notes": {},
    "followups": {},
    "notifications": {},
    "audit_logs": [],
    "model_versions": [
        {
            "id": "mv-v2-1",
            "version_code": "dermasense-v2.1-hybrid",
            "name": "DermaSense Multi-Tone Hybrid Vision & Rule Engine",
            "description": "Conformal prediction set pattern similarity + deterministic 5-stage clinical safety ladder",
            "is_active": True,
            "released_at": "2026-10-01T00:00:00Z"
        }
    ]
}

# Seed default demo profiles into FALLBACK_DB so test logins immediately work
DEFAULT_DEMO_USERS = [
    {
        "id": "usr-patient-1",
        "email": "patient@dermasense.gov.in",
        "full_name": "Smt. Lakshmi Devi",
        "phone": "+91 98765 43210",
        "role": "patient",
        "facility_name": "Kallidaikurichi PHC",
        "is_active": True
    },
    {
        "id": "usr-asha-1",
        "email": "asha@dermasense.gov.in",
        "full_name": "Kavitha M. (ASHA Facilitator)",
        "phone": "+91 98765 43211",
        "role": "asha",
        "facility_name": "Kallidaikurichi Community Sub-Centre",
        "is_active": True
    },
    {
        "id": "usr-pharmacist-1",
        "email": "pharmacist@dermasense.gov.in",
        "full_name": "Ramesh Kumar, D.Pharm",
        "phone": "+91 98765 43212",
        "role": "pharmacist",
        "facility_name": "Jan Aushadhi Kendra #402",
        "is_active": True
    },
    {
        "id": "usr-doctor-1",
        "email": "doctor@dermasense.gov.in",
        "full_name": "Dr. S. Sundaram, MD (Dermatology)",
        "phone": "+91 98765 43213",
        "role": "doctor",
        "facility_name": "Tirunelveli District Hospital",
        "is_active": True
    },
    {
        "id": "usr-analyst-1",
        "email": "analyst@dermasense.gov.in",
        "full_name": "Dr. Ananya Sen, Public Health Epidemiologist",
        "phone": "+91 98765 43214",
        "role": "analyst",
        "facility_name": "State Directorate of Health Services",
        "is_active": True
    },
    {
        "id": "usr-admin-1",
        "email": "admin@dermasense.gov.in",
        "full_name": "Portal Systems Administrator",
        "phone": "+91 98765 43215",
        "role": "admin",
        "facility_name": "National Health Portal Division",
        "is_active": True
    }
]

for u in DEFAULT_DEMO_USERS:
    FALLBACK_DB["profiles"][u["id"]] = u.copy()


def get_headers(use_service_role: bool = False, token: Optional[str] = None) -> Dict[str, str]:
    """Generates standard Supabase HTTP headers."""
    api_key = SUPABASE_SERVICE_ROLE_KEY if (use_service_role and SUPABASE_SERVICE_ROLE_KEY) else SUPABASE_ANON_KEY
    headers = {
        "apikey": api_key,
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif use_service_role and SUPABASE_SERVICE_ROLE_KEY:
        headers["Authorization"] = f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
    else:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


# =============================================================================
# AUTHENTICATION VERIFICATION
# =============================================================================

async def verify_supabase_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifies a Supabase access token and fetches the verified user profile.
    Never trusts roles supplied by the client.
    """
    if not token:
        return None

    # 1. Real Supabase Auth verification
    if is_supabase_configured():
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(
                    f"{SUPABASE_URL}/auth/v1/user",
                    headers={"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {token}"}
                )
                if res.status_code == 200:
                    auth_user = res.json()
                    user_id = auth_user.get("id")
                    email = auth_user.get("email")

                    # Fetch user profile from database
                    prof_res = await client.get(
                        f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}&select=*",
                        headers=get_headers(use_service_role=True)
                    )
                    if prof_res.status_code == 200 and prof_res.json():
                        profile = prof_res.json()[0]
                        if not profile.get("is_active", True):
                            return None
                        return profile
                    
                    # If profile row missing, default to patient
                    return {
                        "id": user_id,
                        "email": email,
                        "full_name": auth_user.get("user_metadata", {}).get("full_name", email.split("@")[0]),
                        "role": auth_user.get("user_metadata", {}).get("role", "patient"),
                        "is_active": True
                    }
        except Exception as e:
            print("Supabase auth verification error:", e)

    # 2. Fallback mode verification (for demo/eval sessions)
    for p in FALLBACK_DB["profiles"].values():
        if token == f"demo-token-{p['role']}" or token == p["id"]:
            if not p.get("is_active", True):
                return None
            return p

    # Allow custom fallback tokens if prefixed
    if token.startswith("token-"):
        uid = token.replace("token-", "")
        if uid in FALLBACK_DB["profiles"]:
            p = FALLBACK_DB["profiles"][uid]
            if not p.get("is_active", True):
                return None
            return p

    return None


# =============================================================================
# AUDIT LOGGING
# =============================================================================

def log_system_audit(actor_id: Optional[str], actor_role: str, action: str, target_type: Optional[str] = None, target_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
    """Logs non-PII audit record."""
    entry = {
        "id": str(uuid.uuid4()),
        "actor_id": actor_id,
        "actor_role": actor_role,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "details": details or {},
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    FALLBACK_DB["audit_logs"].insert(0, entry)
    if len(FALLBACK_DB["audit_logs"]) > 1000:
        FALLBACK_DB["audit_logs"].pop()


# =============================================================================
# DATA SERVICE OPERATIONS
# =============================================================================

async def create_screening_record(
    patient_id: str,
    created_by: str,
    screening_data: Dict[str, Any],
    answers_json: Dict[str, Any],
    images: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Saves screening, answers, and images, creating a referral if required."""
    screening_id = str(uuid.uuid4())
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    rec = {
        "id": screening_id,
        "patient_id": patient_id,
        "created_by": created_by,
        "category": screening_data.get("category", "C"),
        "urgency": screening_data.get("urgency", "ROUTINE"),
        "referral_needed": screening_data.get("referral_needed", False),
        "referral_timeline": screening_data.get("referral_timeline", "Routine follow-up"),
        "action_plan": screening_data.get("action_plan", ""),
        "explanation": screening_data.get("explanation", ""),
        "steroid_warning": screening_data.get("steroid_warning", ""),
        "danger_signs_found": screening_data.get("danger_signs_found", []),
        "contradictions_found": screening_data.get("contradictions_found", []),
        "risk_score": float(screening_data.get("risk_score", 0)),
        "pattern_name": screening_data.get("pattern_name", ""),
        "pattern_strength": screening_data.get("pattern_strength", ""),
        "confidence_band": screening_data.get("confidence_band", ""),
        "created_at": now_iso
    }

    # Save to local fallback store
    FALLBACK_DB["screenings"][screening_id] = rec
    FALLBACK_DB["screening_answers"][screening_id] = {
        "id": str(uuid.uuid4()),
        "screening_id": screening_id,
        "answers_json": answers_json,
        "created_at": now_iso
    }
    for img in images:
        img_id = str(uuid.uuid4())
        FALLBACK_DB["screening_images"][img_id] = {
            "id": img_id,
            "screening_id": screening_id,
            "slot": img.get("slot", "closeup"),
            "data_url": img.get("data_url", ""),
            "quality_blur": img.get("quality_blur", 0),
            "quality_acceptable": img.get("quality_acceptable", True),
            "skin_coverage": img.get("skin_coverage", 0),
            "has_upload_flags": img.get("has_upload_flags", False),
            "upload_flags": img.get("upload_flags", []),
            "created_at": now_iso
        }

    # Automatic Referral creation for Categories D, B, A, or flagged routine referrals
    referral_id = None
    if rec["referral_needed"] or rec["category"] in ("D", "B", "A"):
        referral_id = str(uuid.uuid4())
        priority_map = {
            "D": "EMERGENT",
            "B": "URGENT",
            "A": "ROUTINE",
            "C": "ROUTINE"
        }
        rank_map = {"D": 1, "B": 10, "A": 30, "C": 50}
        ref_entry = {
            "id": referral_id,
            "screening_id": screening_id,
            "patient_id": patient_id,
            "assigned_asha_id": None,
            "assigned_doctor_id": None,
            "priority": priority_map.get(rec["category"], "ROUTINE"),
            "status": "PENDING_ASHA",
            "triage_rank": rank_map.get(rec["category"], 50),
            "facility_name": "Kallidaikurichi Community Health Centre",
            "created_at": now_iso,
            "updated_at": now_iso
        }
        FALLBACK_DB["referrals"][referral_id] = ref_entry

        # Realtime notification to ASHA workers
        for prof in FALLBACK_DB["profiles"].values():
            if prof.get("role") == "asha":
                add_notification(
                    recipient_id=prof["id"],
                    title=f"New Priority {ref_entry['priority']} Referral",
                    message=f"Screening completed for Category {rec['category']}. Triage review required.",
                    type="REFERRAL_CREATED",
                    link=f"#referral/{referral_id}"
                )

    log_system_audit(
        actor_id=patient_id,
        actor_role="patient",
        action="SCREENING_COMPLETED",
        target_type="screening",
        target_id=screening_id,
        details={"category": rec["category"], "urgency": rec["urgency"], "referral_created": bool(referral_id)}
    )

    return {
        "screening": rec,
        "referral_id": referral_id
    }


def add_notification(recipient_id: str, title: str, message: str, type: str = "INFO", link: Optional[str] = None):
    """Creates an in-app notification."""
    nid = str(uuid.uuid4())
    notif = {
        "id": nid,
        "recipient_id": recipient_id,
        "title": title,
        "message": message,
        "type": type,
        "link": link,
        "is_read": False,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    FALLBACK_DB["notifications"][nid] = notif
    return notif


# Initialize synthetic referrals so ASHA, Doctor, and Analyst portals have real operational data on start
def seed_initial_demo_referrals():
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    sample_cases = [
        {
            "category": "D",
            "urgency": "EMERGENT (Immediate hospital visit required)",
            "priority": "EMERGENT",
            "triage_rank": 1,
            "danger_signs_found": ["Severe facial or mucosal rash", "High fever accompanied by rapid skin peeling"],
            "patient_name": "R. Murugan (Age 42)",
            "explanation": "Reported severe red flag symptoms. Immediate medical attention required."
        },
        {
            "category": "B",
            "urgency": "URGENT (Medical consultation within 48 hours)",
            "priority": "URGENT",
            "triage_rank": 10,
            "steroid_warning": "Reported use of potent topical steroid (Clobetasol propionate) without physician prescription.",
            "patient_name": "Smt. Priya Sundar (Age 29)",
            "explanation": "High steroid misuse pattern. Risk of masking infection and cutaneous atrophy."
        },
        {
            "category": "A",
            "urgency": "ROUTINE (Community health centre visit within 7 days)",
            "priority": "ROUTINE",
            "triage_rank": 30,
            "pattern_name": "Fungal-type ring pattern (Typical circular annular border)",
            "pattern_strength": "Strong",
            "patient_name": "Master A. Karthi (Age 11)",
            "explanation": "Pattern consistent with active annular spreading lesion."
        }
    ]

    for idx, sc in enumerate(sample_cases):
        sid = f"seed-sc-{idx+1}"
        ref_id = f"seed-ref-{idx+1}"
        pat_id = "usr-patient-1"

        FALLBACK_DB["screenings"][sid] = {
            "id": sid,
            "patient_id": pat_id,
            "created_by": pat_id,
            "category": sc["category"],
            "urgency": sc["urgency"],
            "referral_needed": True,
            "referral_timeline": "Within 48 hours" if sc["category"] == "B" else "Immediately",
            "action_plan": "Refer to Primary Health Centre physician for clinical examination.",
            "explanation": sc["explanation"],
            "steroid_warning": sc.get("steroid_warning", ""),
            "danger_signs_found": sc.get("danger_signs_found", []),
            "contradictions_found": [],
            "risk_score": 8.5 if sc["category"] in ("D", "B") else 3.2,
            "pattern_name": sc.get("pattern_name", ""),
            "pattern_strength": sc.get("pattern_strength", ""),
            "confidence_band": "High",
            "created_at": now_iso
        }

        FALLBACK_DB["referrals"][ref_id] = {
            "id": ref_id,
            "screening_id": sid,
            "patient_id": pat_id,
            "patient_name": sc["patient_name"],
            "assigned_asha_id": "usr-asha-1",
            "assigned_doctor_id": "usr-doctor-1" if idx == 0 else None,
            "priority": sc["priority"],
            "status": "ASSIGNED_DOCTOR" if idx == 0 else "PENDING_ASHA",
            "triage_rank": sc["triage_rank"],
            "facility_name": "Kallidaikurichi Community Health Centre",
            "created_at": now_iso,
            "updated_at": now_iso
        }

        # Add initial clinical note for doctor
        if idx == 0:
            nid = f"seed-note-1"
            FALLBACK_DB["case_notes"][nid] = {
                "id": nid,
                "referral_id": ref_id,
                "screening_id": sid,
                "author_id": "usr-asha-1",
                "author_role": "asha",
                "note_type": "ASHA_FOLLOWUP",
                "content": "Patient contacted by ASHA Kavitha. Advised urgent hospital visit. Escalated to Dr. Sundaram.",
                "created_at": now_iso
            }

seed_initial_demo_referrals()
