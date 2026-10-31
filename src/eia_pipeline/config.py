"""Load and validate project configuration."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


@dataclass(frozen=True)
class Settings:
    """Configuration required by the pipeline."""

    eia_api_key: str


def get_settings() -> Settings:
    """Read required settings and fail clearly when one is missing."""
    api_key = os.getenv("EIA_API_KEY")

    if not api_key:
        raise ValueError(
            "EIA_API_KEY is missing. Add it to the project's .env file."
        )

    return Settings(eia_api_key=api_key)