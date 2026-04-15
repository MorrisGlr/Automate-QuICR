import { useModel } from "../../hooks/useModel";
import { useAggregate } from "../../hooks/useAggregate";
import { SeverityBadge } from "../shared/SeverityBadge";
import { SkillBar } from "../shared/SkillBar";
import { CollapsibleSection } from "../shared/CollapsibleSection";

const SEV_COLORS: Record<string, string> = {
  Critical: "bg-severity-critical",
  High: "bg-severity-high",
  Moderate: "bg-severity-moderate",
  Low: "bg-gray-300",
};

function SeverityDistribution({ dist }: { dist: Record<string, number> }) {
  const total = Object.values(dist).reduce((a, b) => a + b, 0);
  if (total === 0) return null;
  return (
    <div className="bg-surface rounded-lg p-4 mb-6">
      <h2 className="text-lg font-bold text-teal mb-3">Severity Distribution</h2>
      <div className="space-y-2">
        {Object.entries(dist).map(([level, count]) => (
          <div key={level} className="flex items-center gap-3">
            <span className="text-sm w-20 font-medium">{level}</span>
            <div className="flex-1 bg-gray-200 rounded h-5 overflow-hidden">
              <div
                className={`h-full rounded ${SEV_COLORS[level] ?? "bg-gray-400"}`}
                style={{ width: total > 0 ? `${(count / total) * 100}%` : "0%" }}
              />
            </div>
            <span className="text-sm text-gray-600 w-8 text-right">{count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function AggregateView() {
  const { model } = useModel();
  const { data, loading, error } = useAggregate(model);

  if (loading) return <p className="text-gray-500">Loading aggregate data...</p>;
  if (error) return <p className="text-red-500">Error: {error}</p>;
  if (!data) return null;

  return (
    <div>
      <h1 className="text-3xl font-bold text-teal mb-6">Aggregated Feedback Report</h1>

      <SeverityDistribution dist={data.severity_distribution} />

      {/* Skill distribution summary */}
      <div className="bg-surface rounded-lg p-4 mb-6">
        <h2 className="text-lg font-bold text-teal mb-3">Skill Assessment Distribution</h2>
        <div className="flex gap-4 flex-wrap">
          {Object.entries(data.skill_distribution).map(([skill, count]) => (
            <span
              key={skill}
              className="text-sm bg-white px-3 py-1 rounded shadow-sm"
            >
              <span className="font-medium">{skill}:</span> {count}
            </span>
          ))}
        </div>
      </div>

      {/* Problem list */}
      <h2 className="text-lg font-bold text-teal mb-3">
        Problems ({data.problems.length})
      </h2>
      {data.problems.map((p, i) => (
        <CollapsibleSection
          key={i}
          defaultOpen={i < 3}
          title={
            <span className="flex items-center">
              <h3 className="text-base font-bold">{p.problem_name}</h3>
              <SeverityBadge severity={p.severity} />
            </span>
          }
        >
          <div className="mt-3 space-y-3">
            <SkillBar assessment={p.skill_assessment} />
            <div>
              <h4 className="text-sm font-bold text-green-700 mb-1">Strengths</h4>
              <p className="text-sm whitespace-pre-line">{p.strengths}</p>
            </div>
            <div>
              <h4 className="text-sm font-bold text-orange mb-1">Areas for Improvement</h4>
              <p className="text-sm whitespace-pre-line">{p.areas_for_improvement}</p>
            </div>
          </div>
        </CollapsibleSection>
      ))}
    </div>
  );
}
