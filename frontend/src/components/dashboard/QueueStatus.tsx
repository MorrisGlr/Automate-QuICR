import { useSSE, type PipelineEvent } from "../../hooks/useSSE";

const STAGE_LABELS: Record<string, string> = {
  retrieving_evidence: "Retrieving evidence",
  running_inference_cr: "Running chart review inference",
  running_inference_fb: "Running feedback inference",
  extracting_medications: "Extracting medications",
  validating_severity: "Validating severity",
  generating_pdf: "Generating PDFs",
  complete: "Complete",
  failed: "Failed",
  all_complete: "All complete",
};

function FileProgress({ events, filename }: { events: PipelineEvent[]; filename: string }) {
  const fileEvents = events.filter((e) => e.file === filename);
  const latest = fileEvents[fileEvents.length - 1];
  if (!latest) return null;

  const isFailed = latest.stage === "failed";
  const isDone = latest.stage === "complete";

  return (
    <div className="flex items-center gap-3 py-2 border-b border-gray-50 last:border-0">
      <span className="text-sm text-gray-700 w-48 truncate">{filename}</span>
      <span
        className={`text-xs font-medium px-2 py-0.5 rounded ${
          isFailed
            ? "bg-red-100 text-red-700"
            : isDone
              ? "bg-green-100 text-green-700"
              : "bg-blue-100 text-blue-700"
        }`}
      >
        {STAGE_LABELS[latest.stage] ?? latest.stage}
      </span>
      {isFailed && latest.error && (
        <span className="text-xs text-red-500 truncate">{latest.error}</span>
      )}
      {!isDone && !isFailed && (
        <span className="inline-block w-4 h-4 border-2 border-teal border-t-transparent rounded-full animate-spin" />
      )}
    </div>
  );
}

interface Props {
  jobId: string | null;
  onComplete: () => void;
}

export function QueueStatus({ jobId, onComplete }: Props) {
  const { events, isComplete } = useSSE(jobId);

  if (!jobId) return null;

  // Derive unique filenames from events
  const filenames = [...new Set(events.filter((e) => e.file).map((e) => e.file))];
  const lastEvent = events[events.length - 1];
  const results = lastEvent?.results;

  if (isComplete) {
    // Trigger refresh after a short delay
    setTimeout(onComplete, 500);
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <h2 className="text-lg font-bold text-teal mb-3">
        Pipeline Progress
        {isComplete && (
          <span className="text-sm font-normal text-green-600 ml-2">
            Complete
          </span>
        )}
      </h2>

      <div>
        {filenames.map((f) => (
          <FileProgress key={f} events={events} filename={f} />
        ))}
      </div>

      {isComplete && results && (
        <div className="mt-4 text-sm">
          <p className="text-green-700">
            Processed: {results.processed} / {lastEvent.total}
          </p>
          {results.failures.length > 0 && (
            <div className="mt-2">
              <p className="text-red-600 font-medium">Failures:</p>
              <ul className="text-red-500 text-xs mt-1">
                {results.failures.map((f, i) => (
                  <li key={i}>
                    {f.file}: {f.error}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
