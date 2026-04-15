import type { ChartReview } from "./chart-review";
import type { Feedback } from "./feedback";

export interface PatientSummary {
  id: string;
  display_name: string;
  chief_concern: string;
  worst_severity: string | null;
  problem_count: number;
  has_feedback: boolean;
  has_drug_pricing: boolean;
}

export interface PatientDetail {
  id: string;
  chart_review: ChartReview | null;
  feedback: Feedback | null;
}
