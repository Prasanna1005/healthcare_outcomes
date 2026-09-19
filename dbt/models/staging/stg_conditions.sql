{{ config(materialized='view') }}

select
    condition_id,
    patient_id,
    encounter_id,
    code                              as icd10_code,
    code_text                         as condition_text,
    -- ICD-10 chapter (first letter is the disease category)
    left(code, 1)                     as icd10_chapter,
    onset_date,
    abated_date,
    lower(clinical_status)            as clinical_status,
    lower(verification_status)        as verification_status,
    case when clinical_status = 'active' then true else false end as is_active,
    _loaded_at
from {{ source('raw', 'raw_conditions') }}
