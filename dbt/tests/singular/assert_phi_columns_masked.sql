-- Verify all 8 PHI columns of DIM_PATIENT have masking policies attached.
-- This test should be run after dbt run because the on-run-end macro
-- applies the masking policies.

with phi_columns as (

    select 'FIRST_NAME' as column_name
    union all
    select 'LAST_NAME'
    union all
    select 'MRN'
    union all
    select 'DATE_OF_BIRTH'
    union all
    select 'PHONE_NUMBER'
    union all
    select 'EMAIL'
    union all
    select 'ADDRESS_LINE1'
    union all
    select 'ADDRESS_POSTAL_CODE'

),

attached as (

    select
        ref_column_name as column_name

    from table(
        {{ env_var('SNOWFLAKE_DATABASE', 'HEALTHCARE_DB') }}.information_schema.policy_references(
            ref_entity_name => '{{ env_var("SNOWFLAKE_DATABASE", "HEALTHCARE_DB") }}.MARTS.DIM_PATIENT',
            ref_entity_domain => 'TABLE'
        )
    )

    where policy_kind = 'MASKING_POLICY'

)

select
    p.column_name

from phi_columns p

left join attached a
    on upper(p.column_name) = upper(a.column_name)

where a.column_name is null