# EIA Electricity Market Analysis

> **Active workflow: SQL-first analysis.** Start with
> [the SQL workspace guide](docs/06_sql_first_workflow.md).
> Managed Python ingestion supplies a local DuckDB database and Tableau CSV.
> Your learning focus is SQL, data quality, metrics, visualization, and insights.
> PostgreSQL, dbt, Airflow, generation mix, and weather remain future phases.
> The historical roadmap below records the broader design; it does not describe
> tools already implemented.

## A Guided End-to-End Analytics Pipeline Project

This repository will become a recurring analytics pipeline that retrieves electricity data from the U.S. Energy Information Administration (EIA), stores the source data, transforms and tests it with SQL and dbt, analyzes state electricity markets, and refreshes a Tableau dashboard after the upstream data passes its quality checks.

The pipeline—not a one-time notebook—is the main portfolio artifact.

## Project Story

**Audience:** an analyst supporting a multi-state commercial operator, facilities team, energy buyer, or site-selection team.

**Decision supported:** compare state electricity markets on cost, demand, growth, volatility, and generation mix so the organization can identify markets that merit deeper investigation.

**Core source:** EIA Open Data API v2.

**Later enrichment:** weather and temperature data, added only after the core EIA pipeline works reliably.

## Documentation Map

Read these documents in order:

1. [Project charter and architecture](docs/01_project_charter_and_architecture.md) — what we are building, who it serves, and how data moves through the system.
2. [Data sources, questions, and metrics](docs/02_data_sources_business_questions_and_metrics.md) — what the EIA data means and which analytical questions we will answer.
3. [Technology stack and source-file guide](docs/03_technology_stack_and_source_file_guide.md) — the responsibility of every tool, folder, and planned source file.
4. [Learning and implementation roadmap](docs/04_learning_and_implementation_roadmap.md) — the order in which we will build the project and what you should learn in each phase.
5. [Beginner code-learning templates](docs/05_beginner_code_learning_templates.md) — reusable patterns for understanding and writing API, database, dbt, test, and orchestration code.
6. [Local environment setup](docs/00_environment_setup.md) — how the isolated Python environment, dependencies, secrets, and checks work.

## Our Working Method

For each implementation step, we will use the same sequence:

1. State the problem in plain language.
2. Locate the step in the overall architecture.
3. Define the input and expected output.
4. Learn the minimum syntax needed.
5. Write a small version together.
6. Inspect the result instead of assuming it worked.
7. Add an error case or test.
8. Connect the small version to the pipeline.
9. Record what changed and why.

Code examples will distinguish between:

- **Concept:** what the code is trying to accomplish.
- **Syntax:** what the Python or SQL symbols mean.
- **Project role:** where the code belongs in the architecture.
- **Verification:** how we know it worked.
- **Failure behavior:** what should happen when it does not work.

## Initial Scope

### Version 1: retail electricity market

- Monthly electricity price, sales, revenue, and customer counts.
- U.S. states and District of Columbia.
- Residential, commercial, and industrial sectors.
- Historical backfill followed by incremental monthly updates.
- State comparisons, trends, growth, seasonality, and volatility.

### Version 2: generation mix

- Monthly generation by state and energy source.
- Renewable, fossil, nuclear, and other generation categories.
- Generation share and changes in market composition.

### Version 3: automation and publication

- Scheduled orchestration.
- dbt transformations and blocking data-quality tests.
- Tableau dashboard refresh after successful upstream tasks.

### Version 4: weather enrichment

- Temperature and weather measures aligned by state and month.
- Weather-normalized interpretation of demand and seasonality.
- This phase is intentionally excluded from the first implementation.

## Current Status

**Environment stage.** The project scope and learning framework are documented, the Python package is initialized, and its isolated development environment can be verified. API ingestion code has not been implemented yet.

## Authoritative References

- [EIA Open Data](https://www.eia.gov/opendata/)
- [EIA API v2 technical documentation](https://www.eia.gov/opendata/documentation.php)
- [EIA electricity data](https://www.eia.gov/electricity/data.php)
