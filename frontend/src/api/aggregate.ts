import { apiFetch } from "./client";
import type { AggregateResponse } from "../types/aggregate";

export function getAggregate(model?: string): Promise<AggregateResponse> {
  const params = model ? `?model=${encodeURIComponent(model)}` : "";
  return apiFetch<AggregateResponse>(`/aggregate${params}`);
}
