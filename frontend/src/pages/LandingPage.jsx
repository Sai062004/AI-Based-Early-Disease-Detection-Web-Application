import { Activity, BrainCircuit, HeartPulse, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";

const highlights = [
  {
    icon: BrainCircuit,
    title: "AI-assisted screening",
    text: "Random Forest inference analyzes your symptom pattern and returns ranked disease predictions instantly.",
  },
  {
    icon: ShieldCheck,
    title: "Actionable precautions",
    text: "Each prediction comes with practical next-step guidance so the experience feels useful, not just technical.",
  },
  {
    icon: HeartPulse,
    title: "Early detection mindset",
    text: "LifeLens AI is designed to help users spot risk patterns early and seek care sooner.",
  },
];

function LandingPage({ metrics }) {
  return (
    <main className="page-shell">
      <section className="hero-card">
        <div className="hero-copy">
          <p className="eyebrow">Healthcare intelligence</p>
          <h1>LifeLens AI</h1>
          <p className="hero-tagline">Early detection saves lives.</p>
          <p className="hero-text">
            A polished symptom-checking experience powered by machine learning, designed to turn raw symptom
            combinations into fast, readable health insights.
          </p>
          <div className="hero-actions">
            <Link className="primary-button" to="/check">
              Check Your Health
            </Link>
            <a className="secondary-button" href="#how-it-works">
              See How It Works
            </a>
          </div>
        </div>

        <div className="hero-visual">
          <div className="floating-card large">
            <Activity size={28} />
            <div>
              <p>Model accuracy</p>
              <strong>{metrics ? `${Math.round((metrics.maskedAccuracy ?? metrics.accuracy) * 100)}%` : "Training..."}</strong>
            </div>
          </div>
          <div className="floating-card small tilt-left">
            <span>41 diseases covered</span>
          </div>
          <div className="floating-card small tilt-right">
            <span>{metrics ? `${metrics.symptomCount} symptoms indexed` : "132 symptoms indexed"}</span>
          </div>
        </div>
      </section>

      <section className="stats-row">
        <div className="stat-card">
          <span>Top-1 Accuracy</span>
          <strong>{metrics ? `${((metrics.maskedAccuracy ?? metrics.accuracy) * 100).toFixed(1)}%` : "--"}</strong>
        </div>
        <div className="stat-card">
          <span>Top-3 Accuracy</span>
          <strong>{metrics ? `${((metrics.maskedTop3Accuracy ?? metrics.top3Accuracy) * 100).toFixed(1)}%` : "--"}</strong>
        </div>
        <div className="stat-card">
          <span>Symptoms Indexed</span>
          <strong>{metrics ? metrics.symptomCount : "--"}</strong>
        </div>
      </section>

      <section className="feature-section" id="how-it-works">
        {highlights.map((item) => {
          const Icon = item.icon;
          return (
            <article className="feature-card" key={item.title}>
              <div className="feature-icon">
                <Icon size={24} />
              </div>
              <h3>{item.title}</h3>
              <p>{item.text}</p>
            </article>
          );
        })}
      </section>
    </main>
  );
}

export default LandingPage;
