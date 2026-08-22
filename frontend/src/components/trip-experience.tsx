"use client";

import { useEffect, useRef, useState } from "react";
import {
  ArrowDown,
  Check,
  FileUp,
  Play,
  RotateCcw,
  Sparkles,
  Upload,
  X,
} from "lucide-react";
import { metrics, tripSummary } from "@/data/mock-data";
import { RouteMap } from "@/components/route-map";
import { EngineProgress } from "@/components/engine-progress";
import {
  BeforeAfter,
  CapacityAndPacking,
  DriverPreview,
  ImpactHero,
  Intelligence,
  RouteIntelligence,
  RouteTimeline,
} from "@/components/trip-results";
import { cn } from "@/lib/utils";

type TripState = "empty" | "loaded" | "optimizing" | "optimized";

export function TripExperience() {
  const [tripState, setTripState] = useState<TripState>("empty");
  const [activeStage, setActiveStage] = useState(0);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const resultsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (tripState !== "optimizing") return;
    if (activeStage >= 7) {
      const done = window.setTimeout(() => {
        setTripState("optimized");
        window.setTimeout(
          () =>
            resultsRef.current?.scrollIntoView({
              behavior: "smooth",
              block: "start",
            }),
          150,
        );
      }, 520);
      return () => window.clearTimeout(done);
    }
    const timer = window.setTimeout(
      () => setActiveStage((value) => value + 1),
      460,
    );
    return () => window.clearTimeout(timer);
  }, [tripState, activeStage]);

  function loadDemo() {
    setTripState("loaded");
    setActiveStage(0);
  }

  function optimize() {
    setTripState("optimizing");
    setActiveStage(0);
  }

  return (
    <div className="trip-page">
      <section
        className={cn(
          "trip-hero",
          tripState !== "empty" && "has-data",
          tripState === "optimizing" && "is-running",
          tripState === "optimized" && "is-complete",
        )}
      >
        <div className="hero-map-wrap">
          <RouteMap
            optimized={tripState === "optimized"}
            activeStop={tripState === "optimized" ? "D7" : undefined}
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
          {tripState === "empty" && (
            <div className="demo-loader">
              <div className="demo-stats mono">
                <span>
                  <strong>500</strong> Stops
                </span>
                <span>
                  <strong>250</strong> Deliveries
                </span>
                <span>
                  <strong>250</strong> Returns
                </span>
              </div>
              <button className="primary-button" onClick={loadDemo}>
                <Play size={16} fill="currentColor" /> Try Delhi demo
              </button>
              <button className="drop-button" onClick={loadDemo}>
                <Upload size={15} /> Drop route data here
              </button>
            </div>
          )}
          {tripState !== "empty" && (
            <div className="dataset-badge">
              <span className="dataset-ready">
                <Check size={12} /> Demo loaded
              </span>
              <strong>{tripSummary.zone}</strong>
              <span className="mono">
                {tripSummary.stops} STOPS · {tripSummary.deliveries} OUT ·{" "}
                {tripSummary.returns} BACK
              </span>
            </div>
          )}
        </div>

        <aside className="trip-control-panel">
          {tripState === "empty" && <InitialPanel onLoad={loadDemo} />}
          {tripState === "loaded" && (
            <LoadedPanel
              onOptimize={optimize}
              onReset={() => setTripState("empty")}
            />
          )}
          {tripState === "optimizing" && (
            <EngineProgress activeIndex={activeStage} />
          )}
          {tripState === "optimized" && (
            <OptimizedPanel
              onRerun={optimize}
              onTimeline={() => setDrawerOpen(true)}
            />
          )}
        </aside>
      </section>

      {tripState === "optimized" && (
        <div className="results-story" ref={resultsRef}>
          <ImpactHero />
          <BeforeAfter />
          <RouteTimeline />
          <section className="checks-section reveal-section">
            <div className="section-heading-row">
              <div>
                <span className="eyebrow">Verified by the engine</span>
                <h2>Route intelligence</h2>
              </div>
              <p>Technical constraints, translated into clear decisions.</p>
            </div>
            <RouteIntelligence />
          </section>
          <Intelligence />
          <CapacityAndPacking />
          <DriverPreview />
          <section className="story-end">
            <Sparkles size={19} />
            <p>
              We optimized the route.
              <br />
              <strong>Then we optimized the optimizer.</strong>
            </p>
            <a href="/performance">
              Open Performance Lab{" "}
              <ArrowDown className="rotate-icon" size={16} />
            </a>
          </section>
        </div>
      )}

      {drawerOpen && <EngineDrawer onClose={() => setDrawerOpen(false)} />}
    </div>
  );
}

function InitialPanel({ onLoad }: { onLoad: () => void }) {
  return (
    <div className="initial-panel panel-content">
      <span className="panel-index mono">TRIP / 001</span>
      <div>
        <span className="eyebrow">Ready for a route</span>
        <h2>Turn two trips into one loop.</h2>
        <p>
          Load a route to see deliveries, returns, capacity, risk, and impact as
          one operation.
        </p>
      </div>
      <div className="initial-flow">
        <span>
          <i className="delivery-dot" />
          Deliveries
        </span>
        <ArrowDown size={15} />
        <span>
          <i className="return-dot" />
          Returns
        </span>
        <ArrowDown size={15} />
        <strong>
          <RotateCcw size={14} />
          One loop
        </strong>
      </div>
      <button className="secondary-button" onClick={onLoad}>
        <FileUp size={16} /> Load demo route
      </button>
      <small>No setup. No upload needed.</small>
    </div>
  );
}

function LoadedPanel({
  onOptimize,
  onReset,
}: {
  onOptimize: () => void;
  onReset: () => void;
}) {
  return (
    <div className="loaded-panel panel-content">
      <span className="panel-index mono">DELHI DEMO / READY</span>
      <div className="loaded-heading">
        <span className="eyebrow success">
          Route data valid <Check size={12} />
        </span>
        <h2>{tripSummary.zone}</h2>
        <p>Realistic delivery and return demand across South Delhi.</p>
      </div>
      <dl className="dataset-facts">
        <div>
          <dt>Stops</dt>
          <dd className="mono">500</dd>
        </div>
        <div>
          <dt>Vehicle</dt>
          <dd className="mono">{tripSummary.vehicle}</dd>
        </div>
        <div>
          <dt>Depot</dt>
          <dd>{tripSummary.warehouse}</dd>
        </div>
        <div>
          <dt>Capacity</dt>
          <dd className="mono">{tripSummary.capacityKg} KG</dd>
        </div>
      </dl>
      <div className="action-stack">
        <button className="primary-button optimize-button" onClick={onOptimize}>
          <Sparkles size={17} /> Optimize this trip
        </button>
        <button className="text-button" onClick={onReset}>
          Use different data
        </button>
      </div>
    </div>
  );
}

function OptimizedPanel({
  onRerun,
  onTimeline,
}: {
  onRerun: () => void;
  onTimeline: () => void;
}) {
  return (
    <div className="optimized-panel panel-content">
      <span className="panel-index mono">RESULT / 01.138 SEC</span>
      <div className="result-heading">
        <span className="eyebrow success">
          Trip optimized <Check size={12} />
        </span>
        <strong className="result-distance mono">
          {metrics.afterDistance}
          <small>KM</small>
        </strong>
        <p>
          <b>↓ {metrics.distanceSavedPercent}%</b> distance from the original
          operation.
        </p>
      </div>
      <div className="result-mini-grid">
        <div>
          <span>One loop</span>
          <strong className="mono">500 STOPS</strong>
        </div>
        <div>
          <span>Saved</span>
          <strong className="mono">₹{metrics.moneySaved}</strong>
        </div>
        <div>
          <span>CO₂ avoided</span>
          <strong className="mono">{metrics.co2Saved} KG</strong>
        </div>
        <div>
          <span>Violations</span>
          <strong className="mono success-text">00</strong>
        </div>
      </div>
      <div className="result-callout">
        <Sparkles size={15} />
        <div>
          <span>Intelligence found</span>
          <strong>D7 needs verification.</strong>
        </div>
      </div>
      <div className="action-stack">
        <button className="secondary-button" onClick={onTimeline}>
          View engine timeline
        </button>
        <button className="text-button" onClick={onRerun}>
          <RotateCcw size={13} /> Run again
        </button>
      </div>
    </div>
  );
}

function EngineDrawer({ onClose }: { onClose: () => void }) {
  return (
    <div
      className="drawer-layer"
      role="dialog"
      aria-modal="true"
      aria-labelledby="drawer-title"
    >
      <button
        className="drawer-scrim"
        aria-label="Close engine timeline"
        onClick={onClose}
      />
      <aside className="engine-drawer">
        <div className="drawer-header">
          <div>
            <span className="eyebrow">Technical trace</span>
            <h2 id="drawer-title">Engine timeline</h2>
          </div>
          <button aria-label="Close" onClick={onClose}>
            <X size={18} />
          </button>
        </div>
        <div className="drawer-events">
          {[
            "INPUT · 500 stops",
            "CLUSTER · 6 zones",
            "ROUTE · Generated",
            "OPTIMIZE · 2-opt",
            "METRICS · Calculated",
            "RESULT · Ready",
            "AI · Analysis complete",
          ].map((event, index) => (
            <div key={event}>
              <span className="mono">
                14:32:01.{String(index * 29 + 2).padStart(3, "0")}
              </span>
              <strong className="mono">{event}</strong>
              <Check size={13} />
            </div>
          ))}
        </div>
        <p className="drawer-note">
          Route first. Intelligence second. AI never blocks the operational
          result.
        </p>
      </aside>
    </div>
  );
}
