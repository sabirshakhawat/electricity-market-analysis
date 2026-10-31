-- PURPOSE: establish grain, coverage, and basic data quality before insights.
select * from analytics.retail_monthly limit 20;

select min(month_start), max(month_start), count(*) as rows,
       count(distinct state_code) as geographies
from analytics.retail_monthly;

-- YOUR TASK: count rows by sector; verify each state/month/sector is unique.
-- YOUR TASK: find missing or zero measures and decide what they mean.
