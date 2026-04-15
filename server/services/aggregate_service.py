import json
from pathlib import Path

from server.models import AggregatedProblem, AggregateResponse

ASSESSMENT_RANK = {
    "Critical Gap": 1,
    "Needs Improvement": 2,
    "Meets Expectations": 3,
    "Excellent": 4,
}

SEVERITY_RANK = {"Critical": 4, "High": 3, "Moderate": 2, "Low": 1}


def compute_aggregate(
    model_name: str, output_path: Path
) -> AggregateResponse:
    fb_dir = output_path / model_name / "cr_feedback"
    problems: dict[str, dict] = {}

    if fb_dir.is_dir():
        for f in sorted(fb_dir.iterdir()):
            if not f.name.endswith(".json"):
                continue
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

            details = data.get("Feedback Details", {})
            problem_list = details.get("problems", [])
            if not problem_list:
                # v1 fallback
                problem_list = [
                    v for k, v in details.items()
                    if k.startswith("Problem") and isinstance(v, dict)
                ]

            for content in problem_list:
                pname = content.get("Problem Name")
                if not pname:
                    continue

                entry = problems.setdefault(pname, {
                    "Strengths": "",
                    "Areas for Improvement": "",
                    "Skill Assessment": "Excellent",
                    "Severity": "Low",
                })

                s = content.get("Strengths", "").strip()
                if s:
                    entry["Strengths"] += (s if not entry["Strengths"] else "\n" + s)

                a = content.get("Areas for Improvement", "").strip()
                if a:
                    entry["Areas for Improvement"] += (
                        a if not entry["Areas for Improvement"] else "\n" + a
                    )

                current = entry["Skill Assessment"]
                new = content.get("Skill Assessment", current)
                if ASSESSMENT_RANK.get(new, 0) < ASSESSMENT_RANK.get(current, 0):
                    entry["Skill Assessment"] = new

                current_sev = entry["Severity"]
                new_sev = content.get("Severity", current_sev)
                if SEVERITY_RANK.get(new_sev, 0) > SEVERITY_RANK.get(current_sev, 0):
                    entry["Severity"] = new_sev

    # Sort by worst severity
    sorted_items = sorted(
        problems.items(),
        key=lambda item: SEVERITY_RANK.get(item[1].get("Severity", "Low"), 0),
        reverse=True,
    )

    severity_dist = {"Critical": 0, "High": 0, "Moderate": 0, "Low": 0}
    skill_dist: dict[str, int] = {}
    result_problems: list[AggregatedProblem] = []

    for pname, vals in sorted_items:
        sev = vals.get("Severity", "Low")
        if sev in severity_dist:
            severity_dist[sev] += 1

        skill = vals["Skill Assessment"]
        skill_dist[skill] = skill_dist.get(skill, 0) + 1

        result_problems.append(AggregatedProblem(
            problem_name=pname,
            strengths=vals["Strengths"],
            areas_for_improvement=vals["Areas for Improvement"],
            skill_assessment=skill,
            severity=sev,
        ))

    return AggregateResponse(
        problems=result_problems,
        severity_distribution=severity_dist,
        skill_distribution=skill_dist,
    )
