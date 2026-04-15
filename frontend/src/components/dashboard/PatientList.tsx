import { Link } from "react-router-dom";
import type { PatientSummary } from "../../types/patient";
import { SeverityBadge } from "../shared/SeverityBadge";

export function PatientList({ patients }: { patients: PatientSummary[] }) {
  if (patients.length === 0) {
    return <p className="text-gray-500">No patients found for this model.</p>;
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b-2 border-teal bg-teal/5">
            <th className="px-4 py-3 text-sm font-bold text-teal">Patient</th>
            <th className="px-4 py-3 text-sm font-bold text-teal">Chief Concern</th>
            <th className="px-4 py-3 text-sm font-bold text-teal text-center">Problems</th>
            <th className="px-4 py-3 text-sm font-bold text-teal text-center">Severity</th>
            <th className="px-4 py-3 text-sm font-bold text-teal text-center">Feedback</th>
          </tr>
        </thead>
        <tbody>
          {patients.map((p) => (
            <tr key={p.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3">
                <Link
                  to={`/patients/${p.id}`}
                  className="text-teal font-medium hover:underline no-underline"
                >
                  {p.display_name}
                </Link>
              </td>
              <td className="px-4 py-3 text-sm text-gray-600 max-w-md truncate">
                {p.chief_concern}
              </td>
              <td className="px-4 py-3 text-sm text-center">{p.problem_count}</td>
              <td className="px-4 py-3 text-center">
                <SeverityBadge severity={p.worst_severity} />
                {!p.worst_severity && <span className="text-xs text-gray-400">--</span>}
              </td>
              <td className="px-4 py-3 text-center">
                {p.has_feedback ? (
                  <span className="text-green-600 text-sm">Available</span>
                ) : (
                  <span className="text-gray-400 text-sm">--</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
