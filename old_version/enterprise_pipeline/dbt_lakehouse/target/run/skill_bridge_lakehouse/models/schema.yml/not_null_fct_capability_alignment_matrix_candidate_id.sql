
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select candidate_id
from "warehouse"."main"."fct_capability_alignment_matrix"
where candidate_id is null



  
  
      
    ) dbt_internal_test