// Copyright (c) 2024-2026 Morris A. Aguilar. All Rights Reserved.
// Licensed under the Apache License, Version 2.0.
import { createContext, useContext } from "react";

export interface ModelContextValue {
  model: string;
  models: string[];
  setModel: (model: string) => void;
}

export const ModelContext = createContext<ModelContextValue>({
  model: "",
  models: [],
  setModel: () => {},
});

export function useModel() {
  return useContext(ModelContext);
}
