-- =====================================================================
-- 04_setup_raw_tables.sql
-- FHIR-equivalent resource tables: Patient, Encounter, Condition,
-- Observation, MedicationRequest, Procedure.
-- =====================================================================

USE ROLE DBT_ROLE;
USE WAREHOUSE LOAD_WH_XS;
USE DATABASE HEALTHCARE_DB;
USE SCHEMA RAW;

-- ---------------------------------------------------------------------
-- raw_patients — FHIR Patient
-- All PHI columns are flagged in comments.
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE raw_patients (
    patient_id          VARCHAR(64)        NOT NULL,
    mrn                 VARCHAR(50),     -- PHI: medical record number
    first_name          VARCHAR(100),    -- PHI
    last_name           VARCHAR(100),    -- PHI
    date_of_birth       DATE,            -- PHI
    gender              VARCHAR(20),
    race                VARCHAR(50),
    ethnicity           VARCHAR(50),
    marital_status      VARCHAR(20),
    address_line1       VARCHAR(255),    -- PHI
    address_city        VARCHAR(100),    -- PHI (in combination)
    address_state       VARCHAR(50),
    address_postal_code VARCHAR(20),     -- PHI (3-digit prefix safe; full not safe)
    phone_number        VARCHAR(30),     -- PHI
    email               VARCHAR(255),    -- PHI
    insurance_id        VARCHAR(50),     -- PHI
    insurance_plan      VARCHAR(100),
    primary_language    VARCHAR(20),
    is_deceased         BOOLEAN,
    deceased_date       DATE,
    created_at          TIMESTAMP_NTZ,
    updated_at          TIMESTAMP_NTZ,
    _loaded_at          TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ---------------------------------------------------------------------
-- raw_encounters — FHIR Encounter
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE raw_encounters (
    encounter_id        VARCHAR(64)        NOT NULL,
    patient_id          VARCHAR(64),
    encounter_class     VARCHAR(20),     -- inpatient / outpatient / ambulatory / emergency
    encounter_type      VARCHAR(100),    -- e.g. "office visit", "well-baby"
    admission_timestamp TIMESTAMP_NTZ,
    discharge_timestamp TIMESTAMP_NTZ,
    length_of_stay_hours NUMBER(12, 2),
    department          VARCHAR(100),
    primary_diagnosis_code  VARCHAR(20),  -- ICD-10
    primary_diagnosis_text  VARCHAR(500),
    discharge_disposition VARCHAR(100),
    is_readmission_30d  BOOLEAN,
    total_charges       NUMBER(12, 2),
    created_at          TIMESTAMP_NTZ,
    updated_at          TIMESTAMP_NTZ,
    _loaded_at          TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ---------------------------------------------------------------------
-- raw_observations — FHIR Observation (vitals + labs)
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE raw_observations (
    observation_id      VARCHAR(64)        NOT NULL,
    patient_id          VARCHAR(64),
    encounter_id        VARCHAR(64),
    observation_type    VARCHAR(40),     -- vital / lab / imaging
    code                VARCHAR(20),     -- LOINC
    code_text           VARCHAR(255),    -- e.g. "Heart rate"
    value               NUMBER(18, 4),
    unit                VARCHAR(20),
    observation_timestamp TIMESTAMP_NTZ,
    abnormal_flag       VARCHAR(10),     -- normal / high / low / critical
    _loaded_at          TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ---------------------------------------------------------------------
-- raw_conditions — FHIR Condition
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE raw_conditions (
    condition_id        VARCHAR(64)        NOT NULL,
    patient_id          VARCHAR(64),
    encounter_id        VARCHAR(64),
    code                VARCHAR(20),     -- ICD-10
    code_text           VARCHAR(500),
    onset_date          DATE,
    abated_date         DATE,
    clinical_status     VARCHAR(20),     -- active / resolved / inactive
    verification_status VARCHAR(20),     -- confirmed / provisional / differential
    _loaded_at          TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ---------------------------------------------------------------------
-- raw_medications — FHIR MedicationRequest
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE raw_medications (
    medication_request_id VARCHAR(64)        NOT NULL,
    patient_id          VARCHAR(64),
    encounter_id        VARCHAR(64),
    rxnorm_code         VARCHAR(20),     -- RxNorm
    medication_name     VARCHAR(255),
    dosage_text         VARCHAR(255),
    route               VARCHAR(20),     -- oral / iv / topical / etc.
    prescribed_at       TIMESTAMP_NTZ,
    days_supply         NUMBER(8, 0),
    refills_allowed     NUMBER(4, 0),
    _loaded_at          TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ---------------------------------------------------------------------
-- raw_procedures — FHIR Procedure
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE raw_procedures (
    procedure_id        VARCHAR(64)        NOT NULL,
    patient_id          VARCHAR(64),
    encounter_id        VARCHAR(64),
    cpt_code            VARCHAR(20),     -- CPT or HCPCS
    procedure_text      VARCHAR(500),
    performed_at        TIMESTAMP_NTZ,
    performer_provider  VARCHAR(100),
    _loaded_at          TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

SHOW TABLES IN SCHEMA RAW;
