{{ config(materialized='view') }}

select
    observation_id,
    patient_id,
    encounter_id,
    lower(observation_type)                as observation_type,
    code,
    code_text,
    value,
    unit,
    observation_timestamp,
    cast(observation_timestamp as date)    as observation_date,
    abnormal_flag,
    case when abnormal_flag in ('high','low','critical') then true else false end as is_abnormal,
    case when abnormal_flag = 'critical' then true else false end as is_critical,
    _loaded_at
from {{ source('raw', 'raw_observations') }}
