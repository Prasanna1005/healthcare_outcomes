{{ config(materialized='ephemeral') }}

with e as (select * from {{ ref('stg_encounters') }}),
     o as (
        select encounter_id,
               count(*)                                        as obs_count,
               sum(case when is_abnormal then 1 else 0 end)    as abnormal_count,
               sum(case when is_critical then 1 else 0 end)    as critical_count
          from {{ ref('stg_observations') }}
         group by encounter_id
     ),
     m as (
        select encounter_id, count(*) as medication_count, count(distinct rxnorm_code) as unique_medications
          from {{ ref('stg_medications') }}
         group by encounter_id
     ),
     c as (
        select encounter_id, count(*) as condition_count, count(distinct icd10_code) as unique_conditions
          from {{ ref('stg_conditions') }}
         group by encounter_id
     ),
     p as (
        select encounter_id, count(*) as procedure_count, count(distinct cpt_code) as unique_procedures
          from {{ ref('stg_procedures') }}
         group by encounter_id
     )

select
    e.*,
    coalesce(o.obs_count, 0)         as obs_count,
    coalesce(o.abnormal_count, 0)    as abnormal_obs_count,
    coalesce(o.critical_count, 0)    as critical_obs_count,
    coalesce(m.medication_count, 0)  as medication_count,
    coalesce(c.condition_count, 0)   as condition_count,
    coalesce(p.procedure_count, 0)   as procedure_count
from e
left join o on e.encounter_id = o.encounter_id
left join m on e.encounter_id = m.encounter_id
left join c on e.encounter_id = c.encounter_id
left join p on e.encounter_id = p.encounter_id
