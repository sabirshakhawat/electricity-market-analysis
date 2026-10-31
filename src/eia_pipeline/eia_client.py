"""Communicate with the EIA Open Data API."""

from typing import Any

import requests

EIA_BASE_URL = "https://api.eia.gov/v2"


def fetch_eia_json(
    path: str,
    api_key: str,
    query_params: list[tuple[str, Any]] | None = None,
) -> dict[str, Any]:
    """Request one EIA endpoint and return its decoded JSON response.

    ``query_params`` is optional so metadata requests can continue to pass only
    a path and API key. A list of tuples is used because EIA queries can repeat
    parameter names, such as requesting several measures or facet values.
    """
    if not path.startswith("/"):
        raise ValueError("EIA API paths must begin with '/'")

    url = f"{EIA_BASE_URL}{path}"

    # Copy the caller's parameters before adding authentication. This avoids
    # unexpectedly modifying the list owned by the calling script.
    request_params = list(query_params or [])
    request_params.append(("api_key", api_key))

    response = requests.get(
        url,
        params=request_params,
        timeout=30,
    )

    # Print the endpoint and status, but not the fully encoded request URL,
    # because the latter would expose the API key.
    print(f"GET {url} -> HTTP {response.status_code}")

    response.raise_for_status()

    return response.json()

