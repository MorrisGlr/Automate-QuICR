export interface AggregatedProblem {
  problem_name: string;
  strengths: string;
  areas_for_improvement: string;
  skill_assessment: string;
  severity: string;
}

export interface AggregateResponse {
  problems: AggregatedProblem[];
  severity_distribution: Record<string, number>;
  skill_distribution: Record<string, number>;
}
