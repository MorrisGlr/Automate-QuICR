import type { Feedback, SectionFeedback } from "../../types/feedback";
import { CollapsibleSection } from "../shared/CollapsibleSection";
import { SeverityBadge } from "../shared/SeverityBadge";
import { SkillBar } from "../shared/SkillBar";

function SectionBlock({ title, data }: { title: string; data?: SectionFeedback }) {
  if (!data) return null;
  return (
    <CollapsibleSection title={<h3 className="text-base font-bold text-teal">{title}</h3>}>
      <div className="mt-2 space-y-3">
        <div>
          <h4 className="text-sm font-bold text-green-700 mb-1">Strengths</h4>
          <p className="text-sm whitespace-pre-line">{data.Strengths}</p>
        </div>
        <div>
          <h4 className="text-sm font-bold text-orange mb-1">Areas for Improvement</h4>
          <p className="text-sm whitespace-pre-line">{data["Areas for Improvement"]}</p>
        </div>
      </div>
    </CollapsibleSection>
  );
}

export function FeedbackTab({ data }: { data: Feedback }) {
  const details = data["Feedback Details"];
  return (
    <div>
      {/* Summary */}
      <div className="bg-surface rounded-lg p-4 mb-4">
        <h3 className="text-sm font-bold text-teal mb-2">Feedback Summary</h3>
        <p className="text-sm">{data["Feedback Summary"]}</p>
      </div>

      {/* Assessment Section */}
      <SectionBlock title="Assessment Section" data={details["Assessment Section"]} />

      {/* Per-problem feedback */}
      <h2 className="text-lg font-bold text-teal mt-6 mb-3">
        Problem Feedback ({details.problems.length})
      </h2>
      {details.problems.map((p, i) => (
        <CollapsibleSection
          key={i}
          defaultOpen={i === 0}
          title={
            <span className="flex items-center">
              <h3 className="text-base font-bold">{p["Problem Name"]}</h3>
              <SeverityBadge severity={p.Severity} />
            </span>
          }
        >
          <div className="mt-3 space-y-3">
            <SkillBar assessment={p["Skill Assessment"]} />
            <div>
              <h4 className="text-sm font-bold text-green-700 mb-1">Strengths</h4>
              <p className="text-sm whitespace-pre-line">{p.Strengths}</p>
            </div>
            <div>
              <h4 className="text-sm font-bold text-orange mb-1">Areas for Improvement</h4>
              <p className="text-sm whitespace-pre-line">{p["Areas for Improvement"]}</p>
            </div>
          </div>
        </CollapsibleSection>
      ))}

      {/* Other sections */}
      <div className="mt-6">
        <SectionBlock
          title="Anticipatory Preventative Care Feedback"
          data={details["Anticipatory Preventative Care Section Feedback"]}
        />
        <SectionBlock title="Follow Up Care Feedback" data={details["Follow Up Care Feedback"]} />
      </div>

      {/* Overall Recommendations */}
      {details["Overall Recommendations"] && (
        <div className="mt-6 bg-teal/5 border-l-4 border-teal rounded-r-lg p-4">
          <h3 className="text-sm font-bold text-teal mb-2">Overall Recommendations</h3>
          <p className="text-sm whitespace-pre-line">{details["Overall Recommendations"]}</p>
        </div>
      )}
    </div>
  );
}
