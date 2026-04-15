from pydantic import BaseModel


class PatientSummary(BaseModel):
    id: str
    display_name: str
    chief_concern: str
    worst_severity: str | None = None
    problem_count: int = 0
    has_feedback: bool = False
    has_drug_pricing: bool = False


class PatientDetail(BaseModel):
    id: str
    chart_review: dict | None = None
    feedback: dict | None = None


class AggregatedProblem(BaseModel):
    problem_name: str
    strengths: str
    areas_for_improvement: str
    skill_assessment: str
    severity: str


class AggregateResponse(BaseModel):
    problems: list[AggregatedProblem]
    severity_distribution: dict[str, int]
    skill_distribution: dict[str, int]
