import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  HeartPulse,
  ShieldPlus,
} from "lucide-react";
import { Link } from "react-router-dom";

function ResultsPage({ prediction }) {
  const riskTone = prediction.riskLevel.toLowerCase();

  return (
    <main className="page-shell results-shell">
      <section className="results-grid">
        <article className={`glass-panel result-highlight risk-${riskTone}`}>
          <div className="result-heading">
            <div>
              <p className="eyebrow">Primary prediction</p>
              <h1>{prediction.predictedDisease}</h1>
            </div>
            <span className={`risk-badge risk-${riskTone}`}>{prediction.riskLevel} Risk</span>
          </div>

          <div className="confidence-wrap">
            <div className="confidence-meta">
              <span>Confidence</span>
              <strong>{prediction.confidence}%</strong>
            </div>
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${prediction.confidence}%` }} />
            </div>
          </div>

          <p className="disease-description">{prediction.description}</p>

          <div className="selected-list">
            {prediction.selectedSymptoms.map((item) => (
              <span className="mini-chip" key={item}>
                {item}
              </span>
            ))}
          </div>
        </article>

        <article className="glass-panel chart-card">
          <div className="panel-title">
            <HeartPulse size={20} />
            <h2>Top 3 probable diseases</h2>
          </div>
          <div className="simple-bars">
            {prediction.topPredictions.map((item) => (
              <div className="simple-bar-row" key={item.disease}>
                <div className="simple-bar-header">
                  <span>{item.disease}</span>
                  <strong>{item.confidence}%</strong>
                </div>
                <div className="progress-track slim">
                  <div className="progress-fill" style={{ width: `${item.confidence}%` }} />
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="glass-panel suggestions-card">
          <div className="panel-title">
            <ShieldPlus size={20} />
            <h2>Preventive suggestions</h2>
          </div>
          <div className="suggestion-list">
            {prediction.precautions.map((item) => (
              <div className="suggestion-item" key={item}>
                <CheckCircle2 size={18} />
                <p>{item}</p>
              </div>
            ))}
          </div>
        </article>

        <article className="glass-panel suggestions-card">
          <div className="panel-title">
            <AlertTriangle size={20} />
            <h2>Helpful follow-up symptoms</h2>
          </div>
          <div className="suggestion-list">
            {prediction.suggestedSymptoms.map((item) => (
              <div className="suggestion-item" key={item}>
                <ChevronRight size={18} />
                <p>{item}</p>
              </div>
            ))}
          </div>
          {prediction.unknownSymptoms.length > 0 ? (
            <p className="muted top-space">
              Unrecognized inputs: {prediction.unknownSymptoms.join(", ")}
            </p>
          ) : null}
        </article>
      </section>

      <section className="bottom-actions">
        <Link className="secondary-button" to="/check">
          Check another symptom set
        </Link>
      </section>
    </main>
  );
}

export default ResultsPage;
