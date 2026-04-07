import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import SymptomPage from "./pages/SymptomPage";
import ResultsPage from "./pages/ResultsPage";

function App() {
  const [symptoms, setSymptoms] = useState([]);
  const [catalog, setCatalog] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [isLoadingCatalog, setIsLoadingCatalog] = useState(true);
  const [catalogError, setCatalogError] = useState("");

  useEffect(() => {
    let isMounted = true;

    async function loadSymptoms() {
      setIsLoadingCatalog(true);
      try {
        const response = await fetch("/api/symptoms");
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "Unable to load symptom catalog.");
        }
        if (isMounted) {
          setCatalog(payload.symptoms);
          setMetrics(payload.metrics);
          setCatalogError("");
        }
      } catch (error) {
        if (isMounted) {
          setCatalogError(error.message);
        }
      } finally {
        if (isMounted) {
          setIsLoadingCatalog(false);
        }
      }
    }

    loadSymptoms();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <Routes>
      <Route path="/" element={<LandingPage metrics={metrics} />} />
      <Route
        path="/check"
        element={
          <SymptomPage
            catalog={catalog}
            catalogError={catalogError}
            isLoadingCatalog={isLoadingCatalog}
            prediction={prediction}
            selectedSymptoms={symptoms}
            setPrediction={setPrediction}
            setSelectedSymptoms={setSymptoms}
          />
        }
      />
      <Route
        path="/results"
        element={
          prediction ? (
            <ResultsPage prediction={prediction} selectedSymptoms={symptoms} />
          ) : (
            <Navigate to="/check" replace />
          )
        }
      />
    </Routes>
  );
}

export default App;
