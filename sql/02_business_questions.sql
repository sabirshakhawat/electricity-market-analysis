-- EXAMPLE: Which states have the highest commercial prices in the latest month?
select state_name, price_cents_per_kwh
from analytics.retail_monthly
where sector_code = 'COM'
  and month_start = (select max(month_start) from analytics.retail_monthly)
order by price_cents_per_kwh desc;

-- EXERCISE 1: return the ten states with the largest commercial price YoY increase.
-- Start with analytics.market_trends and price_yoy_percent.

-- EXERCISE 2: compare commercial sales by calendar month across years.
-- Explain whether your result is a sum, average, or weighted measure.

-- EXERCISE 3: calculate state price volatility over twelve complete months.
-- Require twelve observations before comparing states.

-- EXERCISE 4: reconcile price against revenue / sales * 100.
-- Protect division by zero; investigate differences before choosing a tolerance.
