// Copyright (c) 2024-2026 Morris A. Aguilar. All Rights Reserved.
// Licensed under the Apache License, Version 2.0.
import type { DrugPricing } from "../../types/chart-review";

export function DrugPricingTable({ pricing }: { pricing?: DrugPricing[] }) {
  if (!pricing || pricing.length === 0) return null;
  return (
    <div className="mt-4">
      <h4 className="text-sm font-bold text-teal mb-2">Generic Drug Pricing</h4>
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b-2 border-teal text-left">
            <th className="py-1 pr-3">Mention</th>
            <th className="py-1 pr-3">Generic Name</th>
            <th className="py-1 pr-3">Source</th>
            <th className="py-1">30-Day Cost</th>
          </tr>
        </thead>
        <tbody>
          {pricing.map((d, i) => (
            <tr key={i} className="border-b border-gray-100">
              <td className="py-1 pr-3">{d.Mention}</td>
              <td className="py-1 pr-3">{d["Generic Name"]}</td>
              <td className="py-1 pr-3">{d.Source}</td>
              <td className="py-1">{d["30 Day Cost"]}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
