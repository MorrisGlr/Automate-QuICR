import json
import sys
from pathlib import Path

import pytest

# Add project root to path so we can import the migration script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from migrate_v1_to_v2 import migrate_chart_review, migrate_feedback


@pytest.fixture
def v1_chart_review_data():
    path = PROJECT_ROOT / "tests" / "fixtures" / "v1_chart_review.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def v1_feedback_data():
    path = PROJECT_ROOT / "tests" / "fixtures" / "v1_feedback.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_migrate_chart_review_produces_problems_array(v1_chart_review_data):
    result = migrate_chart_review(v1_chart_review_data)
    assert "problems" in result["Plan"]
    assert isinstance(result["Plan"]["problems"], list)
    assert len(result["Plan"]["problems"]) > 0


def test_migrate_chart_review_preserves_problem_count(v1_chart_review_data):
    # Count v1 problems (keys starting with "Problem" in Plan, excluding orphan)
    plan = v1_chart_review_data["Plan"]
    v1_count = sum(
        1 for k, v in plan.items()
        if isinstance(v, dict)
        and k not in ("Anticipatory Preventative Care", "Follow Up Care", "Generic Drug Pricing", "Preventative Care")
        and k.strip() != "Problem"
    )
    result = migrate_chart_review(v1_chart_review_data)
    assert len(result["Plan"]["problems"]) == v1_count


def test_migrate_chart_review_fixes_diagnostic_typo(v1_chart_review_data):
    result = migrate_chart_review(v1_chart_review_data)
    for problem in result["Plan"]["problems"]:
        assert "Decision Making and Diagnostic Plan" in problem
        assert "Decision Making and Diagnositic Plan" not in problem


def test_migrate_chart_review_normalizes_treatment_field(v1_chart_review_data):
    result = migrate_chart_review(v1_chart_review_data)
    for problem in result["Plan"]["problems"]:
        assert "Treatment/Medication Plan" in problem


def test_migrate_chart_review_preserves_apc(v1_chart_review_data):
    result = migrate_chart_review(v1_chart_review_data)
    assert "Anticipatory Preventative Care" in result["Plan"]


def test_migrate_chart_review_preserves_follow_up(v1_chart_review_data):
    result = migrate_chart_review(v1_chart_review_data)
    assert "Follow Up Care" in result["Plan"]


def test_migrate_chart_review_removes_orphan_key():
    """Test that the orphan 'Problem ' key (space, no number) is removed."""
    data = {
        "Plan": {
            "Problem 1": {
                "Problem Name": "Test Problem",
                "Status": "Stable",
                "Decision Making and Diagnositic Plan": "Plan here",
                "Treatment/Medication Plan": "Meds",
                "Contingency Planning": "Contingency",
                "Considerations for Documentation Improvement": "Docs",
                "Considerations for Cost Effective Care Improvement": "Cost",
            },
            "Problem ": {
                "Problem Name": "Orphan",
                "Status": "Unknown",
                "Decision Making and Diagnositic Plan": "N/A",
                "Treatment/Medication Plan": "N/A",
                "Contingency Planning": "N/A",
                "Considerations for Documentation Improvement": "N/A",
                "Considerations for Cost Effective Care Improvement": "N/A",
            },
            "Anticipatory Preventative Care": {"Item 1": "Test"},
            "Follow Up Care": {"Item 1": "Test"},
        }
    }
    result = migrate_chart_review(data)
    assert len(result["Plan"]["problems"]) == 1
    assert result["Plan"]["problems"][0]["Problem Name"] == "Test Problem"


def test_migrate_chart_review_variant_a_condition_names():
    """Test migration of older format where condition names are keys (no 'Problem Name' subfield)."""
    data = {
        "Assessment": "Test",
        "Plan": {
            "Atrial Fibrillation": {
                "Status": "Stable",
                "Decision Making and Diagnostic Plan": "Plan",
                "Treatment Plan": "Meds",
                "Contingency Planning": "Contingency",
            },
            "Hypertension": {
                "Status": "Not at goal",
                "Decision Making and Diagnostic Plan": "Plan",
                "Treatment Plan": "Meds",
                "Contingency Planning": "Contingency",
            },
            "Preventative Care": {"Vaccinations": "Up to date"},
        }
    }
    result = migrate_chart_review(data)
    problems = result["Plan"]["problems"]
    assert len(problems) == 2
    names = [p["Problem Name"] for p in problems]
    assert "Atrial Fibrillation" in names
    assert "Hypertension" in names


def test_migrate_chart_review_moves_toplevel_apc_under_plan():
    """Test that APC at top level gets moved under Plan."""
    data = {
        "Plan": {
            "Problem 1": {
                "Problem Name": "Test",
                "Status": "Stable",
                "Decision Making and Diagnositic Plan": "Plan",
                "Treatment/Medication Plan": "Meds",
                "Contingency Planning": "Contingency",
                "Considerations for Documentation Improvement": "",
                "Considerations for Cost Effective Care Improvement": "",
            },
        },
        "Anticipatory Preventative Care": {"Item 1": "Screening"},
        "Follow Up Care": {"Item 1": "Follow up in 3 months"},
    }
    result = migrate_chart_review(data)
    assert "Anticipatory Preventative Care" in result["Plan"]
    assert "Follow Up Care" in result["Plan"]
    assert "Anticipatory Preventative Care" not in result
    assert "Follow Up Care" not in result


def test_migrate_feedback_produces_problems_array(v1_feedback_data):
    result = migrate_feedback(v1_feedback_data)
    assert "problems" in result["Feedback Details"]
    assert isinstance(result["Feedback Details"]["problems"], list)


def test_migrate_feedback_preserves_problem_count(v1_feedback_data):
    details = v1_feedback_data["Feedback Details"]
    v1_count = sum(1 for k in details if k.startswith("Problem") and isinstance(details[k], dict))
    result = migrate_feedback(v1_feedback_data)
    assert len(result["Feedback Details"]["problems"]) == v1_count


def test_migrate_feedback_preserves_skill_assessments(v1_feedback_data):
    result = migrate_feedback(v1_feedback_data)
    valid_assessments = {"Critical Gap", "Needs Improvement", "Meets Expectations", "Excellent"}
    for problem in result["Feedback Details"]["problems"]:
        assert problem["Skill Assessment"] in valid_assessments


def test_migrate_feedback_preserves_non_problem_sections(v1_feedback_data):
    result = migrate_feedback(v1_feedback_data)
    assert "Assessment Section" in result["Feedback Details"]
    assert "Feedback Summary" in result


def test_migrate_feedback_no_problem_keys_remain(v1_feedback_data):
    result = migrate_feedback(v1_feedback_data)
    for key in result["Feedback Details"]:
        assert not key.startswith("Problem"), f"Fixed problem key remains: {key}"
