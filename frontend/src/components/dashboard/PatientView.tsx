import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useModel } from "../../hooks/useModel";
import { usePatient } from "../../hooks/usePatient";
import { ChartReviewTab } from "../chart-review/ChartReviewTab";
import { FeedbackTab } from "../feedback/FeedbackTab";

export function PatientView() {
  const { id } = useParams<{ id: string }>();
  const { model } = useModel();
  const { patient, loading, error } = usePatient(id!, model);
  const [tab, setTab] = useState<"chart-review" | "feedback">("chart-review");

  if (loading) return <p className="text-gray-500">Loading patient data...</p>;
  if (error) return <p className="text-red-500">Error: {error}</p>;
  if (!patient) return <p className="text-red-500">Patient not found.</p>;

  const tabs = [
    { key: "chart-review" as const, label: "Chart Review", available: !!patient.chart_review },
    { key: "feedback" as const, label: "Feedback", available: !!patient.feedback },
  ];

  return (
    <div>
      <Link to="/" className="text-sm text-teal hover:underline no-underline mb-4 inline-block">
        &larr; Back to Dashboard
      </Link>

      {/* Tab bar */}
      <div className="flex border-b border-gray-200 mb-6">
        {tabs.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => t.available && setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t.key
                ? "border-teal text-teal"
                : t.available
                  ? "border-transparent text-gray-500 hover:text-gray-700"
                  : "border-transparent text-gray-300 cursor-not-allowed"
            }`}
          >
            {t.label}
            {!t.available && <span className="ml-1 text-xs">(N/A)</span>}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === "chart-review" && patient.chart_review && (
        <ChartReviewTab data={patient.chart_review} />
      )}
      {tab === "feedback" && patient.feedback && (
        <FeedbackTab data={patient.feedback} />
      )}
    </div>
  );
}
