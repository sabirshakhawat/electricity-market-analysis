"""Managed plumbing: fetch EIA history, validate, and publish a local SQL workspace."""

import json
import time
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import requests

from eia_pipeline.config import get_settings

ROOT = Path(__file__).resolve().parents[1]
STATES = (
    "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS "
    "MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA "
    "WV WI WY DC"
).split()
SECTORS = ["RES", "COM", "IND"]
URL = "https://api.eia.gov/v2/electricity/retail-sales/data/"


def fetch_page(params):
    """Retry temporary network failures without logging credential-bearing URLs."""
    for attempt in range(4):
        try:
            response = requests.get(URL, params=params, timeout=90)
            if response.status_code == 429 or response.status_code >= 500:
                raise RuntimeError(f"Temporary API status {response.status_code}")
            if response.status_code != 200:
                raise ValueError(f"EIA request failed: HTTP {response.status_code}")
            return response.json()["response"]
        except (requests.RequestException, RuntimeError):
            if attempt == 3:
                raise RuntimeError("EIA unavailable after four attempts") from None
            time.sleep(2**attempt)


def main():
    key = get_settings().eia_api_key
    rows = []
    total = None
    while total is None or len(rows) < total:
        params = [
            ("api_key", key),
            ("frequency", "monthly"),
            ("start", "2019-01"),
            ("offset", len(rows)),
            ("length", 5000),
        ]
        params += [
            (f"data[{i}]", m)
            for i, m in enumerate(["price", "sales", "revenue", "customers"])
        ]
        params += [("facets[stateid][]", s) for s in STATES]
        params += [("facets[sectorid][]", s) for s in SECTORS]
        for i, column in enumerate(["period", "stateid", "sectorid"]):
            params += [(f"sort[{i}][column]", column), (f"sort[{i}][direction]", "asc")]
        page = fetch_page(params)
        new_rows = page["data"]
        page_total = int(page["total"])
        if total is not None and page_total != total:
            raise ValueError("Source changed during pagination; rerun refresh")
        total = page_total
        if not new_rows and len(rows) < total:
            raise ValueError("Incomplete pagination")
        rows.extend(new_rows)
        print(f"Retrieved {len(rows)} of {total} rows")
    if not rows or len(rows) != total:
        raise ValueError("Empty or incomplete extraction")
    keys = [(r["period"], r["stateid"], r["sectorid"]) for r in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate month/state/sector keys")
    data_dir = ROOT / "data"
    export_dir = ROOT / "exports"
    data_dir.mkdir(exist_ok=True)
    export_dir.mkdir(exist_ok=True)
    raw_path = data_dir / "retail_sales.json"
    raw_path.write_text(json.dumps(rows))
    with duckdb.connect(str(data_dir / "electricity.duckdb")) as db:
        db.begin()
        try:
            db.execute("create schema if not exists raw")
            db.execute(
                "create or replace table raw.retail_sales as "
                "select * from read_json_auto(?)",
                [str(raw_path)],
            )
            db.execute((ROOT / "sql/setup.sql").read_text())
            count = db.sql("select count(*) from analytics.retail_monthly").fetchone()[
                0
            ]
            if count != total:
                raise ValueError("Loaded count differs from extraction")
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.execute(
            "copy (select * from analytics.market_trends "
            "order by month_start, state_code, sector_code) "
            "to ? (header, delimiter ',')",
            [str(export_dir / "market_trends.csv")],
        )
    (data_dir / "last_refresh.json").write_text(
        json.dumps(
            {
                "refreshed_at_utc": datetime.now(UTC).isoformat(),
                "rows": total,
                "start_period": min(r["period"] for r in rows),
                "end_period": max(r["period"] for r in rows),
            },
            indent=2,
        )
    )
    print(f"Ready: {count} rows in data/electricity.duckdb; Tableau CSV in exports/")


if __name__ == "__main__":
    main()
