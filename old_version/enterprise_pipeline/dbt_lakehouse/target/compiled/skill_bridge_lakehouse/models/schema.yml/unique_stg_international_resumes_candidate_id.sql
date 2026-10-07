
    
    

select
    candidate_id as unique_field,
    count(*) as n_records

from "warehouse"."main"."stg_international_resumes"
where candidate_id is not null
group by candidate_id
having count(*) > 1


