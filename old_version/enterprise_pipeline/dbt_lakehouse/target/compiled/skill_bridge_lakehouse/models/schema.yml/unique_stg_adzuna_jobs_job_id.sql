
    
    

select
    job_id as unique_field,
    count(*) as n_records

from "warehouse"."main"."stg_adzuna_jobs"
where job_id is not null
group by job_id
having count(*) > 1


