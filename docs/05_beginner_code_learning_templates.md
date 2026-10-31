# Beginner Code-Learning Templates

> As of 2026-10-31, Python exercises are optional reference material.
> The active learning path is [06 — SQL-first workflow](06_sql_first_workflow.md).

## 1. How to Read the Examples

These examples are teaching scaffolds, not finished production code. Each follows the same structure:

```text
PURPOSE -> INPUT -> OUTPUT -> STEPS -> CODE -> VERIFY -> FAILURE -> PIPELINE ROLE
```

When we implement a file, we will type and run the smallest useful version first. Then we will add configuration, logging, tests, retries, and database behavior in separate understandable changes.

## 2. Universal Function Template

Before writing a function, complete this card:

```text
Function name:
Plain-language job:
Inputs:
Output:
Side effects:
Expected failures:
Caller:
Downstream consumer:
How we will test it:
```

Python skeleton:

```python
def verb_noun(input_value: InputType) -> OutputType:
    """One-sentence statement of the function's responsibility."""
    # 1. Validate assumptions about the input.
    # 2. Perform one focused operation.
    # 3. Return a predictable output.
    return output_value
```

Learning notes:

- `def` defines a function.
- `input_value` is a parameter: a name for the value supplied by the caller.
- `InputType` and `OutputType` are type hints that make the contract easier to read.
- `return` sends a value back to the caller.
- A function should generally have one clear reason to change.

## 3. First API Request Template

### Purpose

Send an HTTP GET request to one EIA endpoint and convert its JSON response into a Python dictionary.

### Input

- Endpoint URL.
- API key.
- Query-parameter dictionary.

### Output

A Python dictionary representing the decoded JSON response.

### Teaching scaffold

```python
from typing import Any

import requests


def fetch_json(
    url: str,
    api_key: str,
    query_params: dict[str, Any],
) -> dict[str, Any]:
    """Fetch one JSON response from an EIA API endpoint."""
    params = {**query_params, "api_key": api_key}

    response = requests.get(
        url,
        params=params,
        timeout=30,
    )
    response.raise_for_status()

    return response.json()
```

### Syntax explained

- `import requests` makes the external HTTP library available.
- `dict[str, Any]` means a dictionary with string keys and values that may have different types.
- `{**query_params, "api_key": api_key}` copies the supplied parameters and adds the API key.
- `requests.get(...)` performs an HTTP GET operation.
- `params=params` lets the library encode the URL query string safely.
- `timeout=30` prevents the program from waiting forever.
- `raise_for_status()` raises an exception for unsuccessful HTTP status codes.
- `response.json()` decodes JSON into Python dictionaries and lists.

### Verify

- Print the status code during the first experiment.
- Inspect `payload.keys()` rather than dumping credentials or a huge payload.
- Confirm that the expected response object exists.

### Failure questions

- What happens if the key is missing?
- What happens if the endpoint is misspelled?
- What happens during a timeout?
- What happens if the server returns HTML instead of JSON?

### Pipeline role

This behavior belongs in `eia_client.py`. It should fetch data, not load PostgreSQL or calculate KPIs.

## 4. EIA Parameter Template

EIA uses repeated array-like parameters. The `requests` library can encode them using a list of key/value tuples.

```python
params = [
    ("frequency", "monthly"),
    ("data[0]", "price"),
    ("data[1]", "sales"),
    ("data[2]", "revenue"),
    ("data[3]", "customers"),
    ("facets[stateid][]", "CO"),
    ("facets[sectorid][]", "COM"),
    ("start", "2024-01"),
    ("end", "2024-12"),
    ("sort[0][column]", "period"),
    ("sort[0][direction]", "asc"),
    ("offset", 0),
    ("length", 5000),
]
```

Why a list of tuples instead of only a dictionary? A URL may repeat a parameter name, particularly for multiple facet values. A list preserves those repeated keys and their order visibly.

We will confirm exact parameters against the live route metadata and official documentation before production use.

## 5. Response-Validation Template

### Purpose

Turn a vague downstream error into an immediate, specific source-contract error.

```python
from typing import Any


class EIAResponseError(ValueError):
    """Raised when an EIA response does not match the expected shape."""


def extract_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Return response rows after checking the required envelope."""
    response = payload.get("response")
    if not isinstance(response, dict):
        raise EIAResponseError("Expected a response object")

    rows = response.get("data")
    if not isinstance(rows, list):
        raise EIAResponseError("Expected response.data to be a list")

    return rows
```

Syntax explained:

- `class ... (ValueError)` defines a project-specific exception.
- `.get("response")` returns `None` instead of crashing when a key is absent.
- `isinstance(value, dict)` checks a runtime type.
- `raise` stops normal execution and reports a meaningful failure.

Verification:

- A valid fixture returns rows.
- `{}` raises `EIAResponseError`.
- `{"response": {"data": "not a list"}}` also raises it.

Pipeline connection: validation occurs after fetching and before record conversion or loading.

## 6. Record-Conversion Template

### Purpose

Convert loose JSON strings into a predictable internal record.

```python
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class RetailSalesRecord:
    period: date
    geography_code: str
    sector_code: str
    price_cents_per_kwh: Decimal | None
    sales_million_kwh: Decimal | None
    revenue_million_dollars: Decimal | None
    customers: int | None
```

Why these choices:

- A dataclass groups named fields into one explicit record type.
- `frozen=True` prevents accidental changes after creation.
- `date` is safer for comparisons than an unvalidated date string.
- `Decimal` avoids some floating-point surprises in financial-style values.
- `| None` states that a value may be missing.

The conversion function should be separate so it can be tested with one row at a time.

## 7. Pagination Template

### Purpose

Fetch all rows without assuming one response contains the complete result.

### Pseudocode first

```text
set offset to zero
set all_rows to an empty list

repeat:
    request a page using offset and page length
    validate the response
    read the reported total
    append page rows to all_rows
    increase offset by the number of rows received

    if no rows arrived before total was reached:
        fail to avoid an infinite loop

until number of collected rows reaches total

verify collected count equals total
return all_rows
```

### Python-shaped scaffold

```python
def fetch_all_rows(page_length: int = 5000) -> list[dict]:
    all_rows: list[dict] = []
    offset = 0
    expected_total: int | None = None

    while expected_total is None or len(all_rows) < expected_total:
        page_payload = fetch_page(offset=offset, length=page_length)
        page_rows, page_total = validate_page(page_payload)

        if not page_rows and len(all_rows) < page_total:
            raise RuntimeError("Pagination stopped before reaching total")

        all_rows.extend(page_rows)
        offset += len(page_rows)
        expected_total = page_total

    if len(all_rows) != expected_total:
        raise RuntimeError("Retrieved row count does not match API total")

    return all_rows
```

This scaffold intentionally refers to functions we will design separately. That prevents pagination code from also owning HTTP configuration and source-row conversion.

## 8. Database Transaction Template

### Purpose

Load a batch completely or leave the database unchanged.

```python
import psycopg


def load_batch(connection_string: str, records: list[tuple]) -> int:
    """Load one batch in a transaction and return its row count."""
    with psycopg.connect(connection_string) as connection:
        with connection.cursor() as cursor:
            cursor.executemany(
                """
                insert into raw.eia_retail_sales (...)
                values (...)
                on conflict (...) do update
                set ...
                """,
                records,
            )

    return len(records)
```

Important design lessons:

- SQL values must be passed as parameters, not concatenated into a string.
- The real column lists and conflict key must be explicit.
- The connection context commits on success and rolls back on an exception.
- Batch loading is more efficient than one connection per row.
- We will inspect `psycopg` behavior and write an integration test before trusting the loader.

## 9. dbt Staging-Model Template

### Purpose

Cast and rename source-shaped columns while preserving the source grain.

```sql
with source as (

    select *
    from {{ source('eia_raw', 'retail_sales') }}

), renamed_and_cast as (

    select
        period::date as month_start,
        state_id as geography_code,
        state_description as geography_name,
        sector_id as sector_code,
        sector_name,
        price::numeric as price_cents_per_kwh,
        sales::numeric as sales_million_kwh,
        revenue::numeric as revenue_million_dollars,
        customers::bigint as customers,
        _ingested_at,
        _run_id
    from source

)

select * from renamed_and_cast
```

Syntax explained:

- `{{ source(...) }}` is dbt's reference to a declared external/raw table.
- `with` creates named query steps called common table expressions.
- `::date`, `::numeric`, and `::bigint` are PostgreSQL casts.
- Aliases provide clear analytical names.

Before implementation, the raw column names and period conversion will be matched to the schema we actually create.

## 10. dbt Test Template

Generic tests in YAML:

```yaml
version: 2

models:
  - name: fct_retail_sales_monthly
    description: One row per month, geography, and customer sector.
    columns:
      - name: retail_sales_key
        tests:
          - unique
          - not_null

      - name: sector_code
        tests:
          - accepted_values:
              values: ['RES', 'COM', 'IND', 'TRA', 'OTH', 'ALL']
```

Questions to ask before writing a test:

- Which business or technical failure does this catch?
- Should failure block publication or only warn?
- At which model is the assumption first guaranteed?
- Can the error message lead us to the offending rows?

## 11. SQL Window-Calculation Template

Year-over-year price comparison:

```sql
select
    month_start,
    geography_code,
    sector_code,
    price_cents_per_kwh,
    lag(price_cents_per_kwh, 12) over (
        partition by geography_code, sector_code
        order by month_start
    ) as price_one_year_ago
from {{ ref('fct_retail_sales_monthly') }}
```

Syntax explained:

- `lag(value, 12)` accesses the value twelve rows earlier.
- `partition by` restarts the history for every geography and sector.
- `order by month_start` defines chronological row order.
- This assumes one row per month in each partition; grain and completeness tests matter.

A missing month means twelve rows earlier may not equal twelve calendar months earlier. We will choose a robust date-alignment strategy after inspecting completeness.

## 12. Unit-Test Template

```python
import pytest


def test_extract_rows_rejects_missing_response() -> None:
    payload = {}

    with pytest.raises(EIAResponseError, match="response object"):
        extract_rows(payload)
```

Test structure:

```text
Arrange: create the input and dependencies
Act: run the behavior
Assert: check the observable result
```

The example combines act and assert through `pytest.raises`. The test name states behavior, not implementation detail.

## 13. Orchestration Template

Conceptual task wrappers:

```python
def load_retail_task() -> None:
    run_retail_load()


def dbt_build_task() -> None:
    run_checked_command(["dbt", "build", "--select", "tag:published"])


def refresh_tableau_task() -> None:
    trigger_and_verify_tableau_refresh()
```

The important lesson is not the decorator syntax. It is that the DAG coordinates reusable, independently testable operations. We will add actual Airflow syntax only after the underlying commands work manually.

## 14. Debugging Template

When something fails, fill in this evidence record before changing code:

```text
Expected behavior:
Observed behavior:
Exact error message:
Smallest input that reproduces it:
Last confirmed successful boundary:
Relevant row counts/status codes:
Current hypothesis:
Test that would disprove the hypothesis:
```

This prevents random edits and builds a professional debugging habit.

## 15. Code Review Questions

For every function or model, ask:

- Can I state its responsibility in one sentence?
- Does its name describe that responsibility?
- Is its input/output contract visible?
- Does it mix network, database, transformation, and presentation concerns?
- Can it be tested without calling every external system?
- Could it expose a secret in logs or an exception?
- Does it handle empty or missing data intentionally?
- Is the row grain clear?
- What downstream output becomes wrong if this code fails silently?

## 16. Initial Hands-On Exercise

Our first implementation session should do only this:

1. Create the Python environment.
2. Add the API key safely.
3. Request retail-sales metadata.
4. Print available measures, sectors, frequencies, and date range.
5. Save no production data yet.
6. Explain each line and then rewrite the core request with fewer prompts.

That small exercise teaches the API boundary on which the rest of the project depends.

