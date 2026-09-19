{{ config(materialized='table') }}

with date_spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2024-01-01' as date)",
        end_date="cast('2026-12-31' as date)"
    ) }}
)

select
    date_day,
    {{ dbt_utils.generate_surrogate_key(['date_day']) }}      as date_sk,
    extract(year from date_day)                               as year_number,
    extract(quarter from date_day)                            as quarter_number,
    extract(month from date_day)                              as month_number,
    monthname(date_day)                                       as month_name,
    extract(week from date_day)                               as iso_week_number,
    extract(day from date_day)                                as day_of_month,
    dayname(date_day)                                         as day_name,
    extract(dow from date_day)                                as day_of_week_number,
    case when extract(dow from date_day) in (0, 6) then true else false end as is_weekend
from date_spine
