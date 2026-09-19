{{ config(materialized='view') }}

select
    patient_id,
    mrn,                          -- PHI
    first_name,                   -- PHI
    last_name,                    -- PHI
    date_of_birth,                -- PHI
    datediff('year', date_of_birth, '{{ var("analysis_as_of_date") }}'::date) as age_years,
    case
        when datediff('year', date_of_birth, '{{ var("analysis_as_of_date") }}'::date) < 18 then 'pediatric'
        when datediff('year', date_of_birth, '{{ var("analysis_as_of_date") }}'::date) < 65 then 'adult'
        else 'senior'
    end                                                 as age_band,
    gender,
    race,
    ethnicity,
    marital_status,
    address_line1,                -- PHI
    address_city,                 -- PHI
    address_state,
    address_postal_code,          -- PHI
    phone_number,                 -- PHI
    email,                        -- PHI
    insurance_id,                 -- PHI
    insurance_plan,
    primary_language,
    is_deceased,
    deceased_date,
    created_at,
    updated_at,
    _loaded_at
from {{ source('raw', 'raw_patients') }}
