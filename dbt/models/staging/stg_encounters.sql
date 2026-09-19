{{ config(materialized='view') }}

select
    encounter_id,
    patient_id,
    lower(encounter_class)            as encounter_class,
    encounter_type,
    admission_timestamp,
    discharge_timestamp,
    length_of_stay_hours,
    cast(length_of_stay_hours / 24.0 as number(10, 2)) as length_of_stay_days,
    department,
    primary_diagnosis_code,
    primary_diagnosis_text,
    discharge_disposition,
    is_readmission_30d,
    total_charges,
    cast(admission_timestamp as date) as admission_date,
    extract(year  from admission_timestamp) as admission_year,
    extract(month from admission_timestamp) as admission_month,
    created_at,
    updated_at,
    _loaded_at
from {{ source('raw', 'raw_encounters') }}
