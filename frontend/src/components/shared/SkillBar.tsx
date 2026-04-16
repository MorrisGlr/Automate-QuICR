// Copyright (c) 2024-2026 Morris A. Aguilar. All Rights Reserved.
// Licensed under the Apache License, Version 2.0.
const SKILL_MAP: Record<string, { percent: number; color: string; textColor: string }> = {
  "Critical Gap": { percent: 25, color: "bg-skill-critical-gap", textColor: "text-white" },
  "Needs Improvement": { percent: 50, color: "bg-skill-needs-improvement", textColor: "text-gray-800" },
  "Meets Expectations": { percent: 75, color: "bg-skill-meets-expectations", textColor: "text-gray-800" },
  Excellent: { percent: 100, color: "bg-skill-excellent", textColor: "text-white" },
};

export function SkillBar({ assessment }: { assessment: string }) {
  const info = SKILL_MAP[assessment] ?? { percent: 0, color: "bg-gray-400", textColor: "text-white" };
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="font-medium">{assessment}</span>
      </div>
      <div className="w-full bg-gray-200 rounded h-4 overflow-hidden">
        <div
          className={`h-full rounded ${info.color} transition-all duration-300`}
          style={{ width: `${info.percent}%` }}
        />
      </div>
    </div>
  );
}
