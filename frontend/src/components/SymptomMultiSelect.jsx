import { Search, Sparkles, X } from "lucide-react";

function SymptomMultiSelect({
  catalog,
  filteredSymptoms,
  query,
  selectedSymptoms,
  setQuery,
  toggleSymptom,
}) {
  return (
    <div className="glass-panel selector-panel">
      <div className="selector-header">
        <div>
          <p className="eyebrow">Symptoms</p>
          <h2>Describe how you feel</h2>
        </div>
        <div className="badge">Choose at least 3 if possible</div>
      </div>

      <label className="search-box" htmlFor="symptom-search">
        <Search size={18} />
        <input
          id="symptom-search"
          type="text"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search symptoms like headache, nausea, fatigue..."
        />
      </label>

      <div className="selected-symptoms">
        {selectedSymptoms.length === 0 ? (
          <p className="muted">Selected symptoms will appear here.</p>
        ) : (
          selectedSymptoms.map((symptom) => (
            <button
              key={symptom}
              className="chip active"
              onClick={() => toggleSymptom(symptom)}
              type="button"
            >
              {catalog.find((item) => item.value === symptom)?.label ?? symptom}
              <X size={14} />
            </button>
          ))
        )}
      </div>

      <div className="symptom-grid">
        {filteredSymptoms.map((symptom) => {
          const isActive = selectedSymptoms.includes(symptom.value);
          return (
            <button
              key={symptom.value}
              type="button"
              className={`chip ${isActive ? "active" : ""}`}
              onClick={() => toggleSymptom(symptom.value)}
            >
              <Sparkles size={14} />
              {symptom.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default SymptomMultiSelect;
