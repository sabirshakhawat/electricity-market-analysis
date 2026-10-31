-- Run by refresh_workspace.py after validating a complete API extraction.
create schema if not exists analytics;
create or replace view analytics.retail_monthly as
select
    strptime(period, '%Y-%m')::date as month_start,
    stateid as state_code,
    stateDescription as state_name,
    sectorid as sector_code,
    sectorName as sector_name,
    price::decimal(18,5) as price_cents_per_kwh,
    sales::decimal(18,5) as sales_million_kwh,
    revenue::decimal(18,5) as revenue_million_dollars,
    customers::bigint as customers
from raw.retail_sales;

create or replace view analytics.market_trends as
with history as (
    select *,
        lag(price_cents_per_kwh) over (
            partition by state_code, sector_code order by month_start
        ) as previous_month_price
    from analytics.retail_monthly
)
select h.*,
    y.price_cents_per_kwh as previous_year_price,
    100.0 * (h.price_cents_per_kwh / nullif(y.price_cents_per_kwh, 0) - 1)
        as price_yoy_percent,
    h.sales_million_kwh * 1000000.0 / nullif(h.customers, 0)
        as usage_kwh_per_customer,
    h.revenue_million_dollars * 1000000.0 / nullif(h.customers, 0)
        as revenue_dollars_per_customer
from history h
left join analytics.retail_monthly y
    on h.state_code = y.state_code
    and h.sector_code = y.sector_code
    and h.month_start = y.month_start + interval '1 year';
