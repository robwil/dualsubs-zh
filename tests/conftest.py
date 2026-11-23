import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_probe() -> dict:
    return json.loads((FIXTURES / "sample_probe.json").read_text(encoding="utf-8"))


@pytest.fixture
def en_srt() -> str:
    return (FIXTURES / "en.srt").read_text(encoding="utf-8")


@pytest.fixture
def zh_srt() -> str:
    return (FIXTURES / "zh.srt").read_text(encoding="utf-8")
