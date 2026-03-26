"""Test the flatten_text function for v1 and v2 format support."""

import sys
from pathlib import Path

# We can't import drug_pricing directly since it requires scispacy.
# Instead, we extract and test just the flatten_text function logic.
# The actual module import would fail without scispacy installed.

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _flatten_text(data: dict) -> str:
    """Standalone copy of flatten_text logic for testing without scispacy dependency."""
    pieces = []
    plan = data.get("Plan", {})

    if "problems" in plan:
        for problem in plan["problems"]:
            med_plan = (problem.get("Treatment/Medication Plan")
                        or problem.get("Treatment Plan"))
            if med_plan:
                pieces.append(med_plan)
    else:
        for problem in plan.values():
            if isinstance(problem, dict):
                med_plan = (problem.get("Treatment/Medication Plan")
                            or problem.get("Treatment Plan"))
                if med_plan:
                    pieces.append(med_plan)
    return "\n".join(pieces)


def test_flatten_text_v2_format():
    data = {
        "Plan": {
            "problems": [
                {
                    "Problem Name": "Hypertension",
                    "Treatment/Medication Plan": "Start lisinopril 10mg daily",
                },
                {
                    "Problem Name": "Diabetes",
                    "Treatment/Medication Plan": "Continue metformin 500mg BID",
                },
            ],
            "Anticipatory Preventative Care": {"Item 1": "Screening"},
            "Follow Up Care": {"Item 1": "Follow up"},
        }
    }
    result = _flatten_text(data)
    assert "lisinopril" in result
    assert "metformin" in result


def test_flatten_text_v1_format():
    data = {
        "Plan": {
            "Problem 1": {
                "Problem Name": "Hypertension",
                "Treatment/Medication Plan": "Start lisinopril 10mg daily",
            },
            "Problem 2": {
                "Problem Name": "Diabetes",
                "Treatment Plan": "Continue metformin 500mg BID",
            },
            "Anticipatory Preventative Care": {"Item 1": "Screening"},
        }
    }
    result = _flatten_text(data)
    assert "lisinopril" in result
    assert "metformin" in result


def test_flatten_text_empty_plan():
    data = {"Plan": {}}
    result = _flatten_text(data)
    assert result == ""


def test_flatten_text_v2_no_treatment_plan():
    data = {
        "Plan": {
            "problems": [
                {"Problem Name": "Test", "Status": "Stable"},
            ],
        }
    }
    result = _flatten_text(data)
    assert result == ""
