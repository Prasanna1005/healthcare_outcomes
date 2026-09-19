
  
    



create or replace transient  table MARKETING_DB.dbt_ps.my_second_dbt_model
    
    
    
    
    as (
-- Use the `ref` function to select from other models

select *
from MARKETING_DB.dbt_ps.my_first_dbt_model
where id = 1
    )
;



  