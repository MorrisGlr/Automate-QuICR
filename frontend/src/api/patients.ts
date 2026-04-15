import { apiFetch } from "./client";
import type { PatientSummary, PatientDetail } from "../types/patient";

export function getModels(): Promise<string[]> {
  return apiFetch<string[]>("/models");
}

export function getPatients(model?: string): Promise<PatientSummary[]> {
  const params = model ? `?model=${encodeURIComponent(model)}` : "";
  return apiFetch<PatientSummary[]>(`/patients${params}`);
}

export function getPatient(id: string, model?: string): Promise<PatientDetail> {
  const params = model ? `?model=${encodeURIComponent(model)}` : "";
  return apiFetch<PatientDetail>(`/patients/${encodeURIComponent(id)}${params}`);
}
