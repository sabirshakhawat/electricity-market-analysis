"""Initial smoke test for the Python project setup."""

import eia_pipeline


def test_package_imports() -> None:
    """The installed project package should be importable."""
    assert eia_pipeline.__version__ == "0.1.0"

