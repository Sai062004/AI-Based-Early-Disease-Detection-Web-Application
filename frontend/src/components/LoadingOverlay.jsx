function LoadingOverlay({ message }) {
  return (
    <div className="loading-overlay" role="status" aria-live="polite">
      <div className="loading-card">
        <div className="pulse-ring" />
        <div className="pulse-ring delayed" />
        <div className="loading-core" />
        <p>{message}</p>
      </div>
    </div>
  );
}

export default LoadingOverlay;
