-- =====================================================================
-- 06_setup_baseline_views.sql
-- =====================================================================
-- BASELINE arm: PHI redaction via simple views without masking policies.
-- This is the pattern most teams adopt before discovering Dynamic Data
-- Masking. It works but has well-known weaknesses:
--
--   1. Every consumer SQL must reference the view, not the underlying
--      table. Forgetting → PHI leak.
--   2. New columns in the underlying table are not redacted by default.
--   3. There's no role-based unmasking — clinicians cannot see real
--      values without a separate, manually-grants-managed view.
--   4. There's no row-level filtering at all — must be re-implemented
--      per-view as a WHERE clause.
--
-- These views are referenced by the BASELINE-arm queries in the
-- experiment to give a fair comparison.
-- =====================================================================

USE ROLE DBT_ROLE;
USE WAREHOUSE DBT_WH_XS;
USE DATABASE HEALTHCARE_DB;
USE SCHEMA BASELINE;

-- A view-based redaction of patient data — only de-identified columns
-- are exposed. Effectively a one-size-fits-all mask.
CREATE OR REPLACE VIEW vw_patient_deidentified AS
SELECT
    patient_id,
    -- All PHI removed
    'REDACTED'                                  AS first_name,
    'REDACTED'                                  AS last_name,
    'MRN_*****'                                 AS mrn,
    NULL::DATE                                  AS date_of_birth,
    LEFT(address_postal_code, 3) || '**'        AS address_postal_code_3digit,
    NULL                                        AS phone_number,
    NULL                                        AS email,
    -- Non-PHI columns
    gender, race, ethnicity, marital_status,
    address_state, primary_language,
    insurance_plan,
    is_deceased, deceased_date,
    created_at, updated_at
FROM HEALTHCARE_DB.RAW.RAW_PATIENTS
-- Mimic the row access policy
WHERE NOT is_deceased OR deceased_date >= DATEADD('year', -5, CURRENT_DATE());

-- A separate "clinician" view, manually managed.
CREATE OR REPLACE VIEW vw_patient_clinician AS
SELECT
    patient_id, first_name, last_name, mrn,
    DATE_FROM_PARTS(EXTRACT(YEAR FROM date_of_birth), 1, 1) AS date_of_birth_year_only,
    address_postal_code,
    NULL                                        AS phone_number,  -- still redacted
    NULL                                        AS email,         -- still redacted
    gender, race, ethnicity, marital_status,
    address_state, primary_language,
    insurance_plan,
    is_deceased, deceased_date,
    created_at, updated_at
FROM HEALTHCARE_DB.RAW.RAW_PATIENTS;

GRANT SELECT ON VIEW vw_patient_deidentified TO ROLE ANALYST_ROLE;
GRANT SELECT ON VIEW vw_patient_clinician    TO ROLE CLINICIAN_ROLE;

SHOW VIEWS IN SCHEMA BASELINE;
