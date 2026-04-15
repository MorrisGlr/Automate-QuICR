import { useState, useEffect, useCallback } from "react";
import { getPatients } from "../api/patients";
import type { PatientSummary } from "../types/patient";

export function usePatients(model: string) {
  const [patients, setPatients] = useState<PatientSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshCounter, setRefreshCounter] = useState(0);

  useEffect(() => {
    if (!model) return;
    setLoading(true);
    setError(null);
    getPatients(model)
      .then(setPatients)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [model, refreshCounter]);

  const refresh = useCallback(() => setRefreshCounter((c) => c + 1), []);

  return { patients, loading, error, refresh };
}
