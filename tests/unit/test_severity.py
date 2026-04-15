"""Tests for severity validation rules."""

import pytest

from src.severity.rules import (
    CRITICAL_KEYWORDS,
    HIGH_KEYWORDS,
    MODERATE_KEYWORDS,
    SEVERITY_RANK,
    apply_severity_validation,
    validate_severity,
)


class TestValidateSeverity:
    """Tests for the validate_severity function."""

    def test_no_escalation_when_correct(self):
        """LLM-assigned severity should be preserved when no keywords trigger escalation."""
        problem = {
            "Problem Name": "Well-controlled Diabetes",
            "Severity": "Low",
            "Status": "Stable, at goal",
            "Decision Making and Diagnostic Plan": "Continue current regimen.",
            "Treatment/Medication Plan": "Metformin 500mg BID.",
            "Contingency Planning": "Recheck A1c in 3 months.",
        }
        severity, adjustments = validate_severity(problem)
        assert severity == "Low"
        assert adjustments == []

    def test_escalation_critical_keyword(self):
        """Should escalate to Critical when critical keywords are found."""
        problem = {
            "Problem Name": "Atrial Fibrillation",
            "Severity": "Moderate",
            "Status": "Active",
            "Decision Making and Diagnostic Plan": "Patient has anticoagulation gap of 2 weeks.",
            "Treatment/Medication Plan": "Restart apixaban.",
        }
        severity, adjustments = validate_severity(problem)
        assert severity == "Critical"
        assert len(adjustments) == 1
        assert "keyword" in adjustments[0].lower()

    def test_escalation_high_keyword(self):
        """Should escalate to High when high keywords are found."""
        problem = {
            "Problem Name": "Diabetes",
            "Severity": "Low",
            "Status": "Patient has elevated A1c.",
            "Treatment/Medication Plan": "Medication error identified — wrong dose of insulin prescribed.",
        }
        severity, adjustments = validate_severity(problem)
        assert severity == "High"
        assert len(adjustments) == 1

    def test_escalation_moderate_keyword(self):
        """Should escalate to Moderate when moderate keywords are found."""
        problem = {
            "Problem Name": "Hypertension",
            "Severity": "Low",
            "Status": "Stable",
            "Treatment/Medication Plan": "Patient on suboptimal dose of lisinopril.",
        }
        severity, adjustments = validate_severity(problem)
        assert severity == "Moderate"
        assert len(adjustments) == 1

    def test_no_downgrade(self):
        """Should never downgrade severity even if no keywords match."""
        problem = {
            "Problem Name": "Simple Finding",
            "Severity": "High",
            "Status": "Routine check",
            "Decision Making and Diagnostic Plan": "Standard evaluation.",
        }
        severity, adjustments = validate_severity(problem)
        assert severity == "High"
        assert adjustments == []

    def test_skill_assessment_floor_critical_gap(self):
        """Critical Gap skill assessment should set severity floor to High."""
        problem = {
            "Problem Name": "Missed Finding",
            "Severity": "Low",
            "Status": "Stable",
        }
        severity, adjustments = validate_severity(problem, skill_assessment="Critical Gap")
        assert severity == "High"
        assert len(adjustments) == 1
        assert "floor" in adjustments[0].lower()

    def test_skill_assessment_floor_needs_improvement(self):
        """Needs Improvement should set severity floor to Moderate."""
        problem = {
            "Problem Name": "Documentation Gap",
            "Severity": "Low",
            "Status": "Stable",
        }
        severity, adjustments = validate_severity(problem, skill_assessment="Needs Improvement")
        assert severity == "Moderate"
        assert len(adjustments) == 1

    def test_skill_floor_does_not_downgrade(self):
        """Skill assessment floor should not downgrade existing severity."""
        problem = {
            "Problem Name": "Critical Issue",
            "Severity": "Critical",
            "Status": "Active sepsis concern",
        }
        severity, adjustments = validate_severity(problem, skill_assessment="Needs Improvement")
        assert severity == "Critical"

    def test_keyword_plus_skill_combined(self):
        """Both keyword escalation and skill floor should apply, taking the highest."""
        problem = {
            "Problem Name": "Complex Issue",
            "Severity": "Low",
            "Status": "Patient has incomplete documentation of drug interaction.",
        }
        severity, adjustments = validate_severity(problem, skill_assessment="Critical Gap")
        # "drug interaction" → Critical, skill floor → High; Critical wins
        assert severity == "Critical"
        assert len(adjustments) >= 1

    def test_missing_severity_defaults_to_low(self):
        """Missing Severity field should default to Low."""
        problem = {"Problem Name": "Test", "Status": "OK"}
        severity, adjustments = validate_severity(problem)
        assert severity == "Low"


class TestApplySeverityValidation:
    """Tests for apply_severity_validation on full chart review."""

    def test_basic_application(self):
        chart_review = {
            "Plan": {
                "problems": [
                    {
                        "Problem Name": "AF",
                        "Severity": "Low",
                        "Status": "anticoagulation gap present",
                    },
                    {
                        "Problem Name": "HTN",
                        "Severity": "Low",
                        "Status": "Stable",
                    },
                ]
            }
        }
        result = apply_severity_validation(chart_review)
        assert result["Plan"]["problems"][0]["Severity"] == "Critical"
        assert result["Plan"]["problems"][1]["Severity"] == "Low"
        assert "_severity_adjustments" in result
        assert len(result["_severity_adjustments"]) == 1

    def test_with_feedback_skill_floors(self):
        chart_review = {
            "Plan": {
                "problems": [
                    {"Problem Name": "Issue A", "Severity": "Low", "Status": "OK"},
                ]
            }
        }
        feedback = {
            "Feedback Details": {
                "problems": [
                    {
                        "Problem Name": "Issue A",
                        "Skill Assessment": "Critical Gap",
                        "Strengths": "",
                        "Areas for Improvement": "",
                    }
                ]
            }
        }
        result = apply_severity_validation(chart_review, feedback)
        assert result["Plan"]["problems"][0]["Severity"] == "High"

    def test_no_adjustments_no_metadata(self):
        chart_review = {
            "Plan": {
                "problems": [
                    {"Problem Name": "Fine", "Severity": "High", "Status": "OK"},
                ]
            }
        }
        result = apply_severity_validation(chart_review)
        assert "_severity_adjustments" not in result
