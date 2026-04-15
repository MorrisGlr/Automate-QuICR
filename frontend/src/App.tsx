import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ModelContext } from "./hooks/useModel";
import { getModels } from "./api/patients";
import { AppLayout } from "./components/layout/AppLayout";
import { Dashboard } from "./components/dashboard/Dashboard";
import { PatientView } from "./components/dashboard/PatientView";
import { AggregateView } from "./components/aggregate/AggregateView";

const DEFAULT_MODEL = "o4-mini-2025-04-16";

export default function App() {
  const [model, setModel] = useState(DEFAULT_MODEL);
  const [models, setModels] = useState<string[]>([]);

  useEffect(() => {
    getModels().then((m) => {
      setModels(m);
      if (m.length > 0 && !m.includes(model)) {
        setModel(m[0]);
      }
    });
  }, []);

  return (
    <ModelContext.Provider value={{ model, models, setModel }}>
      <BrowserRouter>
        <AppLayout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/patients/:id" element={<PatientView />} />
            <Route path="/aggregate" element={<AggregateView />} />
          </Routes>
        </AppLayout>
      </BrowserRouter>
    </ModelContext.Provider>
  );
}
