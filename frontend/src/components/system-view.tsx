"use client";

import { useEffect, useState } from "react";
import {
  AlertCircle,
  Check,
  ChevronDown,
  CircleDot,
  Clock3,
  Database,
  GitBranch,
  MapPinned,
  PackageCheck,
  Route,
  Truck,
} from "lucide-react";
import { api } from "@/lib/api";
import type { OptimizationRun, Scenario } from "@/types/api";

const nodes = [
  { label: "PostgreSQL", detail: "Source of truth", icon: Database },
  { label: "Data engine", detail: "Validate · normalize", icon: GitBranch },
  { label: "Geo clustering", detail: "DBSCAN", icon: MapPinned },
  { label: "Route optimizer", detail: "NN · bounded 2-opt", icon: Route },
];
export function SystemView() {
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [run, setRun] = useState<OptimizationRun | null>(null);
  const [eventsOpen, setEventsOpen] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    void api
      .getDemoScenario()
      .then(async (demo) => {
        setScenario(demo);
        const records = await api.getBenchmarks();
        void records;
      })
      .catch((reason) =>
        setError(
          reason instanceof Error ? reason.message : "Backend unavailable",
        ),
      );
  }, []);
  async function loadLatest() {
    if (!scenario) return;
    try {
      const created = await api.createRun(scenario.id);
      let current = created;
      for (
        let i = 0;
        i < 80 && !["COMPLETED", "FAILED"].includes(current.status);
        i += 1
      ) {
        await new Promise((resolve) => window.setTimeout(resolve, 500));
        current = await api.getRun(created.id);
      }
      setRun(current);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Run failed");
    }
  }
  const visibleEvents =
    run?.events.filter(
      (event) => !event.event_type.startsWith("AI_ANALYSIS_"),
    ) ?? [];
  return (
    <div className="content-page system-page">
      <header className="page-hero system-hero">
        <div>
          <span className="eyebrow">Inside Greenmile</span>
          <h1>
            One visible system.
            <br />
            Every event is real.
          </h1>
        </div>
        <p>
          {scenario
            ? `${scenario.stop_count} persisted stops · ${scenario.vehicle_count} vehicles · ${scenario.provenance.kind}`
            : "Connecting to PostgreSQL-backed API…"}
        </p>
      </header>
      <section className="architecture-section">
        <div className="section-heading-row">
          <div>
            <span className="eyebrow">Live architecture</span>
            <h2>From input to movement.</h2>
          </div>
          <button
            className="secondary-button"
            onClick={loadLatest}
            disabled={!scenario}
          >
            Trace a real run
          </button>
        </div>
        <div className="architecture-flow">
          {nodes.map((node, index) => {
            const Icon = node.icon;
            return (
              <div className="architecture-step-wrap" key={node.label}>
                <div className="architecture-node is-selected">
                  <span className="node-index mono">0{index + 1}</span>
                  <Icon size={24} />
                  <strong>{node.label}</strong>
                  <small className="mono">{node.detail}</small>
                  <i>
                    <CircleDot size={12} />
                    {scenario ? "connected" : "waiting"}
                  </i>
                </div>
                {index < nodes.length - 1 && (
                  <span className="flow-connector">
                    <i />
                  </span>
                )}
              </div>
            );
          })}
        </div>
        <div className="system-branches">
          <article className="operations-branch">
            <header>
              <PackageCheck size={20} />
              <div>
                <span className="eyebrow">Operations</span>
                <h3>Deterministic decisions.</h3>
              </div>
            </header>
            <ul>
              <li>
                <Check size={13} />
                Capacity
              </li>
              <li>
                <Check size={13} />
                Time windows
              </li>
              <li>
                <Check size={13} />
                Packing
              </li>
              <li>
                <Check size={13} />
                Driver events
              </li>
            </ul>
            <div className="branch-result">
              <Truck size={18} />
              <span>Route ready first</span>
            </div>
          </article>
        </div>
      </section>
      <section className="event-section">
        <button
          className="event-toggle"
          onClick={() => setEventsOpen(!eventsOpen)}
        >
          <div>
            <Clock3 size={18} />
            <span>
              <small className="eyebrow">Persisted trace</small>
              <strong>Engine timeline</strong>
            </span>
          </div>
          <ChevronDown className={eventsOpen ? "is-open" : ""} size={18} />
        </button>
        {eventsOpen && (
          <div className="event-table">
            <div className="event-table-head mono">
              <span>Timestamp</span>
              <span>Event</span>
              <span>Output</span>
              <span>Status</span>
            </div>
            {visibleEvents.length ? (
              visibleEvents.map((event) => (
                <div className="event-row" key={event.id}>
                  <time className="mono">
                    {new Date(event.created_at).toLocaleTimeString()}
                  </time>
                  <strong className="mono">{event.event_type}</strong>
                  <span>
                    {Object.entries(event.payload)
                      .map(([k, v]) => `${k}: ${String(v)}`)
                      .join(" · ")}
                  </span>
                  <span className="event-status">
                    <Check size={12} />
                    persisted
                  </span>
                </div>
              ))
            ) : (
              <div className="event-row">
                <time className="mono">—</time>
                <strong className="mono">{error ? "ERROR" : "NO RUN"}</strong>
                <span>{error || "Trace a run to populate the timeline."}</span>
                <span className="event-status">—</span>
              </div>
            )}
          </div>
        )}
      </section>
      {error && (
        <section className="principle-strip">
          <AlertCircle />
          <p>{error}</p>
        </section>
      )}
    </div>
  );
}
