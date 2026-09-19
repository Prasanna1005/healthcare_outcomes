{{ config(materialized='table') }}

select
    department,
    encounter_class,
    primary_diagnosis_code,
    count(*)                                       as encounter_count,
    avg(length_of_stay_days)                       as avg_los_days,
    median(length_of_stay_days)                    as median_los_days,
    stddev(length_of_stay_days)                    as sd_los_days,
    min(length_of_stay_days)                       as min_los_days,
    max(length_of_stay_days)                       as max_los_days,
    avg(total_charges)                             as avg_charges,
    median(total_charges)                          as median_charges,
    sum(case when is_readmission_30d then 1 else 0 end) as readmissions,
    {{ safe_divide('sum(case when is_readmission_30d then 1 else 0 end)::float',
                   'count(*)') }}                    as readmission_rate
from {{ ref('fct_encounters') }}
group by 1, 2, 3
having count(*) >= 10
order by avg_los_days desc
