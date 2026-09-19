{{ config(materialized='view') }}

select
    procedure_id,
    patient_id,
    encounter_id,
    cpt_code,
    procedure_text,
    performed_at,
    cast(performed_at as date)   as performed_date,
    performer_provider,
    _loaded_at
from {{ source('raw', 'raw_procedures') }}
