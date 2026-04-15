const STYLES: Record<string, string> = {
  Critical: "bg-severity-critical text-white",
  High: "bg-severity-high text-white",
  Moderate: "bg-severity-moderate text-gray-800",
};

export function SeverityBadge({ severity }: { severity?: string | null }) {
  if (!severity || severity === "Low") return null;
  const cls = STYLES[severity] ?? "";
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-xs font-bold ml-2 align-middle ${cls}`}
    >
      {severity}
    </span>
  );
}
