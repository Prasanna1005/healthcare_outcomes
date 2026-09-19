
{{ config(materialized='table') }}

-- =====================================================================
-- mart_governance_audit
-- =====================================================================
-- Governance audit summary for DIM_PATIENT and baseline objects.
-- =====================================================================

with policy_columns as (

    select
        policy_name,
        policy_kind,
        ref_entity_name,
        ref_column_name

    from table(
        {{ env_var('SNOWFLAKE_DATABASE', 'HEALTHCARE_DB') }}.information_schema.policy_references(
            ref_entity_name => '{{ env_var("SNOWFLAKE_DATABASE", "HEALTHCARE_DB") }}.MARTS.DIM_PATIENT',
            ref_entity_domain => 'TABLE'
        )
    )

),

audit_checks as (

    -- =================================================================
    -- 1. DIM_PATIENT exists
    -- =================================================================

    select
        'dim_patient_exists' as audit_check,

        case
            when count(*) > 0 then 'PASS'
            else 'FAIL'
        end as pass_or_fail,

        'Found ' || count(*) ||
        ' table(s) named DIM_PATIENT in MARTS' as detail

    from {{ env_var('SNOWFLAKE_DATABASE', 'HEALTHCARE_DB') }}.information_schema.tables

    where table_schema = 'MARTS'
      and table_name = 'DIM_PATIENT'


    union all


    -- =================================================================
    -- 2. Masking policies attached
    -- =================================================================

    select
        'masking_policies_count_dim_patient' as audit_check,

        case
            when count(distinct ref_column_name) >= 7
                then 'PASS'
            else 'FAIL'
        end as pass_or_fail,

        'Found ' ||
        count(distinct ref_column_name) ||
        ' column(s) with masking policies (target: 7)' as detail

    from policy_columns

    where policy_kind = 'MASKING_POLICY'


    union all


    -- =================================================================
    -- 3. Row access policy attached
    -- =================================================================

    select
        'row_access_policy_attached_dim_patient' as audit_check,

        case
            when count(*) >= 1
                then 'PASS'
            else 'FAIL'
        end as pass_or_fail,

        'Found ' ||
        count(*) ||
        ' row access policy reference(s) (target: 1)' as detail

    from policy_columns

    where policy_kind = 'ROW_ACCESS_POLICY'


    union all


    -- =================================================================
    -- 4. Baseline views exist
    -- =================================================================

    select
        'baseline_views_exist' as audit_check,

        case
            when count(*) >= 2
                then 'PASS'
            else 'FAIL'
        end as pass_or_fail,

        'Found ' ||
        count(*) ||
        ' view(s) in BASELINE schema (target: 2)' as detail

    from {{ env_var('SNOWFLAKE_DATABASE', 'HEALTHCARE_DB') }}.information_schema.views

    where table_schema = 'BASELINE'


    union all


    -- =================================================================
    -- 5. Analyst cannot see real first name
    -- =================================================================

    select
        'analyst_cannot_see_real_first_name' as audit_check,

        'INFO' as pass_or_fail,

        'Verified manually via experiment runner - see META.experiment_query_log'
        as detail

)

select
    audit_check,
    pass_or_fail,
    detail,
    current_timestamp() as audited_at

from audit_checks

order by audit_check

