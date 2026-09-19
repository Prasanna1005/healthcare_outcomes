{{ config(materialized='ephemeral') }}

with e as (select * from {{ ref('stg_encounters') }}),
     c as (select * from {{ ref('stg_conditions') }}),
     m as (select * from {{ ref('stg_medications') }})

select
    p.patient_id,
    count(distinct e.encounter_id)                              as total_encounters,
    sum(case when e.encounter_class = 'inpatient'  then 1 else 0 end) as inpatient_admissions,
    sum(case when e.encounter_class = 'emergency'  then 1 else 0 end) as ed_visits,
    sum(case when e.is_readmission_30d              then 1 else 0 end) as readmissions_30d,
    sum(e.length_of_stay_hours) / 24.0                            as total_los_days,
    sum(e.total_charges)                                          as total_charges,
    count(distinct c.icd10_code)                                  as unique_conditions,
    sum(case when c.is_active then 1 else 0 end)                  as active_conditions,
    count(distinct m.rxnorm_code)                                 as unique_medications,
    max(e.discharge_timestamp)                                    as last_encounter_at,
    min(e.admission_timestamp)                                    as first_encounter_at
from {{ ref('stg_patients') }} p
left join e on p.patient_id = e.patient_id
left join c on p.patient_id = c.patient_id
left join m on p.patient_id = m.patient_id
group by p.patient_id
