export default function Loading() {
  return (
    <div className="route-loading" role="status" aria-live="polite">
      <span className="eyebrow">Greenmile engine</span>
      <h1>Preparing the route surface.</h1>
      <div className="loading-track">
        <span />
      </div>
      <div className="loading-steps mono">
        <span>MAP</span>
        <span>ROUTE</span>
        <span>OPERATIONS</span>
      </div>
    </div>
  );
}
