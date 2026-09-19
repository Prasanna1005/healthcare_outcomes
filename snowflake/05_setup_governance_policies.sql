-- =====================================================================
-- 05_setup_governance_policies.sql
-- =====================================================================
-- Snowflake Dynamic Data Masking + Row Access Policies.
-- Together with dbt contracts, these form the INTERVENTION arm of the
-- governance experiment.
--
-- Three masking policies are applied to the gold-layer dim_patient mart:
--   mask_full_name           — analyst sees 'REDACTED', clinician sees real
--   mask_mrn                 — analyst sees 'MRN_*****', clinician sees real
--   mask_dob_to_year         — analyst sees NULL, clinician sees year-only,
--                              phi_admin sees real
--   mask_phone               — universal redaction except phi_admin
--   mask_email               — universal redaction except phi_admin
--   mask_address             — universal redaction except phi_admin
--   mask_postal_code_to_3digit — analyst sees first 3 digits + '**', clinician
--                                sees full
--
-- Row access policies:
--   patient_row_access_policy — restricts analyst to non-deceased patients
--                               within the last 5 years
-- =====================================================================

USE ROLE DBT_ROLE;
USE WAREHOUSE DBT_WH_XS;
USE DATABASE HEALTHCARE_DB;
USE SCHEMA GOVERNANCE;

-- ---------------------------------------------------------------------
-- Masking policies
-- ---------------------------------------------------------------------

CREATE OR REPLACE MASKING POLICY mask_full_name AS
    (val VARCHAR) RETURNS VARCHAR ->
        CASE
            WHEN CURRENT_ROLE() IN ('PHI_ADMIN_ROLE', 'CLINICIAN_ROLE') THEN val
            ELSE 'REDACTED'
        END;

CREATE OR REPLACE MASKING POLICY mask_mrn AS
    (val VARCHAR) RETURNS VARCHAR ->
        CASE
            WHEN CURRENT_ROLE() IN ('PHI_ADMIN_ROLE', 'CLINICIAN_ROLE') THEN val
            ELSE 'MRN_*****'
        END;

CREATE OR REPLACE MASKING POLICY mask_dob_to_year AS
    (val DATE) RETURNS DATE ->
        CASE
            WHEN CURRENT_ROLE() = 'PHI_ADMIN_ROLE' THEN val
            WHEN CURRENT_ROLE() = 'CLINICIAN_ROLE' THEN DATE_FROM_PARTS(EXTRACT(YEAR FROM val), 1, 1)
            ELSE NULL
        END;

CREATE OR REPLACE MASKING POLICY mask_phone AS
    (val VARCHAR) RETURNS VARCHAR ->
        CASE WHEN CURRENT_ROLE() = 'PHI_ADMIN_ROLE' THEN val ELSE NULL END;

CREATE OR REPLACE MASKING POLICY mask_email AS
    (val VARCHAR) RETURNS VARCHAR ->
        CASE WHEN CURRENT_ROLE() = 'PHI_ADMIN_ROLE' THEN val ELSE NULL END;

CREATE OR REPLACE MASKING POLICY mask_address AS
    (val VARCHAR) RETURNS VARCHAR ->
        CASE WHEN CURRENT_ROLE() = 'PHI_ADMIN_ROLE' THEN val ELSE NULL END;

CREATE OR REPLACE MASKING POLICY mask_postal_code_to_3digit AS
    (val VARCHAR) RETURNS VARCHAR ->
        CASE
            WHEN CURRENT_ROLE() IN ('PHI_ADMIN_ROLE', 'CLINICIAN_ROLE') THEN val
            ELSE LEFT(val, 3) || '**'
        END;

-- ---------------------------------------------------------------------
-- Row access policy
-- Analysts cannot see deceased patients or patients older than 5 years.
-- ---------------------------------------------------------------------

CREATE OR REPLACE ROW ACCESS POLICY patient_row_access_policy AS
    (is_deceased BOOLEAN, deceased_date DATE) RETURNS BOOLEAN ->
        CASE
            WHEN CURRENT_ROLE() IN ('PHI_ADMIN_ROLE', 'CLINICIAN_ROLE') THEN TRUE
            WHEN CURRENT_ROLE() = 'ANALYST_ROLE'
                THEN NOT is_deceased OR deceased_date >= DATEADD('year', -5, CURRENT_DATE())
            ELSE FALSE
        END;

SHOW MASKING POLICIES IN SCHEMA GOVERNANCE;
SHOW ROW ACCESS POLICIES IN SCHEMA GOVERNANCE;
