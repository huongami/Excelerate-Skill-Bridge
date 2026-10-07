
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select sector
from "warehouse"."main"."dim_australian_market_demand"
where sector is null



  
  
      
    ) dbt_internal_test