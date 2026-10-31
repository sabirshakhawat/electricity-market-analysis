"""Inspect one bounded slice of EIA monthly retail-sales observations.

This is a learning and source-discovery script. It is not the production
loader and does not write anything to PostgreSQL.
"""

from typing import Any

from eia_pipeline.config import get_settings
from eia_pipeline.eia_client import fetch_eia_json

RETAIL_SALES_DATA_PATH = "/electricity/retail-sales/data/"

# ---------------------------------------------------------------------------
# LEARNING INPUTS
# ---------------------------------------------------------------------------
# These values define the small slice we want to inspect. Colorado is only an
# example. Later, these values will become command-line or pipeline inputs.
EXAMPLE_STATE_CODE = "CO"
EXAMPLE_SECTOR_CODE = "COM"
EXAMPLE_START_PERIOD = "2024-01"
EXAMPLE_END_PERIOD = "2024-12"
EXAMPLE_MEASURES = ["price", "sales", "revenue", "customers"]


def build_query_params() -> list[tuple[str, Any]]:
    """Build the query parameters for one bounded learning request.

    The return type is a list of ``(parameter_name, value)`` tuples. EIA uses
    repeated parameter names and bracket notation for measure arrays and facet
    filters, so this representation makes the outgoing request explicit.

    Example tuple:
        ("facets[stateid][]", "CO")

    Meaning:
        Filter the state/geography facet to Colorado.
    """

    # This block defines the request's frequency, geography, sector, dates,
    # ordering, and first page. These choices determine the requested grain.
    params: list[tuple[str, Any]] = [
        ("frequency", "monthly"),
        ("facets[stateid][]", EXAMPLE_STATE_CODE),
        ("facets[sectorid][]", EXAMPLE_SECTOR_CODE),
        ("start", EXAMPLE_START_PERIOD),
        ("end", EXAMPLE_END_PERIOD),
        ("sort[0][column]", "period"),
        ("sort[0][direction]", "asc"),
        ("offset", 0),
        ("length", 5000),
    ]

    # Measures are an API array. Enumerating the list produces data[0],
    # data[1], and so on without hard-coding four nearly identical lines.
    for index, measure in enumerate(EXAMPLE_MEASURES):
        params.append((f"data[{index}]", measure))

    return params


def main() -> None:
    """Request the bounded slice and inspect its response and first row."""

    # BOILERPLATE: safely load the API key from the project's .env file.
    settings = get_settings()

    # CORE API SKILL: construct the query separately so it can be printed,
    # tested, and eventually reused independently of the network request.
    query_params = build_query_params()

    print("Requested slice")
    print(f"- State: {EXAMPLE_STATE_CODE}")
    print(f"- Sector: {EXAMPLE_SECTOR_CODE}")
    print(f"- Period: {EXAMPLE_START_PERIOD} to {EXAMPLE_END_PERIOD}")
    print(f"- Measures: {EXAMPLE_MEASURES}")

    # BOILERPLATE: the shared client adds authentication, applies a timeout,
    # checks the HTTP status, and converts JSON into Python objects.
    payload = fetch_eia_json(
        RETAIL_SALES_DATA_PATH,
        settings.eia_api_key,
        query_params,
    )

    # CORE JSON SKILL: inspect the outer response envelope before assuming the
    # location or shape of the observation rows.
    print("\nOuter response structure")
    print(f"Payload type: {type(payload)}")
    print(f"Payload keys: {payload.keys()}")

    response = payload["response"]

    print("\nNested response structure")
    print(f"Response type: {type(response)}")
    print(f"Response keys: {response.keys()}")
    print(f"API-reported total: {response['total']}")
    print(f"Returned frequency: {response['frequency']}")
    print(f"Returned date format: {response['dateFormat']}")

    # CORE DATA SKILL: observations live in response.data. We first inspect
    # the collection, then one row, before writing conversions or validation.
    rows = response["data"]

    print("\nObservation structure")
    print(f"Rows type: {type(rows)}")
    print(f"Rows returned on this page: {len(rows)}")

    if rows:
        first_row = rows[0]
        print(f"First-row type: {type(first_row)}")
        print(f"First-row keys: {first_row.keys()}")
        print(f"First row: {first_row}")
    else:
        print("No rows were returned. Inspect the requested facet and date values.")

    # NEXT LEARNING TASKS (intentionally not implemented here):
    # 1. Compare len(rows) with response["total"].
    # 2. Verify that this one-year monthly request contains the expected months.
    # 3. Identify dimensions, measures, and unit fields in first_row.
    # 4. Check whether numeric measures arrive as strings or numbers.
    # 5. Define the candidate row key: period + stateid + sectorid.
    # 6. Deliberately request an invalid sector and observe the empty response.


if __name__ == "__main__":
    main()
