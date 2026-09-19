{{ config(materialized='table') }}

-- For each inpatient encounter, compute readmission risk indicators.
-- This mart is the dissertation's clinical-analytics flagship output.

with inpatient as (
    select * from {{ ref('fct_encounters') }}
     where encounter_class = 'inpatient'
)

select
    e.encounter_id,
    e.patient_business_key                                          as patient_id,
    e.admission_date,
    e.length_of_stay_days,
    e.primary_diagnosis_code,
    e.primary_diagnosis_text,
    e.department,
    e.discharge_disposition,
    e.is_readmission_30d,
    e.total_charges,
    e.medication_count,
    e.condition_count,
    e.critical_obs_count,
    -- Risk score (rule-based, illustrative)
    least(100,
        (case when e.length_of_stay_days >= 7 then 25 else e.length_of_stay_days * 3 end)
        + (case when e.medication_count >= 5 then 20 else e.medication_count * 4 end)
        + (case when e.condition_count >= 3 then 20 else e.condition_count * 6 end)
        + (case when e.critical_obs_count >= 1 then 25 else 0 end)
        + (case when e.discharge_disposition in ('skilled_nursing','rehab') then 10 else 0 end)
    )                                                                as risk_score,
    case
        when (case when e.length_of_stay_days >= 7 then 25 else e.length_of_stay_days * 3 end)
           + (case when e.medication_count >= 5 then 20 else e.medication_count * 4 end)
           + (case when e.condition_count >= 3 then 20 else e.condition_count * 6 end)
           + (case when e.critical_obs_count >= 1 then 25 else 0 end)
           + (case when e.discharge_disposition in ('skilled_nursing','rehab') then 10 else 0 end) >= 70 then 'high'
        when (case when e.length_of_stay_days >= 7 then 25 else e.length_of_stay_days * 3 end)
           + (case when e.medication_count >= 5 then 20 else e.medication_count * 4 end)
           + (case when e.condition_count >= 3 then 20 else e.condition_count * 6 end)
           + (case when e.critical_obs_count >= 1 then 25 else 0 end) >= 40 then 'medium'
        else 'low'
    end                                                              as risk_band
from inpatient e
order by risk_score desc
