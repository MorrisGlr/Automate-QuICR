// Copyright (c) 2024-2026 Morris A. Aguilar. All Rights Reserved.
// Licensed under the Apache License, Version 2.0.
import { apiFetch } from "./client";
import type { AggregateResponse } from "../types/aggregate";

export function getAggregate(model?: string): Promise<AggregateResponse> {
  const params = model ? `?model=${encodeURIComponent(model)}` : "";
  return apiFetch<AggregateResponse>(`/aggregate${params}`);
}
