// Copyright (c) 2024-2026 Morris A. Aguilar. All Rights Reserved.
// Licensed under the Apache License, Version 2.0.
import { useState, useEffect } from "react";
import { getAggregate } from "../api/aggregate";
import type { AggregateResponse } from "../types/aggregate";

export function useAggregate(model: string) {
  const [data, setData] = useState<AggregateResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!model) return;
    setLoading(true);
    setError(null);
    getAggregate(model)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [model]);

  return { data, loading, error };
}
