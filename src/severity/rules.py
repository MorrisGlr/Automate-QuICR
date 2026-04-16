# Copyright (c) 2024-2026 Morris A. Aguilar. All Rights Reserved.
# Licensed under the Apache License, Version 2.0.
"""Post-hoc severity validation rules for chart review findings.

Validates and potentially escalates LLM-assigned severity based on:
1. Clinical keyword detection in problem text fields
2. Skill assessment floor mapping (from feedback)

Never downgrades severity — only escalates.
"""

SEVERITY_RANK = {"Critical": 4, "High": 3, "Moderate": 2, "Low": 1}
RANK_TO_SEVERITY = {v: k for k, v in SEVERITY_RANK.items()}

CRITICAL_KEYWORDS = [
    "anticoagulation gap",
    "uncontrolled",
    "suicidal",
    "anaphylaxis",
    "sepsis",
    "acute coronary",
    "stroke",
    "hemorrhage",
    "airway",
    "missing allergy",
    "drug interaction",
    "contraindicated",
]

HIGH_KEYWORDS = [
    "uncontrolled a1c",
    "uncontrolled blood pressure",
    "medication error",
    "missed diagnosis",
    "incomplete workup",
    "no follow-up for critical lab",
    "opioid without naloxone",
    "fall risk unaddressed",
]

MODERATE_KEYWORDS = [
    "suboptimal dose",
    "missing screening",
    "incomplete documentation",
    "generic alternative available",
    "no contingency plan",
]

# Problem text fields to scan for keywords
_TEXT_FIELDS = [
    "Decision Making and Diagnostic Plan",
    "Treatment/Medication Plan",
    "Contingency Planning",
    "Considerations for Documentation Improvement",
    "Considerations for Cost Effective Care Improvement",
    "Status",
]

# Skill assessment → minimum severity floor
_SKILL_FLOORS = {
    "Critical Gap": "High",
    "Needs Improvement": "Moderate",
}


def _scan_keywords(text: str) -> str | None:
    """Scan text for clinical keywords and return the highest matching severity.

    Returns None if no keywords match.
    """
    text_lower = text.lower()
    highest_rank = 0

    for keyword in CRITICAL_KEYWORDS:
        if keyword in text_lower:
            highest_rank = max(highest_rank, SEVERITY_RANK["Critical"])

    for keyword in HIGH_KEYWORDS:
        if keyword in text_lower:
            highest_rank = max(highest_rank, SEVERITY_RANK["High"])

    for keyword in MODERATE_KEYWORDS:
        if keyword in text_lower:
            highest_rank = max(highest_rank, SEVERITY_RANK["Moderate"])

    return RANK_TO_SEVERITY.get(highest_rank)


def validate_severity(
    problem: dict,
    skill_assessment: str | None = None,
) -> tuple[str, list[str]]:
    """Validate and potentially escalate a problem's severity.

    Args:
        problem: A single problem dict with "Severity" and text fields.
        skill_assessment: Optional skill assessment from feedback
                         (e.g., "Critical Gap", "Needs Improvement").

    Returns:
        Tuple of (validated_severity, list_of_adjustment_reasons).
    """
    current = problem.get("Severity", "Low")
    current_rank = SEVERITY_RANK.get(current, 1)
    adjustments = []

    # Step 1: Scan text fields for keyword matches
    combined_text = " ".join(
        problem.get(field, "") for field in _TEXT_FIELDS
    )
    keyword_severity = _scan_keywords(combined_text)

    if keyword_severity:
        keyword_rank = SEVERITY_RANK[keyword_severity]
        if keyword_rank > current_rank:
            adjustments.append(
                f"Escalated from {current} to {keyword_severity}: "
                f"keyword match in problem text"
            )
            current = keyword_severity
            current_rank = keyword_rank

    # Step 2: Apply skill assessment floor
    if skill_assessment and skill_assessment in _SKILL_FLOORS:
        floor = _SKILL_FLOORS[skill_assessment]
        floor_rank = SEVERITY_RANK[floor]
        if floor_rank > current_rank:
            adjustments.append(
                f"Escalated from {current} to {floor}: "
                f"skill assessment floor ({skill_assessment} → minimum {floor})"
            )
            current = floor
            current_rank = floor_rank

    return current, adjustments


def apply_severity_validation(
    chart_review: dict,
    feedback: dict | None = None,
) -> dict:
    """Apply severity validation across all problems in a chart review.

    Args:
        chart_review: Full chart review JSON output dict.
        feedback: Optional feedback JSON for skill assessment floors.

    Returns:
        The chart_review dict with validated severities (mutated in place).
        Appends "_severity_adjustments" metadata if any adjustments were made.
    """
    plan = chart_review.get("Plan", {})
    problems = plan.get("problems", [])

    # Build problem name → skill assessment mapping from feedback
    skill_map = {}
    if feedback:
        fb_details = feedback.get("Feedback Details", {})
        fb_problems = fb_details.get("problems", [])
        for fb_problem in fb_problems:
            name = fb_problem.get("Problem Name", "")
            skill = fb_problem.get("Skill Assessment", "")
            if name and skill:
                skill_map[name.lower()] = skill

    all_adjustments = []
    for problem in problems:
        pname = problem.get("Problem Name", "")
        skill = skill_map.get(pname.lower())

        validated, reasons = validate_severity(problem, skill)
        problem["Severity"] = validated

        if reasons:
            all_adjustments.append({
                "problem": pname,
                "adjustments": reasons,
            })

    if all_adjustments:
        chart_review["_severity_adjustments"] = all_adjustments

    return chart_review
