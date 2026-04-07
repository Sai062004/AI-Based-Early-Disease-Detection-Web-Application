import { Mic, RefreshCcw, Stethoscope } from "lucide-react";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import LoadingOverlay from "../components/LoadingOverlay";
import SymptomMultiSelect from "../components/SymptomMultiSelect";

function SymptomPage({
  catalog,
  catalogError,
  isLoadingCatalog,
  setPrediction,
  selectedSymptoms,
  setSelectedSymptoms,
}) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [isPredicting, setIsPredicting] = useState(false);

  const filteredSymptoms = useMemo(() => {
    const base = query
      ? catalog.filter((item) => item.label.toLowerCase().includes(query.toLowerCase()))
      : catalog;
    return base.slice(0, 36);
  }, [catalog, query]);

  function toggleSymptom(symptom) {
    setSelectedSymptoms((current) =>
      current.includes(symptom) ? current.filter((item) => item !== symptom) : [...current, symptom]
    );
  }

  function clearSelection() {
    setSelectedSymptoms([]);
    setError("");
    setQuery("");
  }

  function useVoiceInput() {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      setError("Voice input is not supported in this browser.");
      return;
    }

    const recognition = new Recognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onresult = (event) => {
      setQuery(event.results[0][0].transcript);
    };
    recognition.start();
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (selectedSymptoms.length === 0) {
      setError("Select at least one symptom before running a prediction.");
      return;
    }

    setIsPredicting(true);
    setError("");

    try {
      const response = await fetch("/api/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ symptoms: selectedSymptoms }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Prediction failed.");
      }
      setPrediction(payload);
      navigate("/results");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsPredicting(false);
    }
  }

  return (
    <main className="page-shell page-checker">
      {isPredicting ? <LoadingOverlay message="Analyzing symptoms and generating ranked predictions..." /> : null}
      <section className="checker-header glass-panel">
        <div>
          <p className="eyebrow">Guided assessment</p>
          <h1>Symptom Intelligence Console</h1>
          <p className="muted">
            Select symptoms, run the model, and review the top disease matches with confidence scores and precautions.
          </p>
        </div>
        <div className="checker-actions">
          <button className="secondary-button" type="button" onClick={useVoiceInput}>
            <Mic size={18} />
            Voice Input
          </button>
          <button className="ghost-button" type="button" onClick={clearSelection}>
            <RefreshCcw size={18} />
            Reset
          </button>
        </div>
      </section>

      <section className="checker-layout">
        <form className="checker-main" onSubmit={handleSubmit}>
          <SymptomMultiSelect
            catalog={catalog}
            filteredSymptoms={filteredSymptoms}
            query={query}
            selectedSymptoms={selectedSymptoms}
            setQuery={setQuery}
            toggleSymptom={toggleSymptom}
          />

          <div className="glass-panel submit-panel">
            <button className="primary-button full-width" disabled={isLoadingCatalog || isPredicting} type="submit">
              <Stethoscope size={18} />
              Predict Likely Disease
            </button>
            {error ? <p className="error-text">{error}</p> : null}
            {catalogError ? <p className="error-text">{catalogError}</p> : null}
          </div>
        </form>

        <aside className="checker-sidebar">
          <div className="glass-panel helper-card">
            <h3>How this works</h3>
            <p>
              The model converts your symptom set into a binary feature vector and scores the most likely diseases from
              the training dataset.
            </p>
          </div>
          <div className="glass-panel helper-card">
            <h3>What makes a stronger prediction</h3>
            <p>More specific symptom combinations usually produce a sharper confidence profile and better top-3 ranking.</p>
          </div>
        </aside>
      </section>
    </main>
  );
}

export default SymptomPage;
