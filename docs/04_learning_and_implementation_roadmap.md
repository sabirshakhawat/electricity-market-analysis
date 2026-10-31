# Learning and Implementation Roadmap

> Updated learning priority (2026-10-31): follow [06 — SQL-first workflow](06_sql_first_workflow.md).
> The assistant maintains Python plumbing; learn SQL, validation, metrics,
> Tableau, and insights first. The phases below are the original extended roadmap.

## 1. Learning Goal

The goal is not merely to receive working code. By the end of the project, you should be able to explain:

- What an API request and JSON response are.
- How authentication, parameters, status codes, pagination, retries, and timeouts work.
- Why raw data is preserved before transformation.
- What database grain, primary keys, and idempotent loads mean.
- Why Python and dbt have different responsibilities.
- How dbt dependencies and tests protect downstream consumers.
- How a scheduler turns manual steps into a dependable DAG.
- Why Tableau refresh must depend on upstream success.
- How to investigate a failed run using evidence.

## 2. Definition of a Lesson

Each build session should produce one visible capability and answer seven questions:

1. **Problem:** What are we trying to accomplish?
2. **Architecture:** Where does this step live?
3. **Contract:** What goes in and what comes out?
4. **Syntax:** Which new language features are required?
5. **Verification:** What successful evidence will we inspect?
6. **Failure:** What can go wrong, and how will the code respond?
7. **Connection:** Which downstream step depends on this output?

## 3. Phase 0 — Environment and Source Discovery

### Concepts

- Terminal, working directory, files, and environment variables.
- Python interpreter and virtual environment.
- Package installation.
- HTTP, URL, endpoint, query parameter, JSON, and API key.
- Difference between API metadata and API data.

### Build tasks

1. Initialize Git.
2. Create the Python project and virtual environment.
3. Add `.gitignore` and `.env.example`.
4. Register for an EIA API key.
5. Store the real key in a local `.env` file.
6. Write a tiny script that requests EIA route metadata.
7. Print selected metadata fields rather than the entire response.
8. Record discovered facets, measures, frequencies, and units.

### Verification

- The API key is not shown in Git status or source code.
- A metadata request returns HTTP 200.
- We can identify the valid retail-sales measures and sectors.
- We can explain the difference between a Python dictionary and JSON text.

### Exit artifact

A documented source contract and a working one-request script.

## 4. Phase 1 — First Retail-Sales Vertical Slice

### Concepts

- Functions, arguments, return values, dictionaries, lists, and loops.
- Request parameters and response status.
- Timeouts and explicit error handling.
- Separating fetch, validate, and display responsibilities.

### Build tasks

1. Request one state, one sector, one year, and the four retail measures.
2. Parse the response.
3. Validate the response envelope and required fields.
4. Convert one source row into a typed record.
5. Print a small readable table or summary.
6. Create a saved response fixture.
7. Write the first unit tests without calling the live API.

### Verification

- The requested date range and filters appear in the response.
- Numeric strings convert correctly.
- An intentionally invalid fixture fails with a useful error.
- Re-running the tests produces the same result without network access.

### Exit artifact

A tested function that retrieves and validates a small retail-sales result.

## 5. Phase 2 — Pagination and Complete Extraction

### Concepts

- Why APIs limit response sizes.
- Offset, page length, reported total, and loop termination.
- Rate limits and responsible request frequency.
- Retryable versus non-retryable errors.
- Backfill versus incremental extraction.

### Build tasks

1. Implement pagination for a controlled sample.
2. Track expected and retrieved row counts.
3. Add a timeout to every network request.
4. Add bounded retries for appropriate failures.
5. Expand extraction to selected states and sectors.
6. Parameterize start and end periods.
7. Test exact page boundaries and malformed pagination.

### Verification

- Retrieved count equals the API's reported total.
- A simulated failure does not create an infinite loop.
- The API key never appears in logs.
- Backfill and incremental date windows are visibly different.

### Exit artifact

A complete in-memory retail-sales extraction with reliable pagination.

## 6. Phase 3 — PostgreSQL Raw Storage

### Concepts

- Database, schema, table, row, column, and data type.
- Primary key, unique constraint, transaction, commit, and rollback.
- Insert versus upsert.
- Idempotency: running the same logical load again has the same result.
- Audit columns and run metadata.

### Build tasks

1. Start a local PostgreSQL instance.
2. Create raw and audit schemas/tables.
3. Connect Python using environment configuration.
4. Insert a tiny known batch.
5. Add the logical unique key.
6. Implement an upsert or delete-and-replace-period strategy.
7. Record ingestion-run status and row counts.
8. Test rollback by causing a controlled failure.

### Verification

- A SQL query returns the expected records.
- Re-running the same load does not increase logical row count.
- A failed transaction leaves no partial batch.
- Every raw record can be associated with a run.

### Exit artifact

An idempotent Python-to-PostgreSQL retail-sales loader.

## 7. Phase 4 — dbt Retail Models

### Concepts

- `source()`, `ref()`, models, materializations, and lineage.
- Staging versus intermediate versus mart responsibilities.
- Grain and unique keys.
- Generic and singular dbt tests.
- SQL window functions.

### Build tasks

1. Configure dbt locally without committing credentials.
2. Declare the raw retail table as a dbt source.
3. Build `stg_eia__retail_sales`.
4. Add uniqueness, not-null, accepted-values, and range tests.
5. Build date, geography, and sector dimensions.
6. Build the monthly retail fact.
7. Add year-over-year, rolling average, and volatility calculations.
8. Build the market and scorecard marts.
9. Add the revenue/sales price-reconciliation test.
10. Generate and inspect dbt documentation and lineage.

### Verification

- Each model's grain is written in its documentation.
- dbt builds models in dependency order.
- Critical tests pass on valid data and fail on a controlled bad record.
- Derived calculations match a hand-calculated sample.

### Exit artifact

A tested retail-electricity analytics layer.

## 8. Phase 5 — SQL/Python Analysis

### Concepts

- Analysis question versus metric definition.
- Reproducible query.
- Aggregation and filtering at the correct grain.
- Validation of surprising results.
- Descriptive analysis versus causal claims.

### Build tasks

1. Answer the price-level and year-over-year questions in SQL.
2. Rank states by rolling commercial price and volatility.
3. Explore seasonality and sales per customer.
4. Reconcile selected records manually and in SQL.
5. Use Python only where it improves exploration or statistical description.
6. Write findings with caveats.

### Verification

- Every reported KPI maps to a documented dbt column or transparent query.
- Rankings do not mix states with EIA aggregate regions.
- `ALL` sector rows are not summed together with component sectors.
- Findings can be regenerated from a clean database.

### Exit artifact

A reproducible analysis and a short findings document.

## 9. Phase 6 — Tableau Version 1

### Concepts

- Live connection versus extract.
- Dimensions, measures, filters, parameters, and dashboard actions.
- Visual hierarchy and audience-oriented design.
- Source-of-truth metric definitions.

### Build tasks

1. Connect Tableau to reporting marts.
2. Build a market overview.
3. Add state and sector filters.
4. Build trend and comparison views.
5. Add refresh timestamp and metric definitions.
6. Reconcile several Tableau values against SQL.

### Verification

- Tableau uses marts rather than raw tables.
- KPI values match SQL.
- Filters do not produce misleading totals.
- The latest data period is visible.

### Exit artifact

A validated retail-market dashboard.

## 10. Phase 7 — Generation-Mix Vertical Slice

### Concepts

- New API source discovery.
- Multiple fact tables with different grains.
- Reference mappings and unknown categories.
- Safe aggregation before joining.

### Build tasks

1. Inspect live power-operations metadata.
2. Document its exact grain, facets, measures, and units.
3. Build generation extraction, validation, and raw loading.
4. Create an energy-source classification seed.
5. Build staging, fact, category, and share models.
6. Add unmapped-source and total-share tests.
7. Add generation views to Tableau.

### Verification

- Fuel-level generation sums to the documented total within expected rules.
- Generation shares sum to approximately 100% at the intended grain.
- Retail measures do not multiply after adding generation data.
- Unknown fuel codes are visible rather than silently discarded.

### Exit artifact

A multi-source EIA dashboard with safe fact-table modeling.

## 11. Phase 8 — Orchestration and Controlled Refresh

### Concepts

- DAG, task, dependency, schedule, retry, backfill, and task state.
- Data interval versus actual execution time.
- Critical path and failure propagation.
- Triggering versus verifying an external refresh.

### Build tasks

1. Write down the manual commands in their required order.
2. Create the Airflow DAG using those commands or callable entry points.
3. Add a schedule appropriate to EIA publication frequency.
4. Configure retries only for transient failures.
5. Run dbt build and critical tests before publication.
6. Trigger Tableau refresh only on upstream success.
7. Verify the refresh result.
8. Exercise a deliberate upstream failure.

### Verification

- The DAG visualization matches the documented architecture.
- A failed critical dbt test prevents Tableau refresh.
- A successful run records row counts, model/test status, and refresh status.
- Re-running a date interval is safe.

### Exit artifact

A scheduled, monitored API-to-dashboard loop.

## 12. Phase 9 — Portfolio Polish

### Build tasks

- Finalize README and setup instructions.
- Add architecture and lineage images.
- Add a data dictionary and metric definitions.
- Write a troubleshooting runbook.
- Add dashboard screenshots or a short demonstration.
- Document at least three meaningful design decisions.
- State limitations and future weather enrichment honestly.
- Add automated checks suitable for the repository.

### Interview narrative

You should be able to explain the project in approximately two minutes:

1. The business problem and audience.
2. The recurring source and why a pipeline is useful.
3. How Python, PostgreSQL, dbt, Airflow, and Tableau divide responsibility.
4. One important data-modeling issue, such as grain or the `ALL` sector.
5. One quality gate that prevents bad dashboard data.
6. One analytical finding and one limitation.

## 13. Future Phase — Weather Enrichment

Weather begins only after the EIA loop is dependable.

New learning topics will include:

- Selecting a second API and comparing its contract with EIA.
- Spatial aggregation from weather observations to states.
- Heating-degree and cooling-degree measures.
- Date alignment and publication timing.
- Confounding variables and careful interpretation.
- Adding a second independent ingestion branch to the DAG.

## 14. “Done” Checklist for Every New Feature

- [ ] The feature has a plain-language purpose.
- [ ] Its input and output contracts are stated.
- [ ] Its file location matches its responsibility.
- [ ] Happy-path behavior was inspected.
- [ ] At least one important failure case was exercised.
- [ ] Secrets and credentials remain outside Git.
- [ ] Grain and keys are documented where data is created.
- [ ] Tests are appropriate to the risk.
- [ ] Documentation explains why, not just how.
- [ ] Downstream dependencies are understood.

