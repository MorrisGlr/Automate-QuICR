// Copyright (c) 2024-2026 Morris A. Aguilar. All Rights Reserved.
// Licensed under the Apache License, Version 2.0.
import { useState, useEffect } from "react";

export interface PipelineEvent {
  stage: string;
  file: string;
  progress: number;
  total: number;
  error?: string;
  results?: {
    processed: number;
    failures: { file: string; error: string }[];
  };
}

export function useSSE(jobId: string | null) {
  const [events, setEvents] = useState<PipelineEvent[]>([]);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    if (!jobId) return;
    setEvents([]);
    setIsComplete(false);

    const source = new EventSource(`/api/inference/status?job_id=${jobId}`);

    source.onmessage = (e) => {
      const event: PipelineEvent = JSON.parse(e.data);
      setEvents((prev) => [...prev, event]);
      if (event.stage === "all_complete") {
        setIsComplete(true);
        source.close();
      }
    };

    source.onerror = () => {
      source.close();
    };

    return () => source.close();
  }, [jobId]);

  return { events, isComplete };
}
