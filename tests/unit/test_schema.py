import json
from pathlib import Path

import pytest

import src.utils.schema as schema_module
from src.utils.schema import load_schema, load_system_prompt

SCHEMA_DIR = Path(__file__).resolve().parent.parent.parent / "prompt" / "json_schema"
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def test_v2_chart_review_schema_is_valid_json():
    schema = load_schema("chart_review", "v2")
    assert isinstance(schema, dict)
    assert "schema" in schema
    assert schema["schema"]["type"] == "object"


def test_v2_feedback_schema_is_valid_json():
    schema = load_schema("cr_feedback", "v2")
    assert isinstance(schema, dict)
    assert "schema" in schema
    assert schema["schema"]["type"] == "object"


def test_chart_review_schema_name_preserved():
    schema = load_schema("chart_review", "v2")
    assert schema["name"] == "chart_review"


def test_feedback_schema_name_preserved():
    schema = load_schema("cr_feedback", "v2")
    assert schema["name"] == "cr_feedback"


def test_v2_chart_review_has_problems_array():
    schema = load_schema("chart_review", "v2")
    plan_props = schema["schema"]["properties"]["Plan"]["properties"]
    assert "problems" in plan_props
    assert plan_props["problems"]["type"] == "array"
    assert plan_props["problems"]["minItems"] == 1
    assert plan_props["problems"]["maxItems"] == 7


def test_v2_chart_review_no_fixed_problem_keys():
    schema = load_schema("chart_review", "v2")
    plan_props = schema["schema"]["properties"]["Plan"]["properties"]
    for key in plan_props:
        assert not key.startswith("Problem"), f"Found fixed problem key: {key}"


def test_v2_chart_review_typo_fixed():
    schema = load_schema("chart_review", "v2")
    problem_props = schema["schema"]["properties"]["Plan"]["properties"]["problems"]["items"]["properties"]
    assert "Decision Making and Diagnostic Plan" in problem_props
    assert "Decision Making and Diagnositic Plan" not in problem_props


def test_v2_chart_review_required_matches_properties():
    schema = load_schema("chart_review", "v2")
    problem_item = schema["schema"]["properties"]["Plan"]["properties"]["problems"]["items"]
    required = problem_item["required"]
    properties = problem_item["properties"]
    for field in required:
        assert field in properties, f"Required field '{field}' not in properties"


def test_v2_chart_review_no_orphan_problem_key():
    schema = load_schema("chart_review", "v2")
    plan_props = schema["schema"]["properties"]["Plan"]["properties"]
    assert "Problem " not in plan_props


def test_v2_feedback_has_problems_array():
    schema = load_schema("cr_feedback", "v2")
    details_props = schema["schema"]["properties"]["Feedback Details"]["properties"]
    assert "problems" in details_props
    assert details_props["problems"]["type"] == "array"


def test_v2_feedback_skill_assessment_enum():
    schema = load_schema("cr_feedback", "v2")
    problem_item = schema["schema"]["properties"]["Feedback Details"]["properties"]["problems"]["items"]
    skill = problem_item["properties"]["Skill Assessment"]
    assert skill["enum"] == ["Critical Gap", "Needs Improvement", "Meets Expectations", "Excellent"]


def test_load_schema_v1():
    schema = load_schema("chart_review", "v1")
    plan_props = schema["schema"]["properties"]["Plan"]["properties"]
    assert "Problem 1" in plan_props


def test_load_system_prompt_chart_review(monkeypatch):
    monkeypatch.setattr(schema_module, "PROMPT_DIR", FIXTURES_DIR)
    prompt = load_system_prompt("chart_review")
    assert len(prompt) > 100
    assert "chart review" in prompt.lower() or "assessment" in prompt.lower()


def test_load_system_prompt_feedback(monkeypatch):
    monkeypatch.setattr(schema_module, "PROMPT_DIR", FIXTURES_DIR)
    prompt = load_system_prompt("feedback")
    assert len(prompt) > 100


def test_load_system_prompt_explicit_path():
    """Covers the explicit path override branch (schema.py line 46)."""
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("custom prompt text")
        path = f.name
    try:
        prompt = load_system_prompt("chart_review", path=path)
        assert prompt == "custom prompt text"
    finally:
        os.unlink(path)


def test_load_system_prompt_unknown_step_raises():
    """Covers the ValueError branch for unknown step (schema.py line 50)."""
    with pytest.raises(ValueError, match="Unknown step"):
        load_system_prompt("nonexistent_step")
