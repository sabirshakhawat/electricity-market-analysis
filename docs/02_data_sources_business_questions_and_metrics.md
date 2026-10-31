# Data Sources, Business Questions, and Metrics

## 1. Source Selection

The project will begin with two EIA API v2 routes.

### Source A: retail electricity sales

**Route:** `/v2/electricity/retail-sales/data/`

**Purpose:** analyze electricity market price and activity by month, geography, and customer sector.

The EIA describes this source as electricity sales to ultimate customers by state and sector. Available measures include:

- `price`: average price in cents per kilowatthour.
- `sales`: electricity sold, reported in million kilowatthours in the API metadata.
- `revenue`: revenue, reported in million dollars.
- `customers`: number of ultimate customers.

Primary dimensions include:

- `period`: monthly observation such as `2025-01`.
- `stateid` and `stateDescription`: state or EIA geography.
- `sectorid` and `sectorName`: residential, commercial, industrial, transportation, other, or all sectors.

Official references:

- [EIA API technical documentation](https://www.eia.gov/opendata/documentation.php)
- [EIA retail-sales browser](https://www.eia.gov/opendata/browser/electricity/retail-sales)
- [EIA electricity data](https://www.eia.gov/electricity/data.php)

### Source B: electric power operations

**Route:** `/v2/electricity/electricity-power-operational-data/data/`

**Purpose:** analyze monthly electricity generation by state, producer sector, and energy source.

This is a distinct dataset with a different grain from retail sales. Its source is EIA Form EIA-923. Exact metadata, measures, facets, and units will be inspected programmatically before we write the production extractor.

Expected analytical use:

- Net generation by state and month.
- Generation by energy source.
- Renewable, fossil, nuclear, and other groupings.
- Generation share and change in share over time.

Official references:

- [EIA Open Data electricity routes](https://www.eia.gov/opendata/)
- [EIA API technical documentation](https://www.eia.gov/opendata/documentation.php)

### Why source metadata is retrieved first

We will not hard-code assumptions solely from a tutorial. Before extracting data, we will request the route's metadata and inspect:

- Available frequencies.
- Facet names and valid facet values.
- Measure names and units.
- Available start and end periods.
- Default date format.

This teaches an important API habit: interrogate the source contract before relying on it.

## 2. Grain: the Most Important Modeling Concept

The **grain** states what one row represents.

Proposed raw retail-sales grain:

```text
one row per reporting period + EIA geography + customer sector
```

Proposed generation grain:

```text
one row per reporting period + state + producer sector + energy source
```

These two fact tables must not be directly joined before generation is aggregated to the intended state-month level. Otherwise, one retail row may match multiple fuel rows and multiply retail measures.

### Example of an unsafe join

Suppose Colorado commercial retail sales has one row for January, while Colorado generation has ten fuel rows for January. Joining only on state and month repeats the retail-sales value ten times.

### Safe pattern

1. Aggregate generation into a state-month market model or generation-share model.
2. Preserve fuel-level data in a separate fact or mart.
3. Join only models whose grains are compatible.
4. Test the intended unique key after every major transformation.

## 3. Business Questions

### Theme A: price level and trend

1. Which states have the highest and lowest average commercial electricity prices?
2. Which states have experienced the largest year-over-year commercial price changes?
3. How have residential, commercial, and industrial price trends differed?
4. Which states consistently remain above or below the national comparison value?
5. Are recent price movements unusual relative to each state's history?

### Theme B: volatility and market-screening risk

6. Which states have the most volatile monthly commercial electricity prices?
7. Which markets combine high current prices with high volatility?
8. Which states show sustained price acceleration rather than a single-month spike?
9. How stable are state rankings over rolling twelve-month windows?

### Theme C: demand and market activity

10. Which states have the largest commercial electricity sales?
11. Which states show sustained growth or decline in commercial sales?
12. How seasonal are monthly sales in different states and sectors?
13. How have customer counts changed relative to sales?
14. Where is estimated electricity usage per customer increasing or decreasing?

### Theme D: revenue and unit reconciliation

15. How do revenue and sales trends compare?
16. Does the price implied by reported revenue and sales reconcile with the reported average price?
17. Which state-month-sector records have missing, zero, or inconsistent measures?

The reconciliation question is both analytical and a data-quality control.

### Theme E: generation mix

18. What percentage of each state's generation comes from renewable, fossil, nuclear, and other sources?
19. Which states have experienced the largest change in renewable generation share?
20. Which fuel types dominate generation in each state?
21. Which states have diverse versus concentrated generation mixes?
22. How do price trends and generation-mix trends move together, without claiming causation?

## 4. Metric Dictionary

### Source measures

| Metric | Definition | Grain | Unit | Notes |
|---|---|---|---|---|
| Average retail price | EIA average price to ultimate customers | Month, geography, sector | cents/kWh | Use EIA value directly |
| Electricity sales | Electricity sold to ultimate customers | Month, geography, sector | million kWh | Confirm unit from live metadata |
| Revenue | Revenue from sales to ultimate customers | Month, geography, sector | million USD | Nominal dollars unless separately adjusted |
| Customers | Ultimate customer count | Month, geography, sector | count | A customer is not necessarily a person |
| Net generation | EIA generation measure | Month, state, producer sector, fuel | verify from metadata | Exact unit validated during source discovery |

### Derived retail metrics

#### Year-over-year price change

```text
(current price / price 12 months earlier - 1) × 100
```

Use a twelve-month comparison for monthly data so seasonality has less influence than in a one-month comparison.

#### Month-over-month price change

```text
(current price / prior-month price - 1) × 100
```

Useful for detecting recent movement, but not sufficient alone for business conclusions.

#### Rolling twelve-month average price

```text
average of the current and previous 11 monthly prices
```

This smooths short-term variation and supports more stable state comparisons.

#### Twelve-month price volatility

Initial definition:

```text
sample standard deviation of monthly price over a rolling 12-month window
```

Optional normalized definition:

```text
rolling standard deviation / rolling average
```

The normalized version supports comparison between high-price and low-price states.

#### Estimated monthly usage per customer

If sales are in million kWh:

```text
(sales × 1,000,000) / customers
```

This is an aggregate ratio, not an individual customer's measured consumption.

#### Revenue per customer

If revenue is in million dollars:

```text
(revenue × 1,000,000) / customers
```

#### Implied price reconciliation

Given million dollars and million kWh:

```text
(revenue / sales) × 100 = implied cents per kWh
```

Compare the implied result to the EIA `price` field within a documented tolerance. Small differences may arise from rounding or source methodology.

### Derived generation metrics

#### Fuel generation share

```text
fuel generation / total state generation for the same month
```

#### Renewable generation share

```text
generation from fuels classified as renewable / total classified generation
```

The renewable classification must exist in a documented seed or mapping table, not in scattered `CASE` statements.

#### Generation concentration

Potential later metric:

```text
sum of squared fuel shares
```

This resembles a concentration index: higher values indicate that a state's generation is dominated by fewer fuel categories.

## 5. Dimensional Model

### Dimensions

#### `dim_date`

- Month start date.
- Calendar year, quarter, month number, and month name.
- Year-month label.
- Flags for latest complete month and rolling windows.

#### `dim_geography`

- EIA geography code.
- Geography name.
- Geography type: state, District of Columbia, national, Census region, or other aggregate.
- State abbreviation where applicable.
- Inclusion flag for primary state analysis.

#### `dim_sector`

- EIA sector code.
- Sector name.
- Display order.
- Primary-analysis flag.

Important: `ALL` is an already aggregated sector. Never sum `ALL` together with residential, commercial, industrial, transportation, and other rows.

#### `dim_energy_source`

- EIA fuel/source code.
- Source name.
- Parent category: renewable, fossil, nuclear, other, or unclassified.
- Renewable flag.
- Display order.

### Facts

#### `fct_retail_sales_monthly`

Grain: one row per month, geography, and sector.

Measures:

- Average retail price.
- Sales.
- Revenue.
- Customers.
- Ingestion and source metadata needed for lineage.

#### `fct_generation_monthly`

Grain: one row per month, state, producer sector, and energy source.

Measures:

- Net generation.
- Any additional source measure explicitly approved after metadata inspection.

### Marts

#### `mart_state_market_monthly`

One row per state, month, and selected customer sector, with retail measures and reusable time-series comparisons.

#### `mart_state_price_scorecard`

One row per state and latest reporting window, with current price, rolling average, growth, volatility, and rank.

#### `mart_state_generation_mix_monthly`

One row per state, month, and energy category or source, with generation and share.

#### `mart_state_market_overview`

A carefully constructed dashboard-facing model combining compatible state-month metrics. It will not join different grains carelessly.

## 6. Data-Quality Rules

### Critical blocking tests

- Unique retail key: period + geography + sector.
- Unique generation key at the declared source grain.
- Required keys are not null.
- Fact foreign keys match dimension keys.
- Price, sales, revenue, customers, and generation are not negative unless the source documentation explicitly permits a case.
- Pagination count matches the API's reported total for the request.
- No unclassified state-like geography enters state-only marts.
- No unknown energy source enters published category totals without being surfaced.
- Implied and reported retail prices reconcile within the agreed tolerance for valid rows.

### Warning-level tests

- Latest period is within the expected publication lag.
- A state-month has every expected primary sector.
- Month-over-month row counts do not change unexpectedly.
- Null or zero measure rates do not spike.
- Newly observed facet values are reported for review.

## 7. Dashboard Concept

### Page 1: market overview

- Latest commercial price by state.
- Year-over-year change.
- Rolling volatility.
- State ranking and map.
- Selected-state historical trend.

### Page 2: sector comparison

- Residential, commercial, and industrial trends.
- Price and sales comparisons.
- Estimated usage and revenue per customer.

### Page 3: generation mix

- Fuel/category share by state.
- Change in renewable share.
- Generation composition over time.

### Page 4: data freshness and quality

- Latest source month.
- Latest successful pipeline run.
- Tableau refresh timestamp.
- Rows loaded and tested.
- Plain-language metric definitions and limitations.

## 8. Deferred Weather Enrichment

Weather is a natural extension because electricity sales and demand are seasonal. It is deferred so we can first prove the single-source pipeline.

When added, the weather work will require explicit design decisions:

- Select weather stations or gridded data appropriate for state aggregation.
- Define population-weighted, station-weighted, or simple state temperature measures.
- Calculate heating-degree and cooling-degree measures.
- Align weather dates and EIA reporting months.
- Avoid interpreting unadjusted demand changes as business growth when weather may explain them.

The future question becomes not merely “did sales rise?” but “did sales rise beyond what temperature conditions would normally suggest?”

