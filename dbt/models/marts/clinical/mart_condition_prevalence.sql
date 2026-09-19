{{ config(materialized='table') }}

with c as (select * from {{ ref('stg_conditions') }}),
     p as (select count(*) as total_patients from {{ ref('stg_patients') }})

select
    c.icd10_code,
    c.condition_text,
    c.icd10_chapter,
    count(distinct c.patient_id)                                       as affected_patients,
    count(*)                                                            as total_diagnoses,
    sum(case when c.is_active then 1 else 0 end)                       as active_diagnoses,
    {{ safe_divide('count(distinct c.patient_id)::float',
                   '(select total_patients from p)') }}                  as prevalence_rate
from c
group by 1, 2, 3
having count(distinct c.patient_id) >= 50
order by affected_patients desc
