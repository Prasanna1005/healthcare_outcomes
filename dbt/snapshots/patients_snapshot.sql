{% snapshot patients_snapshot %}
    {{ config(
        target_database=env_var('SNOWFLAKE_DATABASE', 'HEALTHCARE_DB'),
        target_schema='SNAPSHOTS',
        unique_key='patient_id',
        strategy='check',
        check_cols=['address_state','insurance_plan','marital_status','is_deceased'],
        invalidate_hard_deletes=True
    ) }}
    select patient_id, mrn, first_name, last_name, date_of_birth,
           gender, race, ethnicity, marital_status,
           address_state, address_postal_code,
           insurance_plan, primary_language, is_deceased, deceased_date,
           updated_at
    from {{ ref('stg_patients') }}
{% endsnapshot %}
