-- =====================================================================
-- 00_setup_warehouses.sql
-- =====================================================================

USE ROLE ACCOUNTADMIN;

CREATE WAREHOUSE IF NOT EXISTS DBT_WH_XS
    WITH WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Primary dbt + Airflow workload';

CREATE WAREHOUSE IF NOT EXISTS LOAD_WH_XS
    WITH WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Bulk load workload';

CREATE WAREHOUSE IF NOT EXISTS EXPT_WH_S
    WITH WAREHOUSE_SIZE = 'SMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Governance experiment runs';

SHOW WAREHOUSES LIKE '%WH%';
