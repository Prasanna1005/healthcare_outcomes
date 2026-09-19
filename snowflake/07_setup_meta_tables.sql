-- =====================================================================
-- 07_setup_meta_tables.sql
-- =====================================================================

USE ROLE DBT_ROLE;
USE DATABASE HEALTHCARE_DB;
USE SCHEMA META;

CREATE OR REPLACE TABLE experiment_runs (
    run_id           NUMBER(38, 0) IDENTITY START 1 INCREMENT 1,
    run_uuid         VARCHAR(64)        NOT NULL,
    condition        VARCHAR(40)        NOT NULL,    -- BASELINE_VIEWS | INTERVENTION_POLICIES
    run_index        NUMBER(10, 0),
    started_at       TIMESTAMP_LTZ,
    completed_at     TIMESTAMP_LTZ,
    duration_seconds NUMBER(12, 2),
    notes            VARCHAR(1000)
);

CREATE OR REPLACE TABLE experiment_metrics (
    metric_id        NUMBER(38, 0) IDENTITY START 1 INCREMENT 1,
    run_uuid         VARCHAR(64)        NOT NULL,
    condition        VARCHAR(40)        NOT NULL,
    metric_name      VARCHAR(100)       NOT NULL,
    metric_value     FLOAT,
    captured_at      TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Per-query latency log
CREATE OR REPLACE TABLE experiment_query_log (
    query_log_id     NUMBER(38, 0) IDENTITY START 1 INCREMENT 1,
    run_uuid         VARCHAR(64)        NOT NULL,
    condition        VARCHAR(40)        NOT NULL,
    role_simulated   VARCHAR(40),       -- analyst / clinician / phi_admin
    query_template   VARCHAR(100),
    rows_returned    NUMBER(38, 0),
    elapsed_ms       NUMBER(12, 2),
    captured_at      TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Audit log (governance violations caught + bypass attempts)
CREATE OR REPLACE TABLE governance_audit_log (
    audit_id         NUMBER(38, 0) IDENTITY START 1 INCREMENT 1,
    run_uuid         VARCHAR(64),
    condition        VARCHAR(40),
    audit_check      VARCHAR(100),
    pass_or_fail     VARCHAR(10),
    detail           VARCHAR(2000),
    captured_at      TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

SHOW TABLES IN SCHEMA META;
