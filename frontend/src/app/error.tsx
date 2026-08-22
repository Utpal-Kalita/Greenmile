"use client";

import { AlertTriangle, RotateCcw } from "lucide-react";

export default function ErrorPage({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="error-state">
      <AlertTriangle size={28} />
      <span className="eyebrow danger">Route interrupted</span>
      <h1>Greenmile couldn’t build this view.</h1>
      <div>
        <strong>Why:</strong>
        <p>The interface encountered an unexpected state.</p>
      </div>
      <div>
        <strong>Try:</strong>
        <p>Restart this route surface. Your demo data stays safe.</p>
      </div>
      <button className="primary-button" onClick={reset}>
        <RotateCcw size={16} /> Restart view
      </button>
    </div>
  );
}
