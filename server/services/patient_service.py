# Copyright (c) 2024-2026 Morris A. Aguilar. All Rights Reserved.
# Licensed under the Apache License, Version 2.0.
import json
import re
from pathlib import Path

from server.models import PatientDetail, PatientSummary

CR_PATTERN = re.compile(r"^(.+)_chart_review\.json$")
PRICING_PATTERN = re.compile(r"^(.+)_chart_review_pricing\.json$")
FB_PATTERN = re.compile(r"^(.+)_cr_feedback\.json$")

SEVERITY_RANK = {"Critical": 4, "High": 3, "Moderate": 2, "Low": 1}


def _read_json(path: Path) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def _worst_severity(data: dict) -> str | None:
    problems = data.get("Plan", {}).get("problems", [])
    worst = None
    worst_rank = 0
    for p in problems:
        sev = p.get("Severity")
        if sev and SEVERITY_RANK.get(sev, 0) > worst_rank:
            worst = sev
            worst_rank = SEVERITY_RANK[sev]
    return worst


def list_models(output_path: Path) -> list[str]:
    if not output_path.is_dir():
        return []
    return sorted(
        d.name for d in output_path.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )


def discover_patients(
    model_name: str, output_path: Path
) -> list[PatientSummary]:
    cr_dir = output_path / model_name / "chart_review"
    if not cr_dir.is_dir():
        return []

    pricing_dir = cr_dir / "drug_pricing"
    fb_dir = output_path / model_name / "cr_feedback"

    patients: list[PatientSummary] = []
    for f in sorted(cr_dir.iterdir()):
        m = CR_PATTERN.match(f.name)
        if not m:
            continue
        patient_id = m.group(1)
        data = _read_json(f)
        if data is None:
            continue

        problems = data.get("Plan", {}).get("problems", [])

        patients.append(PatientSummary(
            id=patient_id,
            display_name=data.get("Patient", patient_id),
            chief_concern=data.get("Chief Concern", ""),
            worst_severity=_worst_severity(data),
            problem_count=len(problems),
            has_feedback=(fb_dir / f"{patient_id}_cr_feedback.json").is_file(),
            has_drug_pricing=(
                pricing_dir / f"{patient_id}_chart_review_pricing.json"
            ).is_file(),
        ))

    return patients


def get_patient_detail(
    patient_id: str, model_name: str, output_path: Path
) -> PatientDetail | None:
    cr_dir = output_path / model_name / "chart_review"
    pricing_path = cr_dir / "drug_pricing" / f"{patient_id}_chart_review_pricing.json"
    cr_path = cr_dir / f"{patient_id}_chart_review.json"

    # Prefer drug-pricing-enriched version
    chart_review = _read_json(pricing_path) or _read_json(cr_path)
    if chart_review is None:
        return None

    fb_path = output_path / model_name / "cr_feedback" / f"{patient_id}_cr_feedback.json"
    feedback = _read_json(fb_path)

    return PatientDetail(
        id=patient_id,
        chart_review=chart_review,
        feedback=feedback,
    )
