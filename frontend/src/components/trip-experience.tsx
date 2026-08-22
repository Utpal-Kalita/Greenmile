"use client";

import { useEffect, useState } from "react";
import {
  AlertCircle,
  Check,
  FileUp,
  Play,
  RotateCcw,
  Sparkles,
} from "lucide-react";
import { EngineProgress } from "@/components/engine-progress";
import { RouteMap } from "@/components/route-map";
import { TripResults } from "@/components/trip-results";
import { api, ApiError, streamRunEvents } from "@/lib/api";
import type { OptimizationRun, Scenario, StageEvent, Stop } from "@/types/api";

type TripState =
  "empty" | "loading" | "loaded" | "optimizing" | "optimized" | "error";

export function TripExperience() {
  const [tripState, setTripState] = useState<TripState>("empty");
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [stops, setStops] = useState<Stop[]>([]);
  const [run, setRun] = useState<OptimizationRun | null>(null);
  const [events, setEvents] = useState<StageEvent[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!run || tripState !== "optimizing") return;
    let closed = false;
    const close = streamRunEvents(
      run.id,
      (event) => {
        setEvents((current) =>
          current.some((item) => item.id === event.id)
            ? current
            : [...current, event],
        );
        if (event.event_type === "ROUTE_READY") void refreshRun(run.id);
      },
      () => {
        if (!closed) void pollRun(run.id);
      },
    );
    async function pollRun(id: string) {
      for (let attempt = 0; attempt < 120 && !closed; attempt += 1) {
        const result = await api.getRun(id);
        setEvents(result.events);
        if (result.status === "COMPLETED") {
          setRun(result);
          setTripState("optimized");
          return;
        }
        if (result.status === "FAILED") {
          setError(result.error_message ?? "Optimization failed");
          setTripState("error");
          return;
        }
        await new Promise((resolve) => window.setTimeout(resolve, 500));
      }
    }
    async function refreshRun(id: string) {
      const result = await api.getRun(id);
      if (!closed) {
        setRun(result);
        setEvents(result.events);
        setTripState(
          result.status === "COMPLETED"
            ? "optimized"
            : result.status === "FAILED"
              ? "error"
              : "optimizing",
        );
      }
    }
    return () => {
      closed = true;
      close();
    };
  }, [run, tripState]);

  async function loadDemo() {
    setTripState("loading");
    setError("");
    try {
      const selected = await api.getDemoScenario();
      const routeStops = await api.getStops(selected.id);
      setScenario(selected);
      setStops(routeStops);
      setRun(null);
      setEvents([]);
      setTripState("loaded");
    } catch (reason) {
      setError(messageFor(reason));
      setTripState("error");
    }
  }
  async function optimize() {
    if (!scenario) return;
    setTripState("optimizing");
    setEvents([]);
    setError("");
    try {
      const created = await api.createRun(scenario.id);
      setRun(created);
      setEvents(created.events);
    } catch (reason) {
      setError(messageFor(reason));
      setTripState("error");
    }
  }
  async function submitEvent(eventType: string, stopId: string | null) {
    if (!run) return;
    try {
      const updated = await api.submitEvent(run.id, eventType, stopId);
      setRun(updated);
      setEvents(updated.events);
    } catch (reason) {
      setError(messageFor(reason));
    }
  }

  return (
    <div className="trip-page">
      <section className="trip-hero">
        <div className="hero-map-wrap">
          <RouteMap
            scenario={scenario}
            stops={stops}
            route={run?.route ?? []}
          />
          <div className="hero-map-shade" />
          <div className="hero-copy">
            <span className="eyebrow">
              Bidirectional last-mile optimization
            </span>
            <h1>
              <span>ONE TRIP.</span>
              <span>BOTH WAYS.</span>
            </h1>
            <p>Deliver going out. Collect returns coming back.</p>
          </div>
          {scenario && (
            <div className="dataset-badge">
              <span className="dataset-ready">
                <Check size={12} /> Database scenario
              </span>
              <strong>{scenario.name}</strong>
              <span className="mono">
                {scenario.stop_count} STOPS · {scenario.delivery_count} OUT ·{" "}
                {scenario.return_count} BACK
              </span>
            </div>
          )}
        </div>
        <aside className="trip-control-panel">
          {tripState === "empty" && <InitialPanel onLoad={loadDemo} />}
          {tripState === "loading" && (
            <StatusPanel
              title="Loading scenario"
              message="Reading stops and vehicle capacity from PostgreSQL."
            />
          )}
          {tripState === "loaded" && scenario && (
            <LoadedPanel
              scenario={scenario}
              onOptimize={optimize}
              onReset={() => {
                setTripState("empty");
                setScenario(null);
                setStops([]);
              }}
            />
          )}
          {tripState === "optimizing" && <EngineProgress events={events} />}
          {tripState === "optimized" && run && (
            <OptimizedPanel run={run} onRerun={optimize} />
          )}
          {tripState === "error" && (
            <ErrorPanel error={error} retry={scenario ? optimize : loadDemo} />
          )}
        </aside>
      </section>
      {tripState === "optimized" && run && (
        <TripResults run={run} stops={stops} onTripEvent={submitEvent} />
      )}
    </div>
  );
}

function InitialPanel({ onLoad }: { onLoad: () => void }) {
  return (
    <div className="initial-panel panel-content">
      <span className="panel-index mono">API / DISCONNECTED</span>
      <div>
        <span className="eyebrow">Ready for a scenario</span>
        <h2>Turn two trips into one loop.</h2>
        <p>
          The demo is loaded from PostgreSQL. Routes and impact are computed
          after you ask.
        </p>
      </div>
      <div className="initial-flow">
        <span>
          <i className="delivery-dot" />
          Deliveries
        </span>
        <span>
          <i className="return-dot" />
          Returns
        </span>
        <strong>
          <RotateCcw size={14} />
          One loop
        </strong>
      </div>
      <button className="primary-button" onClick={onLoad}>
        <Play size={16} fill="currentColor" /> Try Delhi demo
      </button>
      <small>Deterministic synthetic dataset · clearly labeled</small>
    </div>
  );
}
function LoadedPanel({
  scenario,
  onOptimize,
  onReset,
}: {
  scenario: Scenario;
  onOptimize: () => void;
  onReset: () => void;
}) {
  return (
    <div className="loaded-panel panel-content">
      <span className="panel-index mono">POSTGRESQL / READY</span>
      <div className="loaded-heading">
        <span className="eyebrow success">
          Scenario ready <Check size={12} />
        </span>
        <h2>{scenario.name}</h2>
        <p>{scenario.provenance.claims ?? scenario.description}</p>
      </div>
      <dl className="dataset-facts">
        <div>
          <dt>Stops</dt>
          <dd className="mono">{scenario.stop_count}</dd>
        </div>
        <div>
          <dt>Vehicles</dt>
          <dd className="mono">{scenario.vehicle_count}</dd>
        </div>
        <div>
          <dt>Depot</dt>
          <dd>{scenario.depot_address}</dd>
        </div>
        <div>
          <dt>Capacity</dt>
          <dd className="mono">{scenario.vehicle_capacity_kg} KG</dd>
        </div>
      </dl>
      <div className="action-stack">
        <button className="primary-button optimize-button" onClick={onOptimize}>
          <Sparkles size={17} /> Optimize this trip
        </button>
        <button className="text-button" onClick={onReset}>
          Choose another scenario
        </button>
      </div>
    </div>
  );
}
function OptimizedPanel({
  run,
  onRerun,
}: {
  run: OptimizationRun;
  onRerun: () => void;
}) {
  const metrics = run.metrics!;
  return (
    <div className="optimized-panel panel-content">
      <span className="panel-index mono">
        {run.run_id} / {run.latency_ms?.toFixed(0)} MS
      </span>
      <div className="result-heading">
        <span className="eyebrow success">
          Route persisted <Check size={12} />
        </span>
        <strong className="result-distance mono">
          {metrics.distance.after_km.toFixed(1)}
          <small>KM</small>
        </strong>
        <p>
          <b>↓ {metrics.distance.saved_percent.toFixed(1)}%</b> versus the
          computed baseline.
        </p>
      </div>
      <div className="result-mini-grid">
        <div>
          <span>Stops</span>
          <strong className="mono">{run.stop_count}</strong>
        </div>
        <div>
          <span>Vehicles</span>
          <strong className="mono">{run.vehicles.length}</strong>
        </div>
        <div>
          <span>Provider</span>
          <strong className="mono">{run.routing_provider}</strong>
        </div>
        <div>
          <span>Violations</span>
          <strong className="mono">{run.constraints.violations.length}</strong>
        </div>
      </div>
      <div className="result-callout">
        <Sparkles size={15} />
        <div>
          <span>Model status</span>
          <strong>
            {run.intelligence.status === "UNAVAILABLE"
              ? "No model connected — no fake output."
              : run.intelligence.message}
          </strong>
        </div>
      </div>
      <div className="action-stack">
        <button
          className="secondary-button"
          onClick={() =>
            document
              .querySelector(".impact-section")
              ?.scrollIntoView({ behavior: "smooth" })
          }
        >
          View real result
        </button>
        <button className="text-button" onClick={onRerun}>
          <RotateCcw size={13} /> Run again
        </button>
      </div>
    </div>
  );
}
function StatusPanel({ title, message }: { title: string; message: string }) {
  return (
    <div className="panel-content">
      <span className="panel-index mono">BACKEND / WORKING</span>
      <div style={{ marginTop: "auto", marginBottom: "auto" }}>
        <span className="eyebrow success">
          <span className="status-dot" /> Live request
        </span>
        <h2>{title}</h2>
        <p>{message}</p>
      </div>
    </div>
  );
}
function ErrorPanel({ error, retry }: { error: string; retry: () => void }) {
  return (
    <div className="panel-content">
      <span className="panel-index mono">BACKEND / ERROR</span>
      <div style={{ marginTop: "auto", marginBottom: "auto" }}>
        <span className="eyebrow danger">
          <AlertCircle size={13} /> Request failed
        </span>
        <h2>Greenmile couldn’t continue.</h2>
        <p>{error}</p>
        <button
          className="primary-button"
          style={{ marginTop: 25 }}
          onClick={retry}
        >
          <FileUp size={15} /> Try again
        </button>
      </div>
    </div>
  );
}
function messageFor(reason: unknown) {
  if (reason instanceof ApiError) {
    const detail = reason.detail as { detail?: string } | undefined;
    return detail?.detail ?? reason.message;
  }
  return reason instanceof Error
    ? reason.message
    : "The backend is unavailable.";
}
