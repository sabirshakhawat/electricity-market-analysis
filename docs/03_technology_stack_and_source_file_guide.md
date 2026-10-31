# Technology Stack and Source-File Guide

## 1. Stack Overview

| Component | Initial choice | Responsibility | Does not own |
|---|---|---|---|
| Source | EIA API v2 | Publish electricity data and metadata | Our pipeline reliability |
| Python | Python 3.12+ | API, JSON, validation, loading, utility scripts | Warehouse business modeling |
| HTTP client | `requests` | Send requests and read responses | Retries or validation by itself |
| Configuration | environment variables + `python-dotenv` locally | Keep credentials outside code | Secret rotation in production |
| Database | PostgreSQL | Persist raw and modeled data | Calling the API |
| Database driver | `psycopg` | Connect Python to PostgreSQL | Analytical model definitions |
| Transformation | dbt Core + `dbt-postgres` | SQL models, tests, lineage, docs | Network ingestion |
| Testing | `pytest` + dbt tests | Test Python behavior and warehouse data | Manual exploration |
| Analysis | SQL and Jupyter/Python | Validate findings and perform suitable analysis | Production ingestion logic |
| Orchestration | Airflow, introduced later | Schedule tasks and enforce dependencies | Performing transformations itself |
| Visualization | Tableau | Present curated metrics and findings | Foundational data cleaning |
| Version control | Git/GitHub | History, review, reproducibility | Secret storage |

## 2. Why We Introduce Tools Gradually

The final architecture contains several tools, but installing and debugging everything at once would hide the concepts we are trying to learn.

We will progress through these operating modes:

1. **Observe:** make one API request and inspect JSON.
2. **Modularize:** place request, validation, and transformation into small Python functions.
3. **Persist:** load repeatable raw records into PostgreSQL.
4. **Model:** build and test dbt models manually.
5. **Publish:** connect Tableau to curated marts.
6. **Automate:** use Airflow to run the already-understood commands.

Airflow is intentionally late. An orchestrator should automate a working process, not disguise an unfinished one.

## 3. Planned Repository Structure

```text
eia-electricity-market-analysis/
├── README.md
├── .gitignore
├── .env.example
├── pyproject.toml
├── docker-compose.yml                  # added when PostgreSQL is introduced
├── Makefile                            # optional friendly command shortcuts
│
├── config/
│   └── project.yml
│
├── src/
│   └── eia_pipeline/
│       ├── __init__.py
│       ├── config.py
│       ├── logging_config.py
│       ├── cli.py
│       ├── eia_client.py
│       ├── pagination.py
│       ├── validators.py
│       ├── records.py
│       ├── database.py
│       ├── load_retail_sales.py
│       ├── load_generation.py
│       └── tableau_refresh.py
│
├── sql/
│   ├── bootstrap/
│   │   ├── 001_create_schemas.sql
│   │   ├── 002_create_raw_tables.sql
│   │   └── 003_create_ingestion_runs.sql
│   └── analysis/
│       ├── validate_retail_metrics.sql
│       ├── market_questions.sql
│       └── dashboard_reconciliation.sql
│
├── dbt_electricity/
│   ├── dbt_project.yml
│   ├── packages.yml
│   ├── models/
│   │   ├── sources/
│   │   │   └── _eia_sources.yml
│   │   ├── staging/
│   │   │   ├── _staging_models.yml
│   │   │   ├── stg_eia__retail_sales.sql
│   │   │   └── stg_eia__generation.sql
│   │   ├── intermediate/
│   │   │   ├── int_retail_sales__with_changes.sql
│   │   │   ├── int_generation__categorized.sql
│   │   │   └── int_generation__state_month.sql
│   │   └── marts/
│   │       ├── core/
│   │       │   ├── dim_date.sql
│   │       │   ├── dim_geography.sql
│   │       │   ├── dim_sector.sql
│   │       │   ├── dim_energy_source.sql
│   │       │   ├── fct_retail_sales_monthly.sql
│   │       │   └── fct_generation_monthly.sql
│   │       └── reporting/
│   │           ├── mart_state_market_monthly.sql
│   │           ├── mart_state_price_scorecard.sql
│   │           ├── mart_state_generation_mix_monthly.sql
│   │           └── mart_state_market_overview.sql
│   ├── macros/
│   │   └── safe_percent_change.sql
│   ├── seeds/
│   │   ├── geography_classification.csv
│   │   └── energy_source_classification.csv
│   ├── snapshots/
│   └── tests/
│       └── assert_retail_price_reconciles.sql
│
├── orchestration/
│   └── dags/
│       └── eia_electricity_pipeline.py
│
├── notebooks/
│   └── 01_market_exploration.ipynb
│
├── tests/
│   ├── unit/
│   │   ├── test_eia_client.py
│   │   ├── test_pagination.py
│   │   ├── test_validators.py
│   │   └── test_records.py
│   ├── integration/
│   │   └── test_retail_load.py
│   └── fixtures/
│       ├── retail_sales_page.json
│       └── api_error.json
│
├── tableau/
│   ├── README.md
│   ├── metric_mapping.md
│   └── screenshots/
│
├── docs/
│   ├── 01_project_charter_and_architecture.md
│   ├── 02_data_sources_business_questions_and_metrics.md
│   ├── 03_technology_stack_and_source_file_guide.md
│   ├── 04_learning_and_implementation_roadmap.md
│   ├── 05_beginner_code_learning_templates.md
│   ├── data_dictionary.md
│   ├── runbook.md
│   └── decisions.md
│
└── .github/
    └── workflows/
        └── checks.yml
```

This is the target structure, not a command to create every empty file immediately. Files will be added when the implementation reaches their responsibility.

## 4. Root Files

### `README.md`

**Purpose:** repository front door.

It explains the business problem, architecture, setup, commands, dashboard, findings, and limitations. A recruiter should not need to read source code to understand what the project demonstrates.

### `.gitignore`

**Purpose:** prevent local or sensitive artifacts from being committed.

It should exclude `.env`, Python virtual environments, caches, logs, downloaded scratch data, dbt build artifacts, notebook checkpoints, and local database volumes where appropriate.

### `.env.example`

**Purpose:** document required environment-variable names without containing real secrets.

Expected variables may include:

```text
EIA_API_KEY=
POSTGRES_HOST=
POSTGRES_PORT=
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
TABLEAU_SERVER_URL=
TABLEAU_SITE_ID=
```

The real `.env` remains local and is ignored by Git.

### `pyproject.toml`

**Purpose:** define the Python project, runtime version, packages, and development tools in one place.

Likely dependencies will be introduced as needed rather than copied in bulk:

- `requests`
- `python-dotenv`
- `psycopg`
- `pytest`
- `pandas` and Jupyter for analysis
- `tenacity` only if we decide a retry library improves the implementation

### `docker-compose.yml`

**Purpose:** provide a repeatable local PostgreSQL environment and, later, possibly Airflow services.

We will initially keep it small. Mixing the first database lesson with a full multi-container Airflow deployment would create unnecessary debugging work.

### `config/project.yml`

**Purpose:** hold non-secret project choices such as endpoints, frequency, starting period, selected sectors, page length, and accepted geography types.

Secrets must not be placed here.

## 5. Python Package Files

### `src/eia_pipeline/__init__.py`

Marks the folder as a Python package. It should remain small and should not execute the pipeline when imported.

### `config.py`

**Purpose:** read and validate environment variables and non-secret configuration.

Responsibilities:

- Read `EIA_API_KEY` and database connection values.
- Fail with a clear message if required configuration is missing.
- Convert string values to appropriate types where needed.
- Expose a settings object to the rest of the package.

Why separate it: scattered environment lookups make code harder to test and error messages harder to understand.

### `logging_config.py`

**Purpose:** create consistent, useful logs.

Logs should answer:

- Which run is this?
- Which endpoint and date window is being processed?
- How many rows were requested, received, accepted, rejected, and loaded?
- Where did a failure occur?

Logs must never print the API key or database password.

### `eia_client.py`

**Purpose:** communicate with EIA over HTTP.

Responsibilities:

- Store the base URL and API key.
- Build request parameters.
- Send requests with timeouts.
- check HTTP status codes.
- Parse JSON.
- Retrieve route metadata and data pages.
- Raise meaningful errors.

It should return Python data structures and should not write directly to PostgreSQL. This keeps network behavior testable independently from database behavior.

### `pagination.py`

**Purpose:** retrieve every page of a result set.

Responsibilities:

- Track `offset` and `length`.
- Read the API's reported `total`.
- Continue until the number retrieved matches the expected total.
- Detect empty or repeated pages that could otherwise cause an infinite loop.

Why separate it: pagination is control-flow logic that deserves focused unit tests.

### `validators.py`

**Purpose:** reject unusable responses before loading them.

Initial checks:

- Response contains a `response` object.
- Response contains a data list.
- Required fields exist.
- Period strings use the expected format.
- Numeric measures can be converted to numbers or recognized as missing.
- Row counts match extraction expectations.

Validation here concerns source shape. Business-quality tests still belong in dbt.

### `records.py`

**Purpose:** translate source dictionaries into explicitly typed application records.

Examples:

- `RetailSalesRecord`
- `GenerationRecord`

This creates a visible contract between untrusted JSON and the raw database. It also provides one place to define conversions such as string-to-decimal and `YYYY-MM` to a month-start date.

### `database.py`

**Purpose:** manage PostgreSQL connections and reusable database operations.

Responsibilities:

- Open and close connections safely.
- Execute transactions.
- Roll back incomplete loads on failure.
- Provide reusable bulk insert/upsert behavior.

It should not know the EIA URL or Tableau details.

### `load_retail_sales.py`

**Purpose:** coordinate the retail-sales extraction and raw load.

Flow:

1. Establish a run record.
2. Request and validate metadata or configured facets.
3. Retrieve all requested pages.
4. Convert rows to typed records.
5. Upsert raw rows using the agreed logical key.
6. Compare requested, accepted, and loaded counts.
7. Mark the run successful or failed.

### `load_generation.py`

Performs the equivalent workflow for generation data while respecting its distinct fields and grain. It must not force generation responses into the retail-sales record shape.

### `cli.py`

**Purpose:** give humans and Airflow the same explicit commands.

Possible commands:

```text
eia-pipeline inspect-metadata
eia-pipeline load-retail-sales --start 2024-01 --end 2024-12
eia-pipeline load-generation --start 2024-01 --end 2024-12
```

Why it matters: a command-line interface separates user inputs from implementation functions and lets us test each operation manually before scheduling it.

### `tableau_refresh.py`

**Purpose:** trigger and verify a Tableau refresh after upstream success.

This file is added late because the specific approach depends on the available Tableau environment. It must distinguish “refresh requested” from “refresh completed successfully.”

## 6. SQL Bootstrap Files

### `001_create_schemas.sql`

Creates logical PostgreSQL schemas such as `raw`, `analytics`, and optionally an audit schema. Separating schemas clarifies which objects are source-shaped versus business-ready.

### `002_create_raw_tables.sql`

Creates raw EIA tables with:

- Source business keys.
- Source measures and units.
- Source labels.
- `_ingested_at`.
- `_run_id`.
- Optional source-response metadata.

Raw tables preserve the source meaning and avoid dashboard-specific calculations.

### `003_create_ingestion_runs.sql`

Creates an audit table containing:

- Run ID.
- Source/endpoint.
- Requested date range.
- Start and finish timestamps.
- Expected, received, accepted, and loaded row counts.
- Status and error summary.

## 7. dbt Files

### `_eia_sources.yml`

Declares raw PostgreSQL tables as dbt sources. It documents source columns and enables source-level tests and freshness expectations.

### `stg_eia__retail_sales.sql`

One-to-one cleanup of raw retail records:

- Rename fields to consistent `snake_case` names.
- Convert the period to a month-start date.
- Cast measure strings to numeric types.
- Standardize null values.
- Preserve the declared grain.

It should not calculate rankings or dashboard KPIs.

### `stg_eia__generation.sql`

Performs equivalent source cleanup for generation data while preserving fuel and producer-sector detail.

### `int_retail_sales__with_changes.sql`

Adds reusable window calculations such as prior-month value, prior-year value, rolling averages, and rolling volatility.

### `int_generation__categorized.sql`

Joins generation records to the reviewed energy-source classification seed. New or unmapped codes remain visible and cause an appropriate test or warning.

### `int_generation__state_month.sql`

Aggregates fuel-level generation into explicitly defined state-month totals and categories for safe downstream use.

### Core dimensions and facts

- `dim_date.sql`: reusable calendar attributes.
- `dim_geography.sql`: classifies state and aggregate codes.
- `dim_sector.sql`: describes EIA customer sectors.
- `dim_energy_source.sql`: assigns energy-source categories.
- `fct_retail_sales_monthly.sql`: tested retail fact.
- `fct_generation_monthly.sql`: tested generation fact.

### Reporting marts

- `mart_state_market_monthly.sql`: time-series retail analysis.
- `mart_state_price_scorecard.sql`: latest state ranking and market-screening measures.
- `mart_state_generation_mix_monthly.sql`: generation composition and share.
- `mart_state_market_overview.sql`: dashboard-facing state market summary.

### Seeds

CSV seed files hold small, reviewed mappings:

- Which EIA geography codes represent states versus aggregates.
- Which energy-source codes map to renewable, fossil, nuclear, or other.

These are explicit analytical decisions and therefore belong in version control.

### Custom tests

`assert_retail_price_reconciles.sql` returns rows whose reported price materially differs from price implied by revenue and sales. In a dbt singular test, returning zero rows means the test passed.

## 8. Test Files

### Unit tests

Unit tests isolate logic from external systems. They should not call the live EIA API.

- `test_eia_client.py`: parameter construction, timeouts, HTTP failures, and JSON handling using mocks.
- `test_pagination.py`: multiple pages, exact boundary, empty page, and mismatched totals.
- `test_validators.py`: missing keys, invalid periods, and nonnumeric measures.
- `test_records.py`: correct type conversion and rejection of invalid records.

### Fixtures

Small saved JSON examples make tests repeatable. They must not contain API keys or enormous response dumps.

### Integration tests

Integration tests verify that multiple real components work together, such as loading a small record set into a test PostgreSQL table and reading it back.

## 9. Orchestration File

### `orchestration/dags/eia_electricity_pipeline.py`

The eventual DAG should coordinate tasks resembling:

```text
check_configuration
    -> load_retail_sales
    -> load_generation
    -> dbt_source_checks
    -> dbt_build
    -> dbt_test_critical
    -> trigger_tableau_refresh
    -> verify_tableau_refresh
    -> record_success
```

Some independent tasks may later run in parallel, but clarity is more important than maximizing concurrency in the first version.

The DAG imports or invokes tested project components. It must not contain copies of all ingestion SQL and Python logic.

## 10. Analysis and Tableau Files

### SQL analysis files

These queries answer documented business questions and reconcile dashboard numbers. They should read marts, not recreate the dbt model in ad hoc SQL.

### Notebook

The notebook is for exploration, charts, diagnostics, or statistical work. It must be restartable from top to bottom and should read curated data rather than becoming the only place where transformations exist.

### `tableau/metric_mapping.md`

Maps every Tableau field and calculation to its dbt column and definition. Ideally most business metrics are already calculated upstream, reducing disagreement between SQL and the dashboard.

## 11. Git and Commit Strategy

Use small commits representing understandable progress, for example:

```text
docs: define retail-sales grain and KPI scope
feat: add EIA metadata request
test: cover missing response data
feat: paginate retail-sales results
feat: load raw retail-sales records
dbt: add retail-sales staging model and tests
```

Do not commit:

- API keys or passwords.
- `.env`.
- Database data directories.
- Large source extracts.
- Temporary notebooks and caches.
- Tableau credentials.

