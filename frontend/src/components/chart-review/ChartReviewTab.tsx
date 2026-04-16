// Copyright (c) 2024-2026 Morris A. Aguilar. All Rights Reserved.
// Licensed under the Apache License, Version 2.0.
import type { ChartReview } from "../../types/chart-review";
import { CollapsibleSection } from "../shared/CollapsibleSection";
import { SeverityBadge } from "../shared/SeverityBadge";
import { EvidenceGradeBadge } from "../shared/EvidenceGradeBadge";
import { CitationList } from "../shared/CitationList";
import { DrugPricingTable } from "../shared/DrugPricingTable";

function Field({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="grid grid-cols-[200px_1fr] gap-2 py-2 border-b border-gray-50 last:border-0">
      <span className={`text-sm font-medium ${highlight ? "text-orange" : "text-gray-600"}`}>
        {label}
      </span>
      <div className="text-sm whitespace-pre-line">{value}</div>
    </div>
  );
}

function CareSection({ title, data }: { title: string; data: Record<string, string> }) {
  const items = Object.entries(data).filter(
    ([k]) => k.startsWith("Item") && data[k]
  );
  const docImprovement = data["Considerations for Documentation Improvement"];

  if (items.length === 0) return null;
  return (
    <CollapsibleSection title={<h3 className="text-base font-bold text-teal">{title}</h3>}>
      <ul className="text-sm space-y-1 mt-2">
        {items.map(([k, v]) => (
          <li key={k}>{v}</li>
        ))}
      </ul>
      {docImprovement && (
        <div className="mt-3">
          <Field
            label="Documentation Improvement"
            value={docImprovement}
            highlight
          />
        </div>
      )}
    </CollapsibleSection>
  );
}

export function ChartReviewTab({ data }: { data: ChartReview }) {
  return (
    <div>
      {/* Patient header */}
      <div className="bg-surface rounded-lg p-4 mb-4">
        <h2 className="text-xl font-bold text-teal">{data.Patient}</h2>
        <p className="text-sm text-gray-600 mt-1">
          <span className="font-medium">Chief Concern:</span> {data["Chief Concern"]}
        </p>
      </div>

      {/* MDM Highlights */}
      <div className="bg-teal/5 border-l-4 border-teal rounded-r-lg p-4 mb-4">
        <h3 className="text-sm font-bold text-teal mb-2">Key Highlights for MDM Improvement</h3>
        <div className="text-sm whitespace-pre-line">
          {data["Key Highlights for Medical Decision-Making (MDM) Improvement"]}
        </div>
      </div>

      {/* Assessment */}
      <CollapsibleSection
        title={<h3 className="text-base font-bold text-teal">Assessment</h3>}
        defaultOpen
      >
        <div className="text-sm whitespace-pre-line mt-2">{data.Assessment}</div>
      </CollapsibleSection>

      {/* Problems */}
      <h2 className="text-lg font-bold text-teal mt-6 mb-3">
        Plan ({data.Plan.problems.length} problems)
      </h2>
      {data.Plan.problems.map((p, i) => (
        <CollapsibleSection
          key={i}
          defaultOpen={i === 0}
          title={
            <span className="flex items-center">
              <h3 className="text-base font-bold">{p["Problem Name"]}</h3>
              <SeverityBadge severity={p.Severity} />
              <EvidenceGradeBadge grade={p["Evidence Grade"]} />
            </span>
          }
        >
          <div className="mt-2">
            <Field label="Status" value={p.Status} />
            <Field label="Decision Making & Diagnostic Plan" value={p["Decision Making and Diagnostic Plan"]} />
            <Field label="Treatment/Medication Plan" value={p["Treatment/Medication Plan"]} />
            <Field label="Contingency Planning" value={p["Contingency Planning"]} />
            <Field
              label="Documentation Improvement"
              value={p["Considerations for Documentation Improvement"]}
              highlight
            />
            <Field
              label="Cost Effective Care"
              value={p["Considerations for Cost Effective Care Improvement"]}
              highlight
            />
            <CitationList grade={p["Evidence Grade"]} />
          </div>
        </CollapsibleSection>
      ))}

      {/* Drug Pricing */}
      <DrugPricingTable pricing={data.Plan["Generic Drug Pricing"]} />

      {/* Preventative Care & Follow Up */}
      <div className="mt-6">
        <CareSection
          title="Anticipatory Preventative Care"
          data={data.Plan["Anticipatory Preventative Care"] as unknown as Record<string, string>}
        />
        <CareSection
          title="Follow Up Care"
          data={data.Plan["Follow Up Care"] as unknown as Record<string, string>}
        />
      </div>
    </div>
  );
}
