# SQL-first analyst workspace

As of October 31, 2026, the active learning path prioritizes SQL, data quality,
metrics, Tableau, and communicating insights. Python infrastructure is maintained
by the assistant. Documents 01–05 describe the broader target architecture;
their Python lessons are optional and their PostgreSQL/dbt/Airflow phases are deferred.

## Current data flow

```text
EIA API -> managed Python fetch/validation -> raw JSON + DuckDB raw table
        -> SQL analytics views -> your SQL analysis -> CSV -> Tableau
```

DuckDB is a local SQL database stored in one file. It lets you practice joins,
aggregation, CTEs, window functions, date logic, and data quality immediately.
It replaces PostgreSQL for this working phase. dbt and orchestration can be
introduced after your first analysis/dashboard. They are not currently implemented.

## Start working

From the project root:

```bash
source .venv/bin/activate
python -m pip install -e '.[dev]'
python scripts/refresh_workspace.py
duckdb data/electricity.duckdb
```

In DuckDB, run:

```sql
.read sql/01_explore.sql
.read sql/02_business_questions.sql
```

Use `.quit` to exit. Save your own queries in `sql/` and your findings in
`analysis/findings.md`. You can also open this database using a DuckDB-compatible
SQL editor. SQL uses DuckDB syntax; some syntax will differ when moving to PostgreSQL.

## Tables and grain

- `raw.retail_sales`: source-shaped monthly EIA records.
- `analytics.retail_monthly`: typed measures and clear column names.
- `analytics.market_trends`: calendar-aligned prior-year prices, YoY change,
  usage per customer, and revenue per customer.

Grain: one month, one state/DC geography, one customer sector. The load selects
50 states plus DC and RES/COM/IND from January 2019 through the latest available
EIA month. It excludes national/region aggregates and ALL sector to avoid overlap.
The fetcher verifies pagination totals, unique keys, and numeric casts. Missing
values and coverage gaps still need analyst review; the load does not certify every
business-quality rule. Prices are nominal average retail prices, not facility tariffs.

## Tableau

Connect Tableau to the text file `exports/market_trends.csv`. Check month_start
is a date and state_code/state_name have geographic roles. Start with commercial
price by state, historical trends, YoY change, and sales seasonality. Compare chart
values with SQL. Source frequency is monthly; latest observations lag calendar time.

The CSV is a snapshot. After refreshing the workspace, manually refresh/reopen
the Tableau data source. Automated Tableau refresh is a future phase. Do not claim
that local generation of the CSV publishes a refreshed dashboard.

## Your immediate learning sequence

1. Inspect columns and coverage; state what one row represents.
2. Write GROUP BY queries and validate totals.
3. Define YoY growth and compare states with compatible periods.
4. Use window functions for rolling averages/volatility.
5. Build Tableau views and reconcile them with SQL.
6. Write findings with evidence, limitations, and a business implication.

Refresh does a complete bounded reload so historical revisions are picked up.
Database replacement happens inside a transaction; HTTP failure leaves the prior
database intact. Raw files and CSV exports are local and excluded from Git.

## GitHub scope

Publish code, SQL, and documentation. Exclude `.env`, virtual environments,
data/exports, and unrelated job-search files. No GitHub workflow currently runs
live ingestion, so a repository clone needs an EIA key to reproduce the data.
