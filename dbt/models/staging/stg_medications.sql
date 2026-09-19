{{ config(materialized='view') }}

select
    medication_request_id,
    patient_id,
    encounter_id,
    rxnorm_code,
    medication_name,
    dosage_text,
    lower(route)                  as route,
    prescribed_at,
    cast(prescribed_at as date)   as prescribed_date,
    days_supply,
    refills_allowed,
    _loaded_at
from {{ source('raw', 'raw_medications') }}
