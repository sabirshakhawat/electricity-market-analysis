# Project Charter and Architecture

## 1. Objective

Build a maintainable analytics pipeline that turns recurring EIA electricity data into tested market-comparison models, documented analysis, and a Tableau dashboard.

The project must demonstrate the full lifecycle:

```text
source data -> ingestion -> storage -> transformation -> testing
            -> analysis -> dashboard -> controlled refresh -> next run
```

A polished chart is not enough. The portfolio value comes from showing that the chart is supplied by a reproducible and dependable data system.

## 2. Business Framing

### Intended user

An analyst supporting a multi-state commercial operator, energy-procurement team, facilities group, or site-selection team.

### Business problem

Electricity markets vary substantially across states and over time. A team evaluating locations or managing facilities needs a repeatable way to identify:

- Markets with high or rapidly increasing commercial electricity prices.
- Markets with unusual price volatility.
- Changes in electricity sales and customer demand.
- Differences between residential, commercial, and industrial sectors.
- Markets whose generation mixes are changing.
- States that should receive deeper investigation rather than an automatic investment recommendation.

### Decision supported

The project produces a **market-screening and monitoring tool**, not a complete site-selection model. It helps a stakeholder decide where to investigate energy cost and market risk in more detail.

### What the project must not claim

- EIA average prices are not guaranteed tariffs for a specific facility.
- State averages do not capture every utility, rate class, contract, tax, or demand charge.
- Correlation does not establish that generation mix causes retail price changes.
- The dashboard is decision support, not a final investment, regulatory, or procurement recommendation.

## 3. High-Level Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│ EIA Open Data API v2                                         │
│  • monthly retail sales                                      │
│  • monthly power operations / generation                     │
└──────────────────────────────┬───────────────────────────────┘
                               │ HTTPS + JSON
                               v
┌──────────────────────────────────────────────────────────────┐
│ Python ingestion                                              │
│  • build request parameters                                  │
│  • authenticate with API key                                 │
│  • paginate, retry, validate, and log                        │
│  • preserve source values and ingestion metadata             │
└──────────────────────────────┬───────────────────────────────┘
                               │ append/upsert
                               v
┌──────────────────────────────────────────────────────────────┐
│ PostgreSQL raw layer                                          │
│  • raw.eia_retail_sales                                      │
│  • raw.eia_generation                                        │
│  • raw.ingestion_runs                                        │
└──────────────────────────────┬───────────────────────────────┘
                               │ dbt sources
                               v
┌──────────────────────────────────────────────────────────────┐
│ dbt staging and intermediate layer                            │
│  • cast, rename, standardize, deduplicate                     │
│  • classify geographies, sectors, and fuels                  │
│  • calculate reusable time-series fields                     │
└──────────────────────────────┬───────────────────────────────┘
                               │ tests must pass
                               v
┌──────────────────────────────────────────────────────────────┐
│ dbt analytics layer                                           │
│  • dimensions and facts                                      │
│  • state-month market mart                                   │
│  • price trend, volatility, and generation-mix marts         │
└───────────────┬───────────────────────────────┬──────────────┘
                │                               │
                v                               v
┌────────────────────────────┐   ┌─────────────────────────────┐
│ SQL/Python analysis        │   │ Tableau dashboard           │
│ validation and exploration │   │ curated marts only          │
└────────────────────────────┘   └──────────────┬──────────────┘
                                               │ refresh verified
                                               v
                                ┌─────────────────────────────┐
                                │ Run status and next schedule│
                                └─────────────────────────────┘
```

## 4. Why the Layers Are Separate

### Source/API layer

The API is someone else's system. Its response format, release schedule, and availability are outside our control. We treat it as an external dependency and preserve enough source detail to diagnose changes.

### Python ingestion layer

Python is responsible for network and JSON work because it can make HTTP requests, handle pagination and retries, validate responses, and communicate with PostgreSQL. It should not contain dashboard-specific business logic.

### Raw storage layer

Raw tables create a boundary between an unstable external source and repeatable internal transformations. If a dbt model changes, we should normally be able to rebuild it from raw data without calling the API again.

### dbt transformation layer

dbt expresses warehouse transformations as version-controlled SQL models. It provides dependencies, tests, documentation, and lineage. Business definitions should live here when they can be expressed clearly in SQL.

### Analysis layer

SQL validates and explores warehouse results. Python is used when statistical analysis or specialized libraries add value. Analysis consumes curated data; it does not silently become a second transformation pipeline.

### Tableau layer

Tableau visualizes stable analytics models. It should not perform foundational cleaning or invent alternate KPI definitions that disagree with dbt.

### Orchestration layer

The orchestrator controls sequence and failure behavior. It does not replace Python, PostgreSQL, dbt, or Tableau; it tells those components when to run.

## 5. Data Flow for One Scheduled Run

1. The scheduler starts a run and creates a unique `run_id`.
2. Python determines the requested date window.
3. Python requests one page of EIA JSON data.
4. The response status and structure are validated.
5. Additional pages are requested until all expected rows are received.
6. Rows are loaded into raw PostgreSQL tables using a repeat-safe key.
7. Load counts and run metadata are recorded.
8. dbt builds staging and intermediate models.
9. dbt builds facts, dimensions, and marts.
10. Critical dbt tests run.
11. If a critical test fails, the workflow stops and Tableau retains its last successful data.
12. If tests pass, Tableau refresh is triggered.
13. The refresh result is checked.
14. The pipeline records success or failure and waits for the next schedule.

## 6. Failure Boundaries

| Failure | Expected behavior | Why |
|---|---|---|
| Missing API key | Stop before making a request | Configuration errors are not transient |
| API timeout | Retry with a delay and limit | A network problem may be temporary |
| HTTP 429/rate limit | Back off, then retry | Immediate repeated calls make the problem worse |
| Unexpected JSON structure | Save useful context and stop | Loading malformed data could corrupt downstream models |
| Partial pagination | Do not mark extraction successful | A partial dataset can produce misleading metrics |
| Raw database unavailable | Retry appropriately; do not run dbt | Transformations cannot use data that was not loaded |
| Duplicate raw keys | Fail or merge according to the load contract | Silent duplicates inflate totals |
| Critical dbt test fails | Stop before Tableau refresh | Invalid analytical data must not be published |
| Tableau refresh fails | Record pipeline publication failure | Upstream success does not prove users received new data |

## 7. Initial Scope Boundaries

### Included

- EIA API v2 JSON responses.
- Monthly state-level retail sales.
- Residential, commercial, and industrial sectors.
- Price, sales, revenue, and customer counts.
- Monthly state-level generation by source in the second vertical slice.
- PostgreSQL, dbt, SQL/Python analysis, orchestration, and Tableau.
- Backfill and repeat monthly refresh behavior.

### Deferred

- Weather and temperature enrichment.
- Utility-level tariffs or individual facility bills.
- Forecasting and machine learning.
- Hourly balancing-authority data.
- Plant-level operations.
- Cloud deployment.
- Complex streaming infrastructure.

Deferring these items protects the learning goal: first build one complete, understandable pipeline.

## 8. Technology Decision Record

| Decision | Choice | Reason |
|---|---|---|
| Source | EIA Open Data API v2 | Authoritative, recurring, documented public energy data |
| Ingestion | Python | Appropriate for APIs, JSON, validation, and database loading |
| Database | PostgreSQL | Widely used relational database with strong SQL support |
| Transformation | dbt Core + PostgreSQL adapter | Teaches modular SQL, tests, lineage, and documentation |
| Analysis | SQL first; Python when useful | Keeps warehouse logic visible while allowing richer analysis |
| Visualization | Tableau | Target presentation tool and marketable analyst skill |
| Orchestration | Airflow after manual pipeline works | Strong DAG demonstration without making the first step too complex |
| Version control | Git and GitHub | Reproducibility, collaboration, and portfolio presentation |
| Environment secrets | `.env` locally, never committed | Keeps the EIA key and credentials out of source control |

## 9. Success Criteria

The project is complete when:

- A new contributor can understand the architecture from the repository.
- A historical backfill loads repeatably without duplicate logical records.
- A monthly incremental run retrieves and processes new or revised periods.
- Raw records can be traced to an ingestion run.
- dbt models have declared grains and documented metrics.
- Critical uniqueness, null, relationship, range, and reconciliation tests pass.
- The dashboard reads curated marts rather than raw tables.
- An upstream failure prevents Tableau refresh.
- A successful run records its completion and dashboard refresh time.
- The README explains findings, limitations, and how to reproduce the project.

