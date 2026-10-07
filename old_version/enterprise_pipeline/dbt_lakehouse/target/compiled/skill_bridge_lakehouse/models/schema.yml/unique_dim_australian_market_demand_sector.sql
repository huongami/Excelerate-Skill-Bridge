
    
    

select
    sector as unique_field,
    count(*) as n_records

from "warehouse"."main"."dim_australian_market_demand"
where sector is not null
group by sector
having count(*) > 1


