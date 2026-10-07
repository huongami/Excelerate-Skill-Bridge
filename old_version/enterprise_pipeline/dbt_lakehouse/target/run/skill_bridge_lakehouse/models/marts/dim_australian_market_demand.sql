
    

    create  table
      "warehouse"."main"."dim_australian_market_demand__dbt_tmp"
  
    
    as (
      WITH job_agg AS (
    SELECT 
        sector,
        COUNT(*) as live_vacancies,
        ROUND(AVG(NULLIF(salary_min, 0)), 0) as avg_salary_min,
        ROUND(AVG(NULLIF(salary_max, 0)), 0) as avg_salary_max
    FROM "warehouse"."main"."stg_adzuna_jobs"
    GROUP BY sector
),
cand_agg AS (
    SELECT 
        sector,
        COUNT(*) as available_candidates,
        ROUND(AVG(years_of_experience), 1) as avg_experience_years
    FROM "warehouse"."main"."stg_international_resumes"
    GROUP BY sector
)
SELECT 
    COALESCE(j.sector, c.sector) as sector,
    COALESCE(j.live_vacancies, 0) as live_vacancies,
    COALESCE(c.available_candidates, 0) as available_candidates,
    COALESCE(c.avg_experience_years, 0.0) as avg_candidate_experience_yrs,
    COALESCE(j.avg_salary_min, 80000) as sector_avg_salary_min,
    COALESCE(j.avg_salary_max, 130000) as sector_avg_salary_max,
    ROUND(CAST(COALESCE(c.available_candidates, 0) AS FLOAT) / GREATEST(COALESCE(j.live_vacancies, 1), 1), 2) as talent_coverage_ratio,
    CURRENT_TIMESTAMP as dbt_computed_at
FROM job_agg j
FULL OUTER JOIN cand_agg c ON j.sector = c.sector
    );
    
  