// Copyright (c) 2024-2026 Morris A. Aguilar. All Rights Reserved.
// Licensed under the Apache License, Version 2.0.
export interface EvidenceSource {
  title: string;
  source: string;
  year?: number;
  url?: string;
  unverified?: boolean;
}

export interface EvidenceGrade {
  certainty: "High" | "Moderate" | "Low" | "Very Low";
  sources: EvidenceSource[];
  rationale: string;
}

export interface Problem {
  "Problem Name": string;
  Status: string;
  "Decision Making and Diagnostic Plan": string;
  "Treatment/Medication Plan": string;
  "Contingency Planning": string;
  "Considerations for Documentation Improvement": string;
  "Considerations for Cost Effective Care Improvement": string;
  Severity?: "Critical" | "High" | "Moderate" | "Low";
  "Evidence Grade"?: EvidenceGrade;
}

export interface DrugPricing {
  Mention: string;
  "Generic Name": string;
  Source: string;
  "30 Day Cost": string;
}

export interface CareSection {
  "Item 1"?: string;
  "Item 2"?: string;
  "Item 3"?: string;
  "Item 4"?: string;
  "Item 5"?: string;
  "Item 6"?: string;
  "Considerations for Documentation Improvement"?: string;
}

export interface ChartReview {
  Patient: string;
  "Chief Concern": string;
  "Key Highlights for Medical Decision-Making (MDM) Improvement": string;
  Assessment: string;
  Plan: {
    problems: Problem[];
    "Anticipatory Preventative Care": CareSection;
    "Follow Up Care": CareSection;
    "Generic Drug Pricing"?: DrugPricing[];
  };
}
