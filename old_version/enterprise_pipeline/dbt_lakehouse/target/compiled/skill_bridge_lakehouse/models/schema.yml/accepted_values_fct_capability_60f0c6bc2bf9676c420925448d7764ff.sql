
    
    

with all_values as (

    select
        match_tier as value_field,
        count(*) as n_records

    from "warehouse"."main"."fct_capability_alignment_matrix"
    group by match_tier

)

select *
from all_values
where value_field not in (
    'Direct Industry Alignment','Transferable Cross-Sector Capability'
)


