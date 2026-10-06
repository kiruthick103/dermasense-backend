-- =============================================================================
-- DERMASENSE MULTI-PORTAL HEALTHCARE PLATFORM SCHEMA
-- Complies with Supabase Auth, Row Level Security (RLS), and Realtime Subscriptions
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. PROFILES TABLE (Linked directly to auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    full_name TEXT NOT NULL,
    phone TEXT,
    role VARCHAR(20) NOT NULL CHECK (role IN ('patient', 'asha', 'pharmacist', 'doctor', 'analyst', 'admin')),
    facility_name TEXT DEFAULT 'Primary Health Centre',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Index for fast role lookups
CREATE INDEX IF NOT EXISTS idx_profiles_role ON public.profiles(role);
CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email);

-- Helper function to fetch the authenticated user's role securely
CREATE OR REPLACE FUNCTION public.current_user_role()
RETURNS TEXT
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT role FROM public.profiles WHERE id = auth.uid() LIMIT 1;
$$;

-- 2. MODEL VERSIONS TABLE
CREATE TABLE IF NOT EXISTS public.model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_code VARCHAR(50) NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    released_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 3. SCREENINGS TABLE (Core screening records with deterministic triage result)
CREATE TABLE IF NOT EXISTS public.screenings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    created_by UUID REFERENCES public.profiles(id),
    category VARCHAR(5) NOT NULL CHECK (category IN ('A', 'B', 'C', 'D')),
    urgency VARCHAR(30) NOT NULL,
    referral_needed BOOLEAN NOT NULL DEFAULT FALSE,
    referral_timeline TEXT,
    action_plan TEXT,
    explanation TEXT,
    steroid_warning TEXT,
    danger_signs_found TEXT[] DEFAULT '{}',
    contradictions_found TEXT[] DEFAULT '{}',
    risk_score NUMERIC(5,2) DEFAULT 0,
    pattern_name TEXT,
    pattern_strength VARCHAR(30),
    confidence_band VARCHAR(30),
    model_version_id UUID REFERENCES public.model_versions(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_screenings_patient ON public.screenings(patient_id);
CREATE INDEX IF NOT EXISTS idx_screenings_category ON public.screenings(category);
CREATE INDEX IF NOT EXISTS idx_screenings_created_at ON public.screenings(created_at DESC);

-- 4. SCREENING ANSWERS TABLE (Normalized questionnaire responses)
CREATE TABLE IF NOT EXISTS public.screening_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    screening_id UUID NOT NULL REFERENCES public.screenings(id) ON DELETE CASCADE,
    answers_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_screening_answers_screening ON public.screening_answers(screening_id);

-- 5. SCREENING IMAGES TABLE (Close-up and optional wider views)
CREATE TABLE IF NOT EXISTS public.screening_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    screening_id UUID NOT NULL REFERENCES public.screenings(id) ON DELETE CASCADE,
    slot VARCHAR(20) NOT NULL CHECK (slot IN ('closeup', 'wider')),
    storage_path TEXT,
    data_url TEXT,
    source VARCHAR(20) DEFAULT 'camera',
    quality_blur NUMERIC(8,2),
    quality_acceptable BOOLEAN DEFAULT TRUE,
    skin_coverage NUMERIC(5,2),
    has_upload_flags BOOLEAN DEFAULT FALSE,
    upload_flags TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_screening_images_screening ON public.screening_images(screening_id);

-- 6. MEDICINE LABELS TABLE (OCR or typed label checks, steroid matching)
CREATE TABLE IF NOT EXISTS public.medicine_labels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    screening_id UUID REFERENCES public.screenings(id) ON DELETE SET NULL,
    checked_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    raw_text TEXT NOT NULL,
    steroid_matched BOOLEAN NOT NULL DEFAULT FALSE,
    matched_ingredients TEXT[] DEFAULT '{}',
    confidence_score NUMERIC(5,2) DEFAULT 0,
    safety_guidance TEXT NOT NULL DEFAULT 'Please confirm the label with a pharmacist or clinician.',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_medicine_labels_screening ON public.medicine_labels(screening_id);

-- 7. REFERRALS TABLE (Triage & coordination between Patient, ASHA & Doctor)
CREATE TABLE IF NOT EXISTS public.referrals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    screening_id UUID NOT NULL REFERENCES public.screenings(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    assigned_asha_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    assigned_doctor_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    priority VARCHAR(20) NOT NULL CHECK (priority IN ('EMERGENT', 'URGENT', 'ROUTINE', 'SELF_CARE')),
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING_ASHA' CHECK (status IN ('PENDING_ASHA', 'ASHA_REVIEWED', 'ASSIGNED_DOCTOR', 'DOCTOR_REVIEWED', 'COMPLETED', 'CLOSED')),
    triage_rank INT NOT NULL DEFAULT 100,
    facility_name TEXT DEFAULT 'Community Health Centre',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_referrals_patient ON public.referrals(patient_id);
CREATE INDEX IF NOT EXISTS idx_referrals_asha ON public.referrals(assigned_asha_id);
CREATE INDEX IF NOT EXISTS idx_referrals_doctor ON public.referrals(assigned_doctor_id);
CREATE INDEX IF NOT EXISTS idx_referrals_status ON public.referrals(status);
CREATE INDEX IF NOT EXISTS idx_referrals_priority ON public.referrals(priority);

-- 8. CASE NOTES TABLE (Clinical notes, ASHA follow-ups, Pharmacist remarks)
CREATE TABLE IF NOT EXISTS public.case_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referral_id UUID NOT NULL REFERENCES public.referrals(id) ON DELETE CASCADE,
    screening_id UUID REFERENCES public.screenings(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    author_role VARCHAR(20) NOT NULL,
    note_type VARCHAR(30) NOT NULL DEFAULT 'CLINICAL' CHECK (note_type IN ('CLINICAL', 'ASHA_FOLLOWUP', 'PHARMACIST_NOTE', 'ADMIN_NOTE')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_case_notes_referral ON public.case_notes(referral_id);

-- 9. FOLLOWUPS TABLE (Scheduled appointments, home visits, verification)
CREATE TABLE IF NOT EXISTS public.followups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referral_id UUID NOT NULL REFERENCES public.referrals(id) ON DELETE CASCADE,
    scheduled_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED' CHECK (status IN ('SCHEDULED', 'ATTENDED', 'MISSED', 'CANCELLED')),
    notes TEXT,
    recorded_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_followups_referral ON public.followups(referral_id);

-- 10. NOTIFICATIONS TABLE (Realtime in-app alerts for users)
CREATE TABLE IF NOT EXISTS public.notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipient_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(30) NOT NULL DEFAULT 'INFO',
    link TEXT,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_notifications_recipient ON public.notifications(recipient_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON public.notifications(is_read);

-- 11. AUDIT LOGS TABLE (Non-PII administrative system events)
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    actor_role VARCHAR(20) NOT NULL,
    action TEXT NOT NULL,
    target_type TEXT,
    target_id TEXT,
    details JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON public.audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_actor ON public.audit_logs(actor_id);

-- =============================================================================
-- AUTOMATIC PROFILE CREATION TRIGGER ON AUTH.SIGNUP
-- =============================================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    assigned_role TEXT;
    user_name TEXT;
    user_phone TEXT;
BEGIN
    -- Read role from raw_user_meta_data safely, default to 'patient'
    assigned_role := COALESCE(new.raw_user_meta_data->>'role', 'patient');
    IF assigned_role NOT IN ('patient', 'asha', 'pharmacist', 'doctor', 'analyst', 'admin') THEN
        assigned_role := 'patient';
    END IF;

    user_name := COALESCE(new.raw_user_meta_data->>'full_name', split_part(new.email, '@', 1));
    user_phone := new.raw_user_meta_data->>'phone';

    INSERT INTO public.profiles (id, email, full_name, phone, role, is_active)
    VALUES (new.id, new.email, user_name, user_phone, assigned_role, TRUE)
    ON CONFLICT (id) DO UPDATE SET
        full_name = EXCLUDED.full_name,
        phone = COALESCE(EXCLUDED.phone, profiles.phone),
        updated_at = now();

    RETURN NEW;
END;
$$;

-- Drop trigger if already exists then attach
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- =============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =============================================================================

-- Enable RLS across all tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.screenings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.screening_answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.screening_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.medicine_labels ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.referrals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.case_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.followups ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model_versions ENABLE ROW LEVEL SECURITY;

-- 1. PROFILES POLICIES
-- Users can view their own profile
CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

-- Staff (ASHA, Doctor, Admin) can view patient profiles
CREATE POLICY "Staff can view all profiles"
    ON public.profiles FOR SELECT
    USING (public.current_user_role() IN ('asha', 'doctor', 'admin', 'analyst'));

-- Users can update their own non-role fields
CREATE POLICY "Users can update own details"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id AND role = (SELECT role FROM public.profiles WHERE id = auth.uid()));

-- Only Admin can update roles or activate/deactivate users
CREATE POLICY "Admin can update any profile"
    ON public.profiles FOR UPDATE
    USING (public.current_user_role() = 'admin');

-- 2. SCREENINGS POLICIES
-- Patients can view and create their own screenings
CREATE POLICY "Patients can view own screenings"
    ON public.screenings FOR SELECT
    USING (auth.uid() = patient_id OR public.current_user_role() IN ('asha', 'doctor', 'admin', 'analyst'));

CREATE POLICY "Authenticated users can insert screenings"
    ON public.screenings FOR INSERT
    WITH CHECK (auth.uid() = patient_id OR public.current_user_role() IN ('asha', 'doctor', 'admin'));

-- Patients can delete their own screenings (Right to erasure)
CREATE POLICY "Patients can delete own screenings"
    ON public.screenings FOR DELETE
    USING (auth.uid() = patient_id OR public.current_user_role() = 'admin');

-- 3. SCREENING ANSWERS & IMAGES POLICIES
CREATE POLICY "Access screening answers via screening ownership"
    ON public.screening_answers FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.screenings s
            WHERE s.id = screening_answers.screening_id
            AND (s.patient_id = auth.uid() OR public.current_user_role() IN ('asha', 'doctor', 'admin', 'analyst'))
        )
    );

CREATE POLICY "Access screening images via screening ownership"
    ON public.screening_images FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.screenings s
            WHERE s.id = screening_images.screening_id
            AND (s.patient_id = auth.uid() OR public.current_user_role() IN ('asha', 'doctor', 'admin'))
        )
    );

-- 4. MEDICINE LABELS POLICIES
CREATE POLICY "Pharmacists and staff can access medicine labels"
    ON public.medicine_labels FOR ALL
    USING (
        checked_by = auth.uid() 
        OR public.current_user_role() IN ('pharmacist', 'doctor', 'admin', 'asha')
    );

-- 5. REFERRALS POLICIES
-- Patient sees own referrals; ASHA, Doctor, Admin see operational queue
CREATE POLICY "Referral access policy"
    ON public.referrals FOR SELECT
    USING (
        patient_id = auth.uid()
        OR assigned_asha_id = auth.uid()
        OR assigned_doctor_id = auth.uid()
        OR public.current_user_role() IN ('asha', 'doctor', 'admin')
    );

CREATE POLICY "Referral creation policy"
    ON public.referrals FOR INSERT
    WITH CHECK (
        patient_id = auth.uid()
        OR public.current_user_role() IN ('asha', 'doctor', 'admin')
    );

CREATE POLICY "Referral update policy"
    ON public.referrals FOR UPDATE
    USING (
        public.current_user_role() IN ('asha', 'doctor', 'admin')
    );

-- 6. CASE NOTES POLICIES
CREATE POLICY "Case notes view policy"
    ON public.case_notes FOR SELECT
    USING (
        public.current_user_role() IN ('asha', 'doctor', 'admin')
        OR EXISTS (
            SELECT 1 FROM public.referrals r
            WHERE r.id = case_notes.referral_id AND r.patient_id = auth.uid()
        )
    );

CREATE POLICY "Clinical staff can insert notes"
    ON public.case_notes FOR INSERT
    WITH CHECK (
        auth.uid() = author_id 
        AND public.current_user_role() IN ('asha', 'doctor', 'pharmacist', 'admin')
    );

-- 7. FOLLOWUPS POLICIES
CREATE POLICY "Followups access policy"
    ON public.followups FOR ALL
    USING (
        public.current_user_role() IN ('asha', 'doctor', 'admin')
        OR EXISTS (
            SELECT 1 FROM public.referrals r
            WHERE r.id = followups.referral_id AND r.patient_id = auth.uid()
        )
    );

-- 8. NOTIFICATIONS POLICIES
CREATE POLICY "Users read their own notifications"
    ON public.notifications FOR SELECT
    USING (auth.uid() = recipient_id);

CREATE POLICY "Users update their own notifications"
    ON public.notifications FOR UPDATE
    USING (auth.uid() = recipient_id);

CREATE POLICY "System or staff can insert notifications"
    ON public.notifications FOR INSERT
    WITH CHECK (TRUE);

-- 9. AUDIT LOGS & MODEL VERSIONS
CREATE POLICY "Admin views audit logs"
    ON public.audit_logs FOR SELECT
    USING (public.current_user_role() = 'admin');

CREATE POLICY "All authenticated users insert audit logs"
    ON public.audit_logs FOR INSERT
    WITH CHECK (TRUE);

CREATE POLICY "Model versions public read"
    ON public.model_versions FOR SELECT
    USING (TRUE);

CREATE POLICY "Admin manages model versions"
    ON public.model_versions FOR ALL
    USING (public.current_user_role() = 'admin');

-- =============================================================================
-- ENABLE SUPABASE REALTIME REPLICATION
-- =============================================================================
-- Adds tables to the realtime publication so Supabase Realtime streams updates
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'supabase_realtime') THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.referrals;
        ALTER PUBLICATION supabase_realtime ADD TABLE public.notifications;
        ALTER PUBLICATION supabase_realtime ADD TABLE public.case_notes;
        ALTER PUBLICATION supabase_realtime ADD TABLE public.screenings;
        ALTER PUBLICATION supabase_realtime ADD TABLE public.audit_logs;
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        NULL; -- Ignore if already added or limited permissions
END $$;

-- =============================================================================
-- SEED INITIAL ACTIVE MODEL VERSION
-- =============================================================================
INSERT INTO public.model_versions (version_code, name, description, is_active)
VALUES (
    'dermasense-v2.1-hybrid',
    'DermaSense Multi-Tone Hybrid Vision & Rule Engine',
    'Conformal prediction set pattern similarity + deterministic 5-stage clinical safety ladder',
    TRUE
)
ON CONFLICT (version_code) DO NOTHING;
