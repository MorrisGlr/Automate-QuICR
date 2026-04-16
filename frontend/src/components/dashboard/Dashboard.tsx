// Copyright (c) 2024-2026 Morris A. Aguilar. All Rights Reserved.
// Licensed under the Apache License, Version 2.0.
import { useState } from "react";
import { useModel } from "../../hooks/useModel";
import { usePatients } from "../../hooks/usePatients";
import { PatientList } from "./PatientList";
import { BatchUploadArea } from "./BatchUploadArea";
import { QueueStatus } from "./QueueStatus";

export function Dashboard() {
  const { model } = useModel();
  const { patients, loading, error, refresh } = usePatients(model);
  const [jobId, setJobId] = useState<string | null>(null);

  const handleComplete = () => {
    setJobId(null);
    refresh();
  };

  return (
    <div>
      <h1 className="text-3xl font-bold text-teal mb-6">Patient Dashboard</h1>

      <BatchUploadArea onJobStarted={setJobId} />
      <QueueStatus jobId={jobId} onComplete={handleComplete} />

      {loading && <p className="text-gray-500">Loading patients...</p>}
      {error && <p className="text-red-500">Error: {error}</p>}
      {!loading && !error && <PatientList patients={patients} />}
    </div>
  );
}
