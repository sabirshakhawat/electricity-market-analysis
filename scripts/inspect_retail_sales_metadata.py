"""Inspect the structure of EIA retail-sales metadata and facet values."""

from eia_pipeline.config import get_settings
from eia_pipeline.eia_client import fetch_eia_json

RETAIL_SALES_METADATA_PATH = "/electricity/retail-sales/"
SECTOR_FACET_PATH = "/electricity/retail-sales/facet/sectorid/"
STATE_FACET_PATH = "/electricity/retail-sales/facet/stateid/"


def main() -> None:
    """Retrieve and display the retail-sales source metadata."""
    settings = get_settings()

    payload = fetch_eia_json(
        RETAIL_SALES_METADATA_PATH,
        settings.eia_api_key,
    )
    metadata = payload["response"]

    print("\nDataset summary")
    print(f"ID: {metadata['id']}")
    print(f"Name: {metadata['name']}")
    print(f"Description: {metadata['description']}")
    print(f"Available period: {metadata['startPeriod']} to {metadata['endPeriod']}")
    print(f"Default date format: {metadata['defaultDateFormat']}")
    print(f"Default frequency: {metadata['defaultFrequency']}")

    frequencies = metadata["frequency"]

    print("\nAvailable frequencies")
    for frequency in frequencies:
        frequency_id = frequency["id"]
        description = frequency["description"]
        query_code = frequency["query"]
        date_format = frequency["format"]

        print(f"- {frequency_id}: {description}")
        print(f"  Query code: {query_code}; date format: {date_format}")

    measures = metadata["data"]

    print("\nAvailable measures")
    for measure_name in measures:
        measure_metadata = measures[measure_name]
        alias = measure_metadata["alias"]
        units = measure_metadata["units"]

        print(f"- {measure_name}: {alias} ({units})")

    facets = metadata["facets"]

    print("\nAvailable facet definitions")
    for facet in facets:
        facet_id = facet["id"]
        description = facet["description"]

        print(f"- {facet_id}: {description}")

    sector_payload = fetch_eia_json(
        SECTOR_FACET_PATH,
        settings.eia_api_key,
    )
    sector_response = sector_payload["response"]
    sector_values = sector_response["facets"]

    print("\nSector facet response structure")
    print(f"Response keys: {sector_response.keys()}")
    print(f"Number of sector values: {len(sector_values)}")
    print(f"First sector value: {sector_values[0]}")

    print("\nValid sector values")
    for sector in sector_values:
        sector_id = sector["id"]
        sector_name = sector["name"]

        print(f"- {sector_id}: {sector_name}")

    state_payload = fetch_eia_json(
        STATE_FACET_PATH,
        settings.eia_api_key,
    )
    state_response = state_payload["response"]
    state_values = state_response["facets"]

    print("\nState facet response structure")
    print(f"Response keys: {state_response.keys()}")
    print(f"Number of state/geography values: {len(state_values)}")
    print(f"First state/geography value: {state_values[0]}")

    print("\nValid state/geography values")
    for state in state_values:
        state_id = state["id"]
        state_name = state["name"]

        print(f"- {state_id}: {state_name}")


if __name__ == "__main__":
    main()
