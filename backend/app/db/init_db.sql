-- ============================================================================
-- ARTS (Applicant Review & Team Selection System) MVP
-- Database Schema Definition (PostgreSQL / Supabase)
-- Reference: ARTS-DRS-006 Data & Database Requirements Specification
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- 1. USERS (E-01)
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    user_role VARCHAR(50) NOT NULL DEFAULT 'Reviewer' CHECK (user_role IN ('Administrator', 'Reviewer', 'Coordinator')),
    account_status VARCHAR(50) NOT NULL DEFAULT 'Active' CHECK (account_status IN ('Active', 'Inactive', 'Suspended')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 2. TEAMS (E-05)
-- ============================================================================
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_name VARCHAR(255) UNIQUE NOT NULL,
    team_description TEXT,
    team_status VARCHAR(50) NOT NULL DEFAULT 'Forming' CHECK (team_status IN ('Forming', 'Active', 'Closed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 3. SKILLS (E-07)
-- ============================================================================
CREATE TABLE IF NOT EXISTS skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_name VARCHAR(150) UNIQUE NOT NULL,
    skill_category VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 4. ROLES (E-04)
-- ============================================================================
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
    role_name VARCHAR(255) NOT NULL,
    role_description TEXT,
    number_of_openings INTEGER NOT NULL DEFAULT 1 CHECK (number_of_openings >= 0),
    role_status VARCHAR(50) NOT NULL DEFAULT 'Open' CHECK (role_status IN ('Open', 'Closed', 'Filled')),
    application_deadline TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 5. ROLE SKILLS (Many-to-Many: Roles <-> Skills)
-- ============================================================================
CREATE TABLE IF NOT EXISTS role_skills (
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, skill_id)
);

-- ============================================================================
-- 6. APPLICANTS (E-02)
-- ============================================================================
CREATE TABLE IF NOT EXISTS applicants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone_number VARCHAR(50),
    location VARCHAR(255),
    external_profile_link TEXT,
    applicant_status VARCHAR(50) NOT NULL DEFAULT 'Active' CHECK (applicant_status IN ('Active', 'Withdrawn', 'Archived')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 7. EXPERIENCES (E-09)
-- ============================================================================
CREATE TABLE IF NOT EXISTS experiences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    applicant_id UUID NOT NULL REFERENCES applicants(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    organization VARCHAR(255),
    start_date DATE NOT NULL,
    end_date DATE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_exp_dates CHECK (end_date IS NULL OR end_date >= start_date)
);

-- ============================================================================
-- 8. PORTFOLIO ITEMS (E-10)
-- ============================================================================
CREATE TABLE IF NOT EXISTS portfolio_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    applicant_id UUID NOT NULL REFERENCES applicants(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    reference_link TEXT,
    attachment_reference TEXT,
    date_added TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_portfolio_evidence CHECK (reference_link IS NOT NULL OR attachment_reference IS NOT NULL)
);

-- ============================================================================
-- 9. APPLICANT SKILLS (E-08)
-- ============================================================================
CREATE TABLE IF NOT EXISTS applicant_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    applicant_id UUID NOT NULL REFERENCES applicants(id) ON DELETE CASCADE,
    skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE RESTRICT,
    proficiency_level VARCHAR(50) CHECK (proficiency_level IN ('Beginner', 'Intermediate', 'Advanced', 'Expert')),
    years_of_experience NUMERIC(4, 1) CHECK (years_of_experience IS NULL OR years_of_experience >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_applicant_skill UNIQUE (applicant_id, skill_id)
);

-- ============================================================================
-- 10. APPLICATIONS (E-03)
-- ============================================================================
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    applicant_id UUID NOT NULL REFERENCES applicants(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    current_status VARCHAR(50) NOT NULL DEFAULT 'Received' CHECK (
        current_status IN (
            'Received',
            'Under Review',
            'Shortlisted',
            'Discussion / Interview',
            'Selected',
            'Not Selected',
            'Withdrawn'
        )
    ),
    motivation_statement TEXT,
    availability_info TEXT,
    submission_date TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_updated_date TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 11. TEAM MEMBERS (E-06)
-- ============================================================================
CREATE TABLE IF NOT EXISTS team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE RESTRICT,
    applicant_id UUID NOT NULL REFERENCES applicants(id) ON DELETE RESTRICT,
    source_application_id UUID NOT NULL REFERENCES applications(id) ON DELETE RESTRICT,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    join_date DATE NOT NULL DEFAULT CURRENT_DATE,
    membership_status VARCHAR(50) NOT NULL DEFAULT 'Active' CHECK (membership_status IN ('Active', 'Removed', 'Completed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_team_member UNIQUE (team_id, applicant_id)
);

-- ============================================================================
-- 12. EVALUATION CRITERIA (E-11)
-- ============================================================================
CREATE TABLE IF NOT EXISTS evaluation_criteria (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    criterion_name VARCHAR(255) UNIQUE NOT NULL,
    criterion_description TEXT,
    weight NUMERIC(5, 2),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 13. EVALUATIONS (E-12)
-- ============================================================================
CREATE TABLE IF NOT EXISTS evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    overall_recommendation VARCHAR(50) CHECK (overall_recommendation IN ('Advance', 'Reject', 'Waitlist', 'Needs Discussion')),
    overall_comments TEXT,
    strengths TEXT,
    concerns TEXT,
    evaluation_status VARCHAR(50) NOT NULL DEFAULT 'Draft' CHECK (evaluation_status IN ('Draft', 'Submitted')),
    submission_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_application_reviewer UNIQUE (application_id, reviewer_id)
);

-- ============================================================================
-- 14. EVALUATION SCORES (E-13)
-- ============================================================================
CREATE TABLE IF NOT EXISTS evaluation_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
    criterion_id UUID NOT NULL REFERENCES evaluation_criteria(id) ON DELETE RESTRICT,
    qualitative_rating VARCHAR(100),
    score_value NUMERIC(4, 2),
    score_comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_evaluation_criterion UNIQUE (evaluation_id, criterion_id)
);

-- ============================================================================
-- 15. NOTES (E-14)
-- ============================================================================
CREATE TABLE IF NOT EXISTS notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    author_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    related_entity_type VARCHAR(50) NOT NULL CHECK (related_entity_type IN ('Applicant', 'Application')),
    related_entity_id UUID NOT NULL,
    note_text TEXT NOT NULL,
    visibility VARCHAR(50) NOT NULL DEFAULT 'Internal' CHECK (visibility IN ('Internal', 'Private', 'Public')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 16. INTERVIEWS / DISCUSSIONS (E-15)
-- ============================================================================
CREATE TABLE IF NOT EXISTS interviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    scheduled_at TIMESTAMPTZ NOT NULL,
    format VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'Scheduled' CHECK (status IN ('Scheduled', 'Completed', 'Cancelled')),
    outcome_summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 17. INTERVIEW PARTICIPANTS (Many-to-Many: Interview <-> Users)
-- ============================================================================
CREATE TABLE IF NOT EXISTS interview_participants (
    interview_id UUID NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    PRIMARY KEY (interview_id, user_id)
);

-- ============================================================================
-- 18. APPLICATION STATUS HISTORY (E-16) - Traceability & Audit
-- ============================================================================
CREATE TABLE IF NOT EXISTS application_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    previous_status VARCHAR(50) CHECK (
        previous_status IS NULL OR previous_status IN (
            'Received',
            'Under Review',
            'Shortlisted',
            'Discussion / Interview',
            'Selected',
            'Not Selected',
            'Withdrawn'
        )
    ),
    new_status VARCHAR(50) NOT NULL CHECK (
        new_status IN (
            'Received',
            'Under Review',
            'Shortlisted',
            'Discussion / Interview',
            'Selected',
            'Not Selected',
            'Withdrawn'
        )
    ),
    changed_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    reason TEXT,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 19. SYNC LOGS (Google Forms & Sheets Sync Audit)
-- ============================================================================
CREATE TABLE IF NOT EXISTS sync_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(100) NOT NULL DEFAULT 'Google Sheets / Forms',
    status VARCHAR(50) NOT NULL,
    total_rows INTEGER NOT NULL DEFAULT 0,
    created_count INTEGER NOT NULL DEFAULT 0,
    updated_count INTEGER NOT NULL DEFAULT 0,
    rejected_count INTEGER NOT NULL DEFAULT 0,
    error_summary TEXT,
    details JSONB,
    synced_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- PERFORMANCE INDEXES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_roles_team_id ON roles(team_id);
CREATE INDEX IF NOT EXISTS idx_applicants_email ON applicants(email);
CREATE INDEX IF NOT EXISTS idx_applications_applicant_id ON applications(applicant_id);
CREATE INDEX IF NOT EXISTS idx_applications_role_id ON applications(role_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(current_status);
CREATE INDEX IF NOT EXISTS idx_experiences_applicant_id ON experiences(applicant_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_items_applicant_id ON portfolio_items(applicant_id);
CREATE INDEX IF NOT EXISTS idx_applicant_skills_applicant_id ON applicant_skills(applicant_id);
CREATE INDEX IF NOT EXISTS idx_team_members_team_id ON team_members(team_id);
CREATE INDEX IF NOT EXISTS idx_team_members_applicant_id ON team_members(applicant_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_app_id ON evaluations(application_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_reviewer_id ON evaluations(reviewer_id);
CREATE INDEX IF NOT EXISTS idx_eval_scores_eval_id ON evaluation_scores(evaluation_id);
CREATE INDEX IF NOT EXISTS idx_notes_entity ON notes(related_entity_type, related_entity_id);
CREATE INDEX IF NOT EXISTS idx_interviews_app_id ON interviews(application_id);
CREATE INDEX IF NOT EXISTS idx_status_history_app_id ON application_status_history(application_id);
CREATE INDEX IF NOT EXISTS idx_status_history_changed_at ON application_status_history(changed_at);

-- ============================================================================
-- SEED DATA: APPROVED TARGET ROLES
-- ============================================================================
INSERT INTO roles (role_name, role_description, number_of_openings, role_status)
VALUES 
    ('Team Lead + Product/Game Concept Lead / Research & Presentation', 'Lead team vision, narrative concept, product roadmap, research integration, and final presentation.', 1, 'Open'),
    ('Game/App Developer', 'Core software engineering, game engine architecture, application development, and interactive feature implementation.', 1, 'Open'),
    ('UI/UX & Visual Designer', 'User experience flows, visual assets, wireframing, interface design, and aesthetic presentation.', 1, 'Open'),
    ('Space/Science Research + Game Logic', 'Domain science research, accuracy verification, game mechanics logic, and narrative fact alignment.', 1, 'Open')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- SEED DATA: APPROVED EVALUATION CRITERIA (ARTS-EDS-008)
-- ============================================================================
INSERT INTO evaluation_criteria (criterion_name, criterion_description, is_active)
VALUES 
    ('Relevant Skills & Technical Competency', 'Does the submitted evidence demonstrate skills genuinely relevant to this role? Assess what has been shown, not credentials alone.', true),
    ('Project Experience & Demonstrable Work', 'Does the applicant submitted work history, portfolio, or GitHub show applied, hands-on experience relevant to the role?', true),
    ('Motivation & Role Alignment', 'Does the applicant stated motivation statement reflect genuine understanding of and alignment with this role purpose within the NASA Space Apps challenge?', true),
    ('Availability & Commitment', 'Has the applicant stated adequate and realistic availability for the challenge duration?', true),
    ('Communication Clarity', 'Is the overall submission coherent, complete, and professional? Does the applicant communicate clearly about their background and intentions?', true)
ON CONFLICT DO NOTHING;

