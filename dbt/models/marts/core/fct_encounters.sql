{{
    config(
        materialized='incremental',
        unique_key='encounter_id',
        on_schema_change='append_new_columns',
        incremental_strategy='merge',
        cluster_by=['admission_date']
    )
}}

with src as (
    select * from {{ ref('int_encounter_enriched') }}
    {% if is_incremental() %}
        where _loaded_at >= (select coalesce(max(_loaded_at), '1900-01-01'::timestamp_ltz) from {{ this }})
    {% endif %}
)

select
    encounter_id,
    {{ dbt_utils.generate_surrogate_key(['patient_id']) }}    as patient_sk,
    patient_id                                                  as patient_business_key,
    {{ dbt_utils.generate_surrogate_key(['admission_date']) }} as date_sk,
    encounter_class,
    encounter_type,
    department,
    primary_diagnosis_code,
    primary_diagnosis_text,
    discharge_disposition,
    is_readmission_30d,
    admission_timestamp,
    discharge_timestamp,
    admission_date,
    length_of_stay_hours,
    length_of_stay_days,
    total_charges,
    obs_count,
    abnormal_obs_count,
    critical_obs_count,
    medication_count,
    condition_count,
    procedure_count,
    _loaded_at,
    current_timestamp() as _dbt_inserted_at
from src
