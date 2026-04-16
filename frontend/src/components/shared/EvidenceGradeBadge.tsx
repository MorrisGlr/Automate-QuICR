// Copyright (c) 2024-2026 Morris A. Aguilar. All Rights Reserved.
// Licensed under the Apache License, Version 2.0.
import type { EvidenceGrade } from "../../types/chart-review";

export function EvidenceGradeBadge({ grade }: { grade?: EvidenceGrade }) {
  if (!grade) return null;
  return (
    <span className="inline-block px-2 py-0.5 rounded text-xs font-bold ml-2 align-middle bg-teal text-white">
      GRADE: {grade.certainty}
    </span>
  );
}
