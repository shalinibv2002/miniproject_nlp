-- TCE Activity Intelligence System - Database Schema
-- All tables, foreign keys, and CHECK constraints.

PRAGMA foreign_keys = ON;

-- ============================================================
-- Reference / Lookup Tables
-- ============================================================

CREATE TABLE IF NOT EXISTS academic_years (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,                           -- e.g. '2020-2021'
    start_year INTEGER NOT NULL CHECK (start_year BETWEEN 2000 AND 2100),
    end_year INTEGER NOT NULL CHECK (end_year BETWEEN 2000 AND 2100),
    is_active INTEGER NOT NULL DEFAULT 0 CHECK (is_active IN (0, 1)),
    CONSTRAINT year_span_valid CHECK (end_year = start_year + 1),
    UNIQUE (start_year, end_year)
);

CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL UNIQUE,
    short_name TEXT,
    aliases TEXT                              -- comma-separated alias list
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS stakeholders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS classification_methods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,                  -- 'Rule-Based Keyword', 'TF-IDF + LogisticRegression' etc.
    description TEXT,
    version TEXT
);

-- Department statuses: Single Department, Multiple Departments, Institution-wide, Unknown
CREATE TABLE IF NOT EXISTS department_statuses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,                  -- 'single', 'multiple', 'institution_wide', 'unknown'
    label TEXT NOT NULL UNIQUE
);

-- Verification statuses
CREATE TABLE IF NOT EXISTS verification_statuses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,                  -- 'pending', 'verified', 'needs_review', 'rejected'
    label TEXT NOT NULL UNIQUE
);

-- ============================================================
-- Source Registry (sites/pages we collect from)
-- ============================================================

CREATE TABLE IF NOT EXISTS source_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN (
        'events', 'academics', 'departments', 'sports', 'ncc',
        'nss', 'clubs', 'achievements', 'outreach', 'newsletter',
        'pdf', 'other'
    )),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    notes TEXT,
    last_collected_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================
-- Collection pipeline tables
-- ============================================================

CREATE TABLE IF NOT EXISTS collection_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_registry_id INTEGER REFERENCES source_registry(id),
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    finished_at TEXT,
    pages_processed INTEGER NOT NULL DEFAULT 0,
    raw_records INTEGER NOT NULL DEFAULT 0,
    saved_records INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'running'
        CHECK (status IN ('running', 'completed', 'failed', 'partial')),
    notes TEXT
);

CREATE TABLE IF NOT EXISTS collection_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_run_id INTEGER REFERENCES collection_runs(id),
    source_registry_id INTEGER REFERENCES source_registry(id),
    url TEXT,
    stage TEXT NOT NULL DEFAULT 'collect'
        CHECK (stage IN ('collect', 'clean', 'validate', 'extract', 'classify', 'dedupe', 'load')),
    error_type TEXT,
    error_message TEXT,
    raw_record_id TEXT,                        -- reference to saved raw JSON id if any
    status TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'reviewed', 'resolved')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Step 2 raw-source provenance. These rows are deliberately independent of
-- institutional_activities: crawling must never create or merge activities.
CREATE TABLE IF NOT EXISTS collection_run_details (
    collection_run_id INTEGER PRIMARY KEY REFERENCES collection_runs(id) ON DELETE CASCADE,
    seed_urls_json TEXT NOT NULL,
    pages_discovered INTEGER NOT NULL DEFAULT 0,
    pages_fetched INTEGER NOT NULL DEFAULT 0,
    pages_successfully_processed INTEGER NOT NULL DEFAULT 0,
    pages_failed INTEGER NOT NULL DEFAULT 0,
    relevant_pages INTEGER NOT NULL DEFAULT 0,
    pdfs_discovered INTEGER NOT NULL DEFAULT 0,
    pdfs_processed INTEGER NOT NULL DEFAULT 0,
    pdfs_failed INTEGER NOT NULL DEFAULT 0,
    duplicate_urls_skipped INTEGER NOT NULL DEFAULT 0,
    retry_count INTEGER NOT NULL DEFAULT 0,
    parser_errors INTEGER NOT NULL DEFAULT 0,
    safety_limit_reached INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS raw_source_occurrences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_run_id INTEGER NOT NULL REFERENCES collection_runs(id) ON DELETE CASCADE,
    source_url TEXT NOT NULL,
    normalized_url TEXT NOT NULL,
    referring_url TEXT,
    source_type TEXT NOT NULL CHECK (source_type IN ('html', 'pdf')),
    page_title TEXT,
    source_section TEXT,
    http_status INTEGER,
    content_type TEXT,
    archive_path TEXT,
    text_archive_path TEXT,
    extraction_status TEXT NOT NULL DEFAULT 'not_attempted',
    extraction_error TEXT,
    first_discovered_at TEXT NOT NULL DEFAULT (datetime('now')),
    collected_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(collection_run_id, normalized_url)
);

-- Step 3 candidates are an extraction workbench. They are deliberately not
-- canonical institutional activities and must not be deduplicated at this stage.
CREATE TABLE IF NOT EXISTS extraction_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_run_id INTEGER REFERENCES collection_runs(id),
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    finished_at TEXT,
    minimum_evidence_score REAL NOT NULL DEFAULT 0.5,
    dry_run INTEGER NOT NULL DEFAULT 0 CHECK (dry_run IN (0, 1)),
    status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
    metrics_json TEXT
);

CREATE TABLE IF NOT EXISTS activity_candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    extraction_run_id INTEGER NOT NULL REFERENCES extraction_runs(id) ON DELETE CASCADE,
    source_occurrence_id INTEGER NOT NULL REFERENCES raw_source_occurrences(id) ON DELETE RESTRICT,
    title TEXT NOT NULL,
    description TEXT,
    activity_date TEXT,
    activity_date_end TEXT,
    activity_date_text TEXT,
    academic_year TEXT,
    category_hint TEXT,
    department TEXT,
    department_text TEXT,
    stakeholder TEXT,
    stakeholder_text TEXT,
    achievement_outcome TEXT,
    keywords_json TEXT,
    evidence_text TEXT NOT NULL,
    extraction_method TEXT NOT NULL,
    extraction_confidence REAL NOT NULL CHECK (extraction_confidence >= 0 AND extraction_confidence <= 1),
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'REVIEW', 'ACCEPTED', 'REJECTED')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS source_extraction_telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    extraction_run_id INTEGER NOT NULL REFERENCES extraction_runs(id) ON DELETE CASCADE,
    source_occurrence_id INTEGER NOT NULL REFERENCES raw_source_occurrences(id) ON DELETE CASCADE,
    contains_activity_evidence INTEGER NOT NULL CHECK (contains_activity_evidence IN (0, 1)),
    evidence_score REAL NOT NULL CHECK (evidence_score >= 0 AND evidence_score <= 1),
    reason TEXT,
    candidates_extracted INTEGER NOT NULL DEFAULT 0,
    extraction_status TEXT NOT NULL CHECK (extraction_status IN ('SUCCESS', 'SKIPPED', 'FAILED')),
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(extraction_run_id, source_occurrence_id)
);

-- Step 4 candidate-only final-taxonomy classifications.  These rows remain
-- separate from activity_categories until a later review/promotion stage.
CREATE TABLE IF NOT EXISTS candidate_classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL REFERENCES activity_candidates(id) ON DELETE CASCADE,
    final_category TEXT NOT NULL,
    classification_confidence REAL NOT NULL CHECK (classification_confidence >= 0 AND classification_confidence <= 1),
    category_hint TEXT,
    hint_match_status TEXT NOT NULL CHECK (hint_match_status IN ('CONSISTENT', 'SUPPORTING', 'DIFFERENT', 'NO_HINT')),
    classified_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(candidate_id, final_category)
);

CREATE INDEX IF NOT EXISTS idx_candidate_classifications_candidate ON candidate_classifications(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_classifications_category ON candidate_classifications(final_category);

-- Step 5 audit trail for conservative academic-year resolution.  The original
-- value is retained so later review can distinguish source extraction from
-- this evidence-based resolution pass.
CREATE TABLE IF NOT EXISTS candidate_academic_year_resolutions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL UNIQUE REFERENCES activity_candidates(id) ON DELETE CASCADE,
    original_academic_year TEXT,
    resolved_academic_year TEXT NOT NULL,
    resolution_reason TEXT NOT NULL CHECK (resolution_reason IN (
        'EXACT_ACTIVITY_DATE', 'ACTIVITY_BLOCK_DATE', 'ACADEMIC_YEAR_CONTEXT',
        'ANNUAL_REPORT_CONTEXT', 'YEAR_CONTEXT'
    )),
    resolved_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS candidate_quality_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL UNIQUE REFERENCES activity_candidates(id) ON DELETE CASCADE,
    quality_status TEXT NOT NULL CHECK (quality_status IN ('GOOD', 'REVIEW', 'NON_ACTIVITY')),
    quality_reason TEXT,
    reviewed_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_candidate_quality_status ON candidate_quality_reviews(quality_status);

-- Step 6 final-dataset extensions. Candidate provenance and display-oriented
-- metadata remain separate from the stable core activity table.
CREATE TABLE IF NOT EXISTS final_activity_metadata (
    activity_id INTEGER PRIMARY KEY REFERENCES institutional_activities(id) ON DELETE CASCADE,
    activity_date_text TEXT,
    academic_year TEXT,
    department_display TEXT NOT NULL DEFAULT 'General',
    stakeholder_display TEXT,
    achievement_outcome TEXT,
    evidence_text TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS activity_candidate_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL REFERENCES institutional_activities(id) ON DELETE CASCADE,
    candidate_id INTEGER NOT NULL UNIQUE REFERENCES activity_candidates(id) ON DELETE RESTRICT,
    linked_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(activity_id, candidate_id)
);

CREATE INDEX IF NOT EXISTS idx_activity_candidate_links_activity ON activity_candidate_links(activity_id);

CREATE TABLE IF NOT EXISTS duplicate_candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id_a INTEGER REFERENCES institutional_activities(id),
    activity_id_b INTEGER REFERENCES institutional_activities(id),
    similarity_score REAL NOT NULL CHECK (similarity_score >= 0 AND similarity_score <= 1),
    match_reason TEXT,
    status TEXT NOT NULL DEFAULT 'Pending'
        CHECK (status IN ('Auto-Merged', 'Pending', 'Resolved-Not-Duplicate', 'Resolved-Merged', 'Rejected')),
    reviewed_by TEXT,
    reviewed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================
-- Core Activity Tables
-- ============================================================

CREATE TABLE IF NOT EXISTS institutional_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    normalized_title TEXT NOT NULL,
    description TEXT,
    activity_date TEXT,                        -- YYYY-MM-DD
    activity_date_end TEXT,
    venue TEXT,
    organizer TEXT,
    resource_person TEXT,
    activity_year_id INTEGER REFERENCES academic_years(id),
    department_status_id INTEGER REFERENCES department_statuses(id),
    verification_status_id INTEGER REFERENCES verification_statuses(id),
    overall_confidence REAL CHECK (overall_confidence >= 0 AND overall_confidence <= 1),
    is_verified INTEGER NOT NULL DEFAULT 0 CHECK (is_verified IN (0, 1)),
    source_url TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS activity_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL REFERENCES institutional_activities(id) ON DELETE CASCADE,
    source_registry_id INTEGER REFERENCES source_registry(id),
    source_url TEXT NOT NULL,
    raw_record_id TEXT,
    collected_at TEXT,
    UNIQUE (activity_id, source_url)
);

CREATE TABLE IF NOT EXISTS activity_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL REFERENCES institutional_activities(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    confidence REAL CHECK (confidence >= 0 AND confidence <= 1),
    classification_method_id INTEGER REFERENCES classification_methods(id),
    is_primary INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (activity_id, category_id)
);

CREATE TABLE IF NOT EXISTS activity_departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL REFERENCES institutional_activities(id) ON DELETE CASCADE,
    department_id INTEGER NOT NULL REFERENCES departments(id),
    confidence REAL CHECK (confidence >= 0 AND confidence <= 1),
    is_primary INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (activity_id, department_id)
);

CREATE TABLE IF NOT EXISTS activity_stakeholders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL REFERENCES institutional_activities(id) ON DELETE CASCADE,
    stakeholder_id INTEGER NOT NULL REFERENCES stakeholders(id),
    confidence REAL CHECK (confidence >= 0 AND confidence <= 1),
    is_primary INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (activity_id, stakeholder_id)
);

CREATE TABLE IF NOT EXISTS activity_entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL REFERENCES institutional_activities(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL CHECK (entity_type IN (
        'PERSON', 'ORG', 'DATE', 'GPE', 'VENUE', 'AWARD', 'TOPIC', 'MONEY', 'PRODUCT', 'OTHER'
    )),
    entity_text TEXT NOT NULL,
    confidence REAL CHECK (confidence >= 0 AND confidence <= 1),
    extraction_method_id INTEGER REFERENCES classification_methods(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS activity_keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL REFERENCES institutional_activities(id) ON DELETE CASCADE,
    keyword TEXT NOT NULL,
    weight REAL CHECK (weight >= 0 AND weight <= 1),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (activity_id, keyword)
);

-- ============================================================
-- Review / Human-in-the-loop
-- ============================================================

CREATE TABLE IF NOT EXISTS review_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL REFERENCES institutional_activities(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,                       -- e.g. 'low-confidence', 'duplicate', 'validation-flag'
    status TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'in_progress', 'approved', 'rejected')),
    assigned_to TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS review_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL REFERENCES institutional_activities(id) ON DELETE CASCADE,
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    action TEXT NOT NULL CHECK (action IN (
        'edit', 'merge', 'duplicate-mark', 'verify-source',
        'verify-linkedin', 'approve', 'reject', 'unflag'
    )),
    reviewer TEXT NOT NULL,
    reason TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================
-- LinkedIn cross-reference
-- ============================================================

CREATE TABLE IF NOT EXISTS linkedin_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL REFERENCES institutional_activities(id) ON DELETE CASCADE,
    match_status TEXT NOT NULL CHECK (match_status IN (
        'Matched', 'Possible Match', 'Not Found', 'Not Checked'
    )),
    linkedin_post_url TEXT,
    linkedin_post_text TEXT,
    search_terms TEXT,
    confidence REAL CHECK (confidence >= 0 AND confidence <= 1),
    checked_by TEXT,
    checked_at TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================
-- Indexes for typical query patterns
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_activities_year ON institutional_activities(activity_year_id);
CREATE INDEX IF NOT EXISTS idx_activities_date ON institutional_activities(activity_date);
CREATE INDEX IF NOT EXISTS idx_activities_verification ON institutional_activities(verification_status_id);
CREATE INDEX IF NOT EXISTS idx_activities_confidence ON institutional_activities(overall_confidence);
CREATE INDEX IF NOT EXISTS idx_act_cat_activity ON activity_categories(activity_id);
CREATE INDEX IF NOT EXISTS idx_act_cat_category ON activity_categories(category_id);
CREATE INDEX IF NOT EXISTS idx_act_dept_activity ON activity_departments(activity_id);
CREATE INDEX IF NOT EXISTS idx_act_dept_department ON activity_departments(department_id);
CREATE INDEX IF NOT EXISTS idx_act_stake_activity ON activity_stakeholders(activity_id);
CREATE INDEX IF NOT EXISTS idx_act_stake_stakeholder ON activity_stakeholders(stakeholder_id);
CREATE INDEX IF NOT EXISTS idx_act_ent_activity ON activity_entities(activity_id);
CREATE INDEX IF NOT EXISTS idx_act_keyword_activity ON activity_keywords(activity_id);
CREATE INDEX IF NOT EXISTS idx_review_queue_status ON review_queue(status);
CREATE INDEX IF NOT EXISTS idx_dup_candidates_status ON duplicate_candidates(status);


