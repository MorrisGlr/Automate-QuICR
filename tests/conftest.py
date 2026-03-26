import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"


@pytest.fixture
def project_root():
    return PROJECT_ROOT


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR


@pytest.fixture
def v1_chart_review(fixtures_dir):
    path = fixtures_dir / "v1_chart_review.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def v1_feedback(fixtures_dir):
    path = fixtures_dir / "v1_feedback.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def v2_chart_review(fixtures_dir):
    path = fixtures_dir / "v2_chart_review.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def v2_feedback(fixtures_dir):
    path = fixtures_dir / "v2_feedback.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
