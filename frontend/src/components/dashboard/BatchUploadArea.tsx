import { useState, useCallback, type DragEvent } from "react";
import { useModel } from "../../hooks/useModel";

interface Props {
  onJobStarted: (jobId: string) => void;
}

export function BatchUploadArea({ onJobStarted }: Props) {
  const { model } = useModel();
  const [files, setFiles] = useState<File[]>([]);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDrop = useCallback((e: DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const dropped = Array.from(e.dataTransfer.files).filter((f) =>
      f.name.endsWith(".txt")
    );
    setFiles((prev) => [...prev, ...dropped]);
  }, []);

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) {
        const selected = Array.from(e.target.files).filter((f) =>
          f.name.endsWith(".txt")
        );
        setFiles((prev) => [...prev, ...selected]);
      }
    },
    []
  );

  const handleUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    setError(null);

    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));

    try {
      const res = await fetch(
        `/api/inference?model=${encodeURIComponent(model)}&overwrite=true`,
        { method: "POST", body: formData }
      );
      if (!res.ok) {
        const body = await res.json();
        throw new Error(body.detail || `Upload failed: ${res.status}`);
      }
      const data = await res.json();
      setFiles([]);
      onJobStarted(data.job_id);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <h2 className="text-lg font-bold text-teal mb-3">Upload EMR Charts</h2>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragging
            ? "border-teal bg-teal/5"
            : "border-gray-300 hover:border-gray-400"
        }`}
      >
        <p className="text-gray-500 mb-2">
          Drag and drop .txt files here, or{" "}
          <label className="text-teal cursor-pointer hover:underline">
            browse
            <input
              type="file"
              multiple
              accept=".txt"
              className="hidden"
              onChange={handleFileSelect}
            />
          </label>
        </p>
      </div>

      {files.length > 0 && (
        <div className="mt-3">
          <ul className="text-sm space-y-1 mb-3">
            {files.map((f, i) => (
              <li key={i} className="flex items-center gap-2">
                <span className="text-gray-600">{f.name}</span>
                <button
                  type="button"
                  onClick={() => setFiles(files.filter((_, j) => j !== i))}
                  className="text-red-400 hover:text-red-600 text-xs"
                >
                  remove
                </button>
              </li>
            ))}
          </ul>
          <button
            type="button"
            onClick={handleUpload}
            disabled={uploading}
            className="bg-teal text-white px-4 py-2 rounded text-sm font-medium hover:bg-teal-light disabled:opacity-50 transition-colors"
          >
            {uploading ? "Uploading..." : `Run Pipeline (${files.length} files)`}
          </button>
        </div>
      )}

      {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
    </div>
  );
}
