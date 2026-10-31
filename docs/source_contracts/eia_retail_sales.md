# EIA Retail Sales Source Contract

## 1. Contract Status

| Field | Value |
|---|---|
| Source | U.S. Energy Information Administration (EIA) Open Data API v2 |
| Dataset | Electricity Sales to Ultimate Customers |
| Metadata route | `/v2/electricity/retail-sales/` |
| Data route | `/v2/electricity/retail-sales/data/` |
| Authentication | EIA API key supplied as the `api_key` query parameter |
| Initial inspection date | 2026-10-10 |
| Contract status | Draft: core metadata and facet values verified; data rows not yet inspected |

This contract records what the source supplies, how the project intends to use it, and which assumptions must be validated before data is loaded.

## 2. Source Purpose

EIA describes this dataset as electricity sales to ultimate customers by state and customer sector. It contains customer counts, average price, revenue, and electricity sales.

EIA identifies the source forms as:

- EIA-826
- EIA-861
- EIA-861M

The project will use this source to compare state electricity markets by price, sales, revenue, customer activity, growth, seasonality, and volatility.

## 3. Observed Metadata Response

The metadata request returned HTTP `200` and a top-level JSON object containing:

```text
response
request
apiVersion
ExcelAddInVersion
```

The nested `response` object contained:

```text
id
name
description
frequency
facets
data
startPeriod
endPeriod
defaultDateFormat
defaultFrequency
```

## 4. Availability and Time

| Property | Observed value |
|---|---|
| Start period | `2001-01` |
| End period at inspection | `2026-07` |
| Default date format | `YYYY-MM` |
| Default frequency | `monthly` |

Supported frequencies observed from metadata:

| Frequency ID | Meaning | Period format |
|---|---|---|
| `monthly` | One observation per month | `YYYY-MM` |
| `quarterly` | One observation every three months | `YYYY-"Q"Q` |
| `annual` | One observation per calendar year | `YYYY` |

### Project decision

The initial pipeline will explicitly request `monthly` data. We will not rely on the API default, even though the observed default is monthly. Explicit parameters make the extraction contract easier to understand and protect against unnoticed default changes.

The source's `endPeriod` is not assumed to equal the current calendar month. EIA publication lag and revisions are expected.

## 5. Measures

| API field | EIA alias | Source unit | Planned internal name |
|---|---|---|---|
| `revenue` | Revenue from Sales to Ultimate Customers | million dollars | `revenue_million_dollars` |
| `sales` | Megawatt-hours Sold to Ultimate Customers | million kilowatt-hours | `sales_million_kwh` |
| `price` | Average Price of Electricity to Ultimate Customers | cents per kilowatt-hour | `price_cents_per_kwh` |
| `customers` | Number of Ultimate Customers | number of customers | `customers` |

### Project decisions

- Request all four measures during the initial retail-sales extraction.
- Preserve source values and source units in the raw layer.
- Convert numeric strings to appropriate numeric types only after source-shape validation.
- Do not treat `customers` as a count of people; it is an EIA customer count.
- Do not treat state average price as a guaranteed rate for a specific building or utility account.

### Future reconciliation rule

Because revenue is reported in million dollars and sales in million kilowatt-hours, an implied price can be calculated as:

```text
(revenue / sales) × 100 = implied cents per kilowatt-hour
```

The implied result will later be compared with the reported `price` field using a documented tolerance. Small differences may occur due to rounding or source methodology.

## 6. Facets

The metadata response contains a `facets` list. Each list item is a dictionary whose required keys are discovered from the live response before being used.

Verified project-relevant facets:

| Facet ID | Expected meaning | Verification status |
|---|---|---|
| `stateid` | State or EIA geographic aggregate | 62 values verified |
| `sectorid` | Ultimate-customer sector | 6 values verified |

Facet-definition routes:

```text
/v2/electricity/retail-sales/facet/stateid/
/v2/electricity/retail-sales/facet/sectorid/
```

### Sector decisions

Valid sector values returned by EIA:

| Sector ID | Name | Initial analytical use |
|---|---|---|
| `RES` | residential | Include |
| `COM` | commercial | Include; initial bounded request |
| `IND` | industrial | Include |
| `TRA` | transportation | Preserve; defer from initial comparison |
| `OTH` | other | Preserve; defer from initial comparison |
| `ALL` | all sectors | Preserve; never combine with component-sector totals |

- Primary analysis sectors: residential, commercial, and industrial.
- Preserve other valid source sectors in the raw layer unless later scope decisions exclude them from extraction.
- Preserve the `ALL` sector if returned, but never sum it together with its component sectors.
- Use valid sector values returned by the facet endpoint rather than inventing or silently accepting codes.

### Geography decisions

The state facet returned 62 values:

- 50 U.S. states.
- District of Columbia (`DC`).
- U.S. total (`US`).
- Ten EIA/Census regional aggregates.

Verified non-state aggregate values:

| Geography ID | Name | Classification |
|---|---|---|
| `US` | U.S. Total | national |
| `NEW` | New England | region |
| `MAT` | Middle Atlantic | region |
| `ENC` | East North Central | region |
| `WNC` | West North Central | region |
| `SAT` | South Atlantic | region |
| `ESC` | East South Central | region |
| `WSC` | West South Central | region |
| `MTN` | Mountain | region |
| `PACC` | Pacific Contiguous | region |
| `PACN` | Pacific Noncontiguous | region |

The remaining 51 values are the 50 states plus District of Columbia.

- Primary state analysis: the 50 states plus District of Columbia.
- Preserve EIA national and regional aggregate values in raw data when collected.
- Exclude national and regional aggregates from state rankings and state maps.
- Maintain an explicit geography classification rather than assuming that every `stateid` value is a state.

## 7. Draft Row Grain

The expected retail-sales observation grain is:

```text
one row per reporting period + EIA geography + customer sector
```

The candidate logical key is:

```text
period + stateid + sectorid
```

This key remains draft until an actual bounded data response is inspected and tested for uniqueness.

## 8. Initial Extraction Scope

The first bounded learning request will use:

```text
frequency: monthly
geography: one selected state
sector: commercial
period: one complete historical year
measures: revenue, sales, price, customers
sort: period ascending
```

Expected result: approximately 12 observations, one for each month. The returned count must be inspected rather than assumed.

The production scope will expand only after the bounded request is understood and validated.

## 9. Source-Quality Observations

- The dataset description contained HTML-encoded whitespace such as `&#x20;`.
- API measures may be returned as strings and require explicit numeric conversion.
- The latest available period may lag the current month.
- Facet values may include aggregates that are inappropriate for state-only analysis.
- The `ALL` sector can cause double counting if combined with component sectors.
- Valid source codes may change, so unknown geography or sector values must be surfaced rather than silently discarded.

## 10. Required Validation Before Raw Loading

The ingestion layer must eventually verify:

- HTTP request succeeds.
- JSON contains a `response` object.
- Data requests contain `response.data` as a list.
- Required row fields exist.
- Period follows the expected monthly format.
- Measure values are numeric or explicitly missing.
- Retrieved row count agrees with the API-reported total.
- Candidate grain fields are not null.
- Candidate logical key is unique for the requested slice.
- Newly observed sector or geography values are reported.

## 11. Open Verification Items

- [x] Record the live `facets` list and each facet's keys.
- [x] Retrieve and record every valid `sectorid` value.
- [x] Retrieve and record every valid `stateid` value.
- [x] Classify geography values as state, District of Columbia, national, or region.
- [x] Confirm quarterly and annual format values from live metadata.
- [ ] Inspect one actual monthly data row and record all returned fields.
- [ ] Test uniqueness of `period + stateid + sectorid` on a bounded request.
- [ ] Confirm missing-value and zero-value behavior.
- [ ] Determine the production backfill start period.

## 12. Downstream Architectural Use

This contract informs:

- Python request parameters and response validation.
- Raw PostgreSQL column definitions and logical keys.
- `dim_geography` and `dim_sector` classifications.
- dbt accepted-value, uniqueness, not-null, and reconciliation tests.
- Tableau filters, rankings, and metric definitions.
- Airflow failure gates before dashboard refresh.
