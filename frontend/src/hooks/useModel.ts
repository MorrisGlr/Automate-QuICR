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
