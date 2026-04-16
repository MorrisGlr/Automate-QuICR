// Copyright (c) 2024-2026 Morris A. Aguilar. All Rights Reserved.
// Licensed under the Apache License, Version 2.0.
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
