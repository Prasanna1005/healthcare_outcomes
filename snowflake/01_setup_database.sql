-- =====================================================================
-- 01_setup_database.sql
-- =====================================================================

USE ROLE ACCOUNTADMIN;

CREATE DATABASE IF NOT EXISTS HEALTHCARE_DB
    COMMENT = 'Healthcare Outcomes & PHI Governance — MSc Capstone Project 3';

USE DATABASE HEALTHCARE_DB;

CREATE SCHEMA IF NOT EXISTS RAW          COMMENT = 'Bronze: source landing (synthetic FHIR)';
CREATE SCHEMA IF NOT EXISTS STAGING      COMMENT = 'Silver: cleaned views';
CREATE SCHEMA IF NOT EXISTS INTERMEDIATE COMMENT = 'Silver: joined and enriched';
CREATE SCHEMA IF NOT EXISTS MARTS        COMMENT = 'Gold: clinical + governance marts';
CREATE SCHEMA IF NOT EXISTS GOVERNANCE   COMMENT = 'Snowflake masking + row access policies';
CREATE SCHEMA IF NOT EXISTS BASELINE     COMMENT = 'View-based PHI redaction (BASELINE arm of experiment)';
CREATE SCHEMA IF NOT EXISTS SNAPSHOTS    COMMENT = 'dbt SCD2 snapshots';
CREATE SCHEMA IF NOT EXISTS META         COMMENT = 'Experiment metadata + audit logs';

SHOW SCHEMAS IN DATABASE HEALTHCARE_DB;
