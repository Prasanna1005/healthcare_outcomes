{{ config(
    materialized='table',
    contract={'enforced': true},
    post_hook=[]
) }}

-- =====================================================================
-- dim_patient
-- =====================================================================
-- This table is the heart of the INTERVENTION arm of the experiment.
-- After dbt run, the on-run-end macro apply_masking_policies_to_dim_patient
-- attaches 7 masking policies + 1 row access policy to this table.
--
-- dbt contract enforcement guarantees the schema cannot drift; if a column
-- is added or removed, dbt run will fail rather than silently bypassing
-- policy attachment.
-- =====================================================================

select
    {{ dbt_utils.generate_surrogate_key(['patient_id']) }} as patient_sk,
    patient_id                          as patient_business_key,
    -- PHI columns — masking policies applied via on-run-end macro
    first_name,
    last_name,
    mrn,
    date_of_birth,
    phone_number,
    email,
    address_line1,
    address_postal_code,
    -- Non-PHI columns
    age_years,
    age_band,
    gender,
    race,
    ethnicity,
    marital_status,
    address_state,
    insurance_plan,
    primary_language,
    is_deceased,
    deceased_date,
    created_at,
    updated_at
from {{ ref('stg_patients') }}
