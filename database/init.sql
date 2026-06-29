-- =============================================================
-- AI-WAF PostgreSQL Schema
-- Version: 1.0.0
-- =============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================
-- ENUM TYPES
-- =============================================================

CREATE TYPE decision_enum AS ENUM ('allowed', 'blocked');
CREATE TYPE severity_enum AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
CREATE TYPE engine_enum AS ENUM ('rule_engine', 'secbert', 'autoencoder', 'meta_learner');
CREATE TYPE replay_status_enum AS ENUM ('pending', 'replayed', 'failed');
CREATE TYPE attack_category_enum AS ENUM ('SQLI', 'XSS', 'PATH_TRAVERSAL', 'COMMAND_INJECTION');

-- =============================================================
-- TABLE: raw_request_logs
-- Immutable capture of every inbound HTTP request.
-- Nothing is ever updated here; rows are append-only.
-- =============================================================

CREATE TABLE raw_request_logs (
    id               UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ip_address       INET        NOT NULL,
    method           VARCHAR(10) NOT NULL,
    path             TEXT        NOT NULL,
    original_headers JSONB,
    original_body    TEXT,
    user_agent       TEXT,
    request_size     INTEGER
);

COMMENT ON TABLE  raw_request_logs               IS 'Immutable capture of every inbound HTTP request before WAF processing.';
COMMENT ON COLUMN raw_request_logs.id            IS 'Globally unique request identifier (UUID v4).';
COMMENT ON COLUMN raw_request_logs.timestamp     IS 'UTC timestamp when the request arrived at the WAF.';
COMMENT ON COLUMN raw_request_logs.ip_address    IS 'Source IP address (supports both IPv4 and IPv6).';
COMMENT ON COLUMN raw_request_logs.method        IS 'HTTP method: GET, POST, PUT, DELETE, PATCH, etc.';
COMMENT ON COLUMN raw_request_logs.path          IS 'Raw request path including query string.';
COMMENT ON COLUMN raw_request_logs.original_headers IS 'Complete request headers stored as JSONB.';
COMMENT ON COLUMN raw_request_logs.original_body IS 'Raw request body (may be NULL for bodyless methods).';
COMMENT ON COLUMN raw_request_logs.user_agent    IS 'User-Agent header value for fingerprinting.';
COMMENT ON COLUMN raw_request_logs.request_size  IS 'Total request size in bytes.';

-- =============================================================
-- TABLE: processed_request_logs
-- WAF analysis output linked to the raw capture.
-- =============================================================

CREATE TABLE processed_request_logs (
    id               UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    raw_log_id       UUID            NOT NULL REFERENCES raw_request_logs(id) ON DELETE CASCADE,
    normalized_path  TEXT,
    normalized_body  TEXT,
    fingerprint      VARCHAR(64),
    decision         decision_enum   NOT NULL,
    attack_type      attack_category_enum,
    rule_version     VARCHAR(20),
    response_status  INTEGER,
    latency_ms       FLOAT,
    created_at       TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  processed_request_logs               IS 'WAF analysis results; one row per raw_request_logs entry.';
COMMENT ON COLUMN processed_request_logs.raw_log_id    IS 'FK to the raw_request_logs row being analysed.';
COMMENT ON COLUMN processed_request_logs.normalized_path IS 'URL-decoded, canonicalized path used by the WAF engines.';
COMMENT ON COLUMN processed_request_logs.normalized_body IS 'Sanitized/decoded body used by the WAF engines.';
COMMENT ON COLUMN processed_request_logs.fingerprint   IS 'SHA-256 (truncated) hash of the normalized request for deduplication.';
COMMENT ON COLUMN processed_request_logs.decision      IS 'Final WAF verdict: allowed or blocked.';
COMMENT ON COLUMN processed_request_logs.attack_type   IS 'Detected attack category when decision=blocked.';
COMMENT ON COLUMN processed_request_logs.rule_version  IS 'Rule-set version that was active at analysis time.';
COMMENT ON COLUMN processed_request_logs.response_status IS 'HTTP status code returned to the client.';
COMMENT ON COLUMN processed_request_logs.latency_ms    IS 'Total WAF processing latency in milliseconds.';

-- =============================================================
-- TABLE: detection_results
-- Per-engine detection outcome; multiple rows per request.
-- =============================================================

CREATE TABLE detection_results (
    id          UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id  UUID            NOT NULL REFERENCES raw_request_logs(id) ON DELETE CASCADE,
    engine      engine_enum     NOT NULL DEFAULT 'rule_engine',
    rule_id     VARCHAR(100),
    severity    severity_enum,
    confidence  FLOAT           CHECK (confidence >= 0 AND confidence <= 1),
    decision    decision_enum   NOT NULL,
    metadata    JSONB,
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  detection_results            IS 'Individual detection engine results; multiple engines can fire per request.';
COMMENT ON COLUMN detection_results.request_id IS 'FK to the raw_request_logs row being analysed.';
COMMENT ON COLUMN detection_results.engine     IS 'Detection engine that produced this result.';
COMMENT ON COLUMN detection_results.rule_id    IS 'Specific rule or model checkpoint that triggered.';
COMMENT ON COLUMN detection_results.severity   IS 'Severity assessment from this engine.';
COMMENT ON COLUMN detection_results.confidence IS 'Model confidence score [0.0–1.0]; NULL for rule-based engines.';
COMMENT ON COLUMN detection_results.decision   IS 'This engine''s individual verdict before meta-learner aggregation.';
COMMENT ON COLUMN detection_results.metadata   IS 'Engine-specific extra data (matched pattern, token positions, etc.).';

-- =============================================================
-- TABLE: request_replays
-- Queue for replaying captured requests against target apps.
-- =============================================================

CREATE TABLE request_replays (
    id              UUID                PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_log_id  UUID                NOT NULL REFERENCES raw_request_logs(id) ON DELETE CASCADE,
    payload         TEXT,
    headers         JSONB,
    method          VARCHAR(10)         NOT NULL,
    path            TEXT                NOT NULL,
    timestamp       TIMESTAMPTZ         NOT NULL DEFAULT NOW(),
    status          replay_status_enum  NOT NULL DEFAULT 'pending',
    replayed_at     TIMESTAMPTZ
);

COMMENT ON TABLE  request_replays                 IS 'Queue of captured requests to be replayed against target applications.';
COMMENT ON COLUMN request_replays.request_log_id  IS 'FK to the original raw_request_logs row.';
COMMENT ON COLUMN request_replays.payload         IS 'Optionally modified request body for replay.';
COMMENT ON COLUMN request_replays.headers         IS 'Optionally modified headers for replay.';
COMMENT ON COLUMN request_replays.status          IS 'Replay lifecycle: pending → replayed | failed.';
COMMENT ON COLUMN request_replays.replayed_at     IS 'Timestamp when the replay worker dispatched the request.';

-- =============================================================
-- TABLE: rule_stats
-- Aggregate hit counters for every WAF rule.
-- =============================================================

CREATE TABLE rule_stats (
    id              UUID                PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id         VARCHAR(100)        NOT NULL UNIQUE,
    rule_name       VARCHAR(200),
    category        attack_category_enum,
    severity        severity_enum,
    hit_count       BIGINT              NOT NULL DEFAULT 0,
    last_triggered  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ         NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ         NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  rule_stats              IS 'Aggregate hit counters and metadata for each WAF rule.';
COMMENT ON COLUMN rule_stats.rule_id      IS 'Unique rule identifier (e.g. SQLI-001, XSS-042).';
COMMENT ON COLUMN rule_stats.rule_name    IS 'Human-readable rule description.';
COMMENT ON COLUMN rule_stats.hit_count    IS 'Total number of times this rule has fired.';
COMMENT ON COLUMN rule_stats.last_triggered IS 'Timestamp of the most recent match.';
COMMENT ON COLUMN rule_stats.updated_at   IS 'Auto-updated by application logic when hit_count changes.';

-- =============================================================
-- INDEXES
-- =============================================================

-- raw_request_logs
CREATE INDEX idx_raw_logs_timestamp   ON raw_request_logs(timestamp DESC);
CREATE INDEX idx_raw_logs_ip          ON raw_request_logs(ip_address);
CREATE INDEX idx_raw_logs_method      ON raw_request_logs(method);

-- processed_request_logs
CREATE INDEX idx_processed_logs_raw         ON processed_request_logs(raw_log_id);
CREATE INDEX idx_processed_logs_decision    ON processed_request_logs(decision);
CREATE INDEX idx_processed_logs_attack      ON processed_request_logs(attack_type);
CREATE INDEX idx_processed_logs_fingerprint ON processed_request_logs(fingerprint);
CREATE INDEX idx_processed_logs_created_at  ON processed_request_logs(created_at DESC);

-- detection_results
CREATE INDEX idx_detection_results_request ON detection_results(request_id);
CREATE INDEX idx_detection_results_engine  ON detection_results(engine);
CREATE INDEX idx_detection_results_rule    ON detection_results(rule_id);
CREATE INDEX idx_detection_results_created ON detection_results(created_at DESC);

-- request_replays
CREATE INDEX idx_replays_status    ON request_replays(status);
CREATE INDEX idx_replays_timestamp ON request_replays(timestamp DESC);

-- rule_stats
CREATE INDEX idx_rule_stats_hit_count ON rule_stats(hit_count DESC);
CREATE INDEX idx_rule_stats_category  ON rule_stats(category);

-- =============================================================
-- SEED DATA: Built-in WAF rules
-- =============================================================

INSERT INTO rule_stats (rule_id, rule_name, category, severity, hit_count) VALUES
    ('SQLI-001', 'Classic SQL Injection (UNION SELECT)',          'SQLI',              'CRITICAL', 0),
    ('SQLI-002', 'Blind SQL Injection (Boolean-based)',           'SQLI',              'HIGH',     0),
    ('SQLI-003', 'Time-Based Blind SQL Injection',               'SQLI',              'HIGH',     0),
    ('SQLI-004', 'SQL Comment Sequence Detection',               'SQLI',              'MEDIUM',   0),
    ('XSS-001',  'Reflected XSS – Script Tag Injection',         'XSS',               'HIGH',     0),
    ('XSS-002',  'DOM-Based XSS – Event Handler Injection',      'XSS',               'HIGH',     0),
    ('XSS-003',  'Stored XSS – HTML Entity Bypass',              'XSS',               'MEDIUM',   0),
    ('PATH-001', 'Path Traversal – Dot-Dot Slash Sequence',      'PATH_TRAVERSAL',    'HIGH',     0),
    ('PATH-002', 'Path Traversal – URL-Encoded Bypass',          'PATH_TRAVERSAL',    'HIGH',     0),
    ('CMD-001',  'OS Command Injection – Shell Metacharacters',  'COMMAND_INJECTION', 'CRITICAL', 0),
    ('CMD-002',  'OS Command Injection – Backtick Execution',    'COMMAND_INJECTION', 'CRITICAL', 0),
    ('CMD-003',  'OS Command Injection – Semicolon Chaining',    'COMMAND_INJECTION', 'HIGH',     0);
