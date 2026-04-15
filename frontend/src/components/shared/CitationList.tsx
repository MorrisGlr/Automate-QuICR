import type { EvidenceGrade } from "../../types/chart-review";

export function CitationList({ grade }: { grade?: EvidenceGrade }) {
  if (!grade || !grade.sources || grade.sources.length === 0) return null;
  return (
    <div className="mt-3">
      <h4 className="text-sm font-bold text-teal mb-1">Evidence Sources</h4>
      <p className="text-xs text-gray-500 mb-2 italic">{grade.rationale}</p>
      <ul className="text-sm space-y-1">
        {grade.sources.map((s, i) => (
          <li key={i} className={s.unverified ? "italic text-gray-400" : ""}>
            {s.url ? (
              <a
                href={s.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-teal hover:underline"
              >
                {s.title}
              </a>
            ) : (
              <span>{s.title}</span>
            )}
            <span className="text-gray-400 ml-1">
              — {s.source}
              {s.year ? `, ${s.year}` : ""}
            </span>
            {s.unverified && (
              <span className="text-orange text-xs ml-1">* unverified</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
