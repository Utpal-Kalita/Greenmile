"use client";

import { useState } from "react";
import {
  AlertCircle,
  ArrowDown,
  Check,
  PackageCheck,
  RotateCcw,
  Sparkles,
  Warehouse,
} from "lucide-react";
import { RouteMap } from "@/components/route-map";
import { cn } from "@/lib/utils";
import type { OptimizationRun, RouteStop, Stop } from "@/types/api";

export function TripResults({
  run,
  stops,
  onTripEvent,
}: {
  run: OptimizationRun;
  stops: Stop[];
  onTripEvent: (event: string, stopId: string | null) => Promise<void>;
}) {
  if (!run.metrics) return null;
  return (
    <div className="results-story">
      <ImpactHero run={run} />
      <BeforeAfter run={run} stops={stops} />
      <RouteTimeline route={run.route} />
      <RouteIntelligence run={run} />
      <CapacityAndPacking run={run} />
      <DriverPreview run={run} onTripEvent={onTripEvent} />
      <section className="story-end">
        <Sparkles size={19} />
        <p>
          We optimized the route.
          <br />
          <strong>Then we measured every decision.</strong>
        </p>
        <a href="/performance">
          Open Performance Lab <ArrowDown className="rotate-icon" size={16} />
        </a>
      </section>
    </div>
  );
}

function ImpactHero({ run }: { run: OptimizationRun }) {
  const metrics = run.metrics!;
  const impact = [
    {
      value: `${metrics.distance.after_km.toFixed(1)} KM`,
      detail: `↓ ${metrics.distance.saved_percent.toFixed(1)}% distance`,
      primary: true,
    },
    {
      value: `₹${metrics.total_cost.saved.toFixed(0)}`,
      detail: "saved per run",
    },
    { value: `${metrics.co2_kg.saved.toFixed(1)} KG`, detail: "CO₂ avoided" },
    {
      value: `${metrics.driver_hours.saved.toFixed(1)} HRS`,
      detail: "driver time recovered",
    },
  ];
  return (
    <section className="impact-section reveal-section">
      <div className="section-heading-row">
        <div>
          <span className="eyebrow success">
            Trip computed <Check size={12} />
          </span>
          <h2>The loop is the impact.</h2>
        </div>
        <p>
          {run.routing_provider} distance · {run.algorithm_version}
        </p>
      </div>
      <div className="impact-grid">
        {impact.map((item) => (
          <article
            key={item.detail}
            className={cn("impact-metric", item.primary && "is-primary")}
          >
            <strong className="mono">{item.value}</strong>
            <span>{item.detail}</span>
          </article>
        ))}
      </div>
    </section>
  );
}

function BeforeAfter({ run, stops }: { run: OptimizationRun; stops: Stop[] }) {
  const [mode, setMode] = useState<"before" | "after">("after");
  const metrics = run.metrics!;
  return (
    <section className="comparison-section reveal-section">
      <div className="section-heading-row">
        <div>
          <span className="eyebrow">Route transformation</span>
          <h2>Before → After</h2>
        </div>
        <div className="segmented">
          <button
            className={mode === "before" ? "is-active" : ""}
            onClick={() => setMode("before")}
          >
            Before
          </button>
          <button
            className={mode === "after" ? "is-active" : ""}
            onClick={() => setMode("after")}
          >
            After
          </button>
        </div>
      </div>
      <div className="comparison-grid">
        <RouteMap
          scenario={run.scenario}
          stops={stops}
          route={mode === "after" ? run.route : []}
          before={mode === "before"}
          compact
        />
        <div className="comparison-data">
          <span
            className={`comparison-label ${mode === "before" ? "danger" : "success"}`}
          >
            {mode === "before" ? "Separate journeys" : "Bidirectional loops"}
          </span>
          <strong className="mono">
            {mode === "before" ? "2 TYPES" : `${run.vehicles.length} VANS`}
          </strong>
          <dl>
            <div>
              <dt>Distance</dt>
              <dd className="mono">
                {(mode === "before"
                  ? metrics.distance.before_km
                  : metrics.distance.after_km
                ).toFixed(1)}{" "}
                KM
              </dd>
            </div>
            <div>
              <dt>Stops</dt>
              <dd className="mono">{run.stop_count}</dd>
            </div>
            <div>
              <dt>Constraint violations</dt>
              <dd className="mono">{run.constraints.violations.length}</dd>
            </div>
          </dl>
          <p>
            {mode === "before"
              ? "Delivery and return routes are computed independently."
              : "Each route starts and closes at the persisted depot."}
          </p>
        </div>
      </div>
    </section>
  );
}

function RouteTimeline({ route }: { route: RouteStop[] }) {
  const firstVehicle = route
    .filter((item) => item.vehicle_sequence === 1)
    .slice(0, 12);
  return (
    <section className="timeline-section reveal-section">
      <div className="section-heading-row">
        <div>
          <span className="eyebrow">Vehicle 01</span>
          <h2>One loop, in order.</h2>
        </div>
        <p>Showing the first twelve persisted route stops.</p>
      </div>
      <div className="route-timeline">
        {firstVehicle.map((stop) => (
          <article
            key={stop.sequence_number}
            className={cn(
              "timeline-stop",
              stop.type === "DELIVERY"
                ? "is-delivery"
                : stop.type === "WAREHOUSE"
                  ? "is-warehouse"
                  : "is-return",
            )}
          >
            <span className="timeline-number mono">
              {String(stop.sequence_number).padStart(2, "0")}
            </span>
            <div className="timeline-marker">
              {stop.type === "WAREHOUSE" ? (
                <Warehouse size={16} />
              ) : stop.type === "DELIVERY" ? (
                <PackageCheck size={15} />
              ) : (
                <RotateCcw size={15} />
              )}
            </div>
            <div>
              <span className="mono stop-id">{stop.external_id}</span>
              <h3>{stop.name}</h3>
              <p>
                {new Date(stop.arrival_time).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}{" "}
                · {stop.distance_from_previous_km.toFixed(2)} km
              </p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function RouteIntelligence({ run }: { run: OptimizationRun }) {
  const checks = [
    {
      label: "Depot closure",
      ok: !run.constraints.violations.some((v) => v.type === "DEPOT"),
    },
    {
      label: "Capacity",
      ok: !run.constraints.violations.some((v) => v.type === "CAPACITY"),
    },
    {
      label: "Time windows",
      ok: !run.constraints.violations.some((v) => v.type === "TIME_WINDOW"),
    },
    {
      label: "Precedence",
      ok: !run.constraints.violations.some((v) => v.type === "PRECEDENCE"),
    },
  ];
  return (
    <section className="checks-section reveal-section">
      <div className="section-heading-row">
        <div>
          <span className="eyebrow">Verified by the engine</span>
          <h2>Route checks</h2>
        </div>
        <p>
          {run.constraints.feasible
            ? "All configured constraints passed."
            : `${run.constraints.violations.length} real violations reported — no result is hidden.`}
        </p>
      </div>
      <div className="route-checks">
        {checks.map((item, index) => (
          <div key={item.label}>
            <span style={{ color: item.ok ? "var(--green)" : "var(--red)" }}>
              {item.ok ? <Check size={14} /> : <AlertCircle size={14} />}
            </span>
            <strong>
              {item.label} {item.ok ? "feasible" : "needs attention"}
            </strong>
            <small className="mono">
              CHECK {String(index + 1).padStart(2, "0")}
            </small>
          </div>
        ))}
      </div>
    </section>
  );
}

function CapacityAndPacking({ run }: { run: OptimizationRun }) {
  const packing = run.packing;
  if (!packing) return null;
  return (
    <section className="packing-section reveal-section">
      <div className="section-heading-row">
        <div>
          <span className="eyebrow">Physical operation</span>
          <h2>Load the van</h2>
        </div>
        <p>Derived from vehicle 01’s persisted route and load transitions.</p>
      </div>
      <div className="packing-grid">
        <div className="capacity-panel">
          <div className="panel-kicker">Van utilization</div>
          <strong className="mono">
            {packing.utilization_percent.toFixed(0)}%
          </strong>
          <div className="capacity-track">
            <span
              style={{
                width: `${Math.min(packing.utilization_percent, 100)}%`,
              }}
            />
          </div>
          <div className="capacity-labels mono">
            <span>0 KG</span>
            <span>{packing.capacity_kg.toFixed(0)} KG</span>
          </div>
          <div className="reserved-space">
            <RotateCcw size={18} />
            <div>
              <strong>
                {packing.initial_load_l.toFixed(1)} L outbound load
              </strong>
              <span>
                {(packing.capacity_l - packing.initial_load_l).toFixed(1)} L
                available at departure
              </span>
            </div>
          </div>
        </div>
        <div className="van-wrap">
          <div className="van-label front mono">FRONT / CAB</div>
          <div className="van-body">
            <div className="van-cab">
              <span />
              <span />
            </div>
            <div className="cargo-grid">
              {packing.items.slice(0, 8).map((item) => (
                <div
                  className="cargo delivery-cargo"
                  key={`${item.stop_id}-${item.sequence}`}
                >
                  <small className="mono">
                    {String(item.sequence).padStart(2, "0")}
                  </small>
                  <strong className="mono">{item.stop_id}</strong>
                </div>
              ))}
              <div className="return-bay">
                <span>Return access zone</span>
                <div>
                  {packing.items
                    .filter((item) => item.zone === "RETURN_ACCESS")
                    .slice(0, 3)
                    .map((item) => (
                      <b className="mono" key={item.stop_id}>
                        {item.stop_id}
                      </b>
                    ))}
                </div>
              </div>
            </div>
          </div>
          <div className="van-label back mono">BACK / ACCESS</div>
        </div>
      </div>
    </section>
  );
}

function DriverPreview({
  run,
  onTripEvent,
}: {
  run: OptimizationRun;
  onTripEvent: (event: string, stopId: string | null) => Promise<void>;
}) {
  const [working, setWorking] = useState(false);
  const next = run.route.find(
    (item) => item.stop_id && item.status === "PENDING",
  );
  if (!next) return null;
  async function complete() {
    setWorking(true);
    await onTripEvent(
      next!.action === "DELIVER" ? "DELIVERY_COMPLETED" : "RETURN_COLLECTED",
      next!.stop_id,
    );
    setWorking(false);
  }
  return (
    <section className="driver-section reveal-section">
      <div className="driver-copy">
        <span className="eyebrow">Driver mode</span>
        <h2>
          Complex engine.
          <br />
          Simple next move.
        </h2>
        <p>This action is sent to the backend as a persisted trip event.</p>
      </div>
      <div className="phone-shell">
        <div className="phone-status mono">
          <span>LIVE</span>
          <span>{run.run_id}</span>
        </div>
        <div className="phone-progress">
          <span style={{ width: "12%" }} />
        </div>
        <span className="phone-kicker">Next stop</span>
        <strong className="phone-stop mono">{next.external_id}</strong>
        <h3>{next.name}</h3>
        <p className="phone-eta mono">
          {new Date(next.arrival_time).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}{" "}
          · {next.distance_from_previous_km.toFixed(1)} KM
        </p>
        <div className="phone-success">
          <Check size={17} />
          <div>
            <strong>{next.action}</strong>
            <span>{next.address}</span>
          </div>
        </div>
        <button
          disabled={working}
          className="primary-button phone-action"
          onClick={complete}
        >
          {working
            ? "Updating route…"
            : next.action === "DELIVER"
              ? "Mark delivered"
              : "Collect return"}
          <ArrowDown className="rotate-icon" size={17} />
        </button>
      </div>
    </section>
  );
}
