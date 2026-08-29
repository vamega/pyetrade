"""Shared test utilities and fixture loading."""

import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(filename: str) -> str:
    """Load a fixture file as a string.

    Args:
        filename: Name of the fixture file (e.g., 'AccountListResponse.xml')

    Returns:
        Contents of the fixture file as a string.
    """
    fixture_path = FIXTURES_DIR / filename
    return fixture_path.read_text()


def load_json_fixture(filename: str) -> dict:
    """Load a JSON fixture file and parse it.

    Args:
        filename: Name of the JSON fixture file.

    Returns:
        Parsed JSON as a dictionary.
    """
    content = load_fixture(filename)
    return json.loads(content)
