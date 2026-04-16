// Copyright (c) 2024-2026 Morris A. Aguilar. All Rights Reserved.
// Licensed under the Apache License, Version 2.0.
import { Link, useLocation } from "react-router-dom";
import { useModel } from "../../hooks/useModel";

export function Header() {
  const { model, models, setModel } = useModel();
  const location = useLocation();

  const navLinks = [
    { to: "/", label: "Dashboard" },
    { to: "/aggregate", label: "Aggregate" },
  ];

  return (
    <header className="bg-teal text-white shadow-md">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link to="/" className="text-2xl font-bold tracking-tight no-underline text-white">
          QuICR
        </Link>

        <nav className="flex items-center gap-6">
          {navLinks.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className={`text-sm font-medium no-underline transition-colors ${
                location.pathname === link.to
                  ? "text-white border-b-2 border-white pb-0.5"
                  : "text-white/70 hover:text-white"
              }`}
            >
              {link.label}
            </Link>
          ))}

          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="text-sm bg-white/20 text-white border border-white/30 rounded px-2 py-1 outline-none"
          >
            {models.map((m) => (
              <option key={m} value={m} className="text-gray-800">
                {m}
              </option>
            ))}
          </select>
        </nav>
      </div>
    </header>
  );
}
