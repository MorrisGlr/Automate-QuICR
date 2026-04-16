// Copyright (c) 2024-2026 Morris A. Aguilar. All Rights Reserved.
// Licensed under the Apache License, Version 2.0.
import { useState, useEffect } from "react";
import { getPatient } from "../api/patients";
import type { PatientDetail } from "../types/patient";

export function usePatient(id: string, model: string) {
  const [patient, setPatient] = useState<PatientDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id || !model) return;
    setLoading(true);
    setError(null);
    getPatient(id, model)
      .then(setPatient)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id, model]);

  return { patient, loading, error };
}
