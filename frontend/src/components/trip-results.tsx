"use client";

import { useState } from "react";
import {
  AlertTriangle,
  ArrowDown,
  Check,
  ChevronRight,
  PackageCheck,
  RotateCcw,
  Sparkles,
  Warehouse,
} from "lucide-react";
import { metrics, stops, tripSummary } from "@/data/mock-data";
import { cn } from "@/lib/utils";
import { RouteMap } from "@/components/route-map";

export function ImpactHero() {
  const impact = [
    {
      value: `${metrics.afterDistance} KM`,
      detail: `↓ ${metrics.distanceSavedPercent}% distance`,
      primary: true,
    },
    { value: `₹${metrics.moneySaved}`, detail: "saved per trip" },
    { value: `${metrics.co2Saved} KG`, detail: "CO₂ avoided" },
    { value: `${metrics.hoursSaved} HRS`, detail: "driver time recovered" },
  ];
  return (
    <section
      className="impact-section reveal-section"
      aria-labelledby="impact-heading"
    >
      <div className="section-heading-row">
        <div>
          <span className="eyebrow success">
            Trip optimized <Check size={12} />
          </span>
          <h2 id="impact-heading">The loop is the impact.</h2>
        </div>
        <p>Two disconnected journeys became one continuous operation.</p>
      </div>
      <div className="impact-grid">
        {impact.map((item, index) => (
          <article
            key={item.value}
            className={cn("impact-metric", item.primary && "is-primary")}
            style={{ animationDelay: `${index * 90}ms` }}
          >
            <strong className="mono">{item.value}</strong>
            <span>{item.detail}</span>
          </article>
        ))}
      </div>
    </section>
  );
}

export function BeforeAfter() {
  const [mode, setMode] = useState<"before" | "after">("after");
  return (
    <section
      className="comparison-section reveal-section"
      aria-labelledby="comparison-heading"
    >
      <div className="section-heading-row">
        <div>
          <span className="eyebrow">Route transformation</span>
          <h2 id="comparison-heading">Before → After</h2>
        </div>
        <div className="segmented" role="group" aria-label="Select route view">
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
          before={mode === "before"}
          optimized={mode === "after"}
          compact
        />
        <div className="comparison-data">
          {mode === "before" ? (
            <>
              <span className="comparison-label danger">Separate journeys</span>
              <strong className="mono">2 TRIPS</strong>
              <dl>
                <div>
                  <dt>Delivery trip</dt>
                  <dd className="mono">87 KM</dd>
                </div>
                <div>
                  <dt>Return trip</dt>
                  <dd className="mono">43 KM</dd>
                </div>
                <div>
                  <dt>Empty legs</dt>
                  <dd className="mono">35 KM</dd>
                </div>
              </dl>
            </>
          ) : (
            <>
              <span className="comparison-label success">
                Bidirectional loop
              </span>
              <strong className="mono">1 TRIP</strong>
              <dl>
                <div>
                  <dt>Continuous loop</dt>
                  <dd className="mono">52.1 KM</dd>
                </div>
                <div>
                  <dt>Stops served</dt>
                  <dd className="mono">500</dd>
                </div>
                <div>
                  <dt>Empty legs</dt>
                  <dd className="mono success-text">0 KM</dd>
                </div>
              </dl>
            </>
          )}
          <p>
            {mode === "before"
              ? "The van repeats roads and comes home empty."
              : "Deliver going out. Collect returns coming back."}
          </p>
        </div>
      </div>
    </section>
  );
}

export function RouteTimeline() {
  const routeStops = stops.slice(0, 8);
  return (
    <section
      className="timeline-section reveal-section"
      aria-labelledby="timeline-heading"
    >
      <div className="section-heading-row">
        <div>
          <span className="eyebrow">The operation</span>
          <h2 id="timeline-heading">One loop, in order.</h2>
        </div>
        <p>Deliver first. Collect returns. Come home.</p>
      </div>
      <div className="route-timeline">
        {routeStops.map((stop, index) => (
          <article
            key={stop.id}
            className={cn("timeline-stop", `is-${stop.kind}`)}
          >
            <span className="timeline-number mono">
              {String(index).padStart(2, "0")}
            </span>
            <div className="timeline-marker">
              {stop.kind === "warehouse" ? (
                <Warehouse size={16} />
              ) : stop.kind === "delivery" ? (
                <PackageCheck size={15} />
              ) : (
                <RotateCcw size={15} />
              )}
            </div>
            <div>
              <span className="mono stop-id">{stop.id}</span>
              <h3>{stop.name}</h3>
              <p>
                {stop.eta} · {stop.window}
              </p>
            </div>
            {stop.risk === "high" && (
              <span className="risk-chip">
                <AlertTriangle size={12} />
                84% risk
              </span>
            )}
            {index < routeStops.length - 1 && (
              <ChevronRight className="timeline-arrow" size={17} />
            )}
          </article>
        ))}
        <article className="timeline-stop is-warehouse is-last">
          <span className="timeline-number mono">08</span>
          <div className="timeline-marker">
            <Warehouse size={16} />
          </div>
          <div>
            <span className="mono stop-id">DEPOT</span>
            <h3>Home</h3>
            <p>14:36 · Loop closed</p>
          </div>
        </article>
      </div>
    </section>
  );
}

export function Intelligence() {
  return (
    <section
      className="intelligence-section reveal-section"
      aria-labelledby="intelligence-heading"
    >
      <div className="intelligence-intro">
        <span className="eyebrow intelligence">
          <Sparkles size={12} /> Greenmile Intelligence
        </span>
        <h2 id="intelligence-heading">
          We look for things the route alone can’t see.
        </h2>
        <p>
          D7 is the main operational risk. Its return probability is 84%. Keep
          capacity available and verify the delivery before dispatch.
        </p>
      </div>
      <div className="risk-console">
        <div className="risk-header">
          <span>Return risk</span>
          <span className="mono">MODEL / R-07</span>
        </div>
        <div className="risk-score">
          <span className="mono">D7</span>
          <strong className="mono">84%</strong>
        </div>
        <p>
          <AlertTriangle size={15} /> High chance of return
        </p>
        <dl>
          <div>
            <dt>Previous returns</dt>
            <dd className="mono">03</dd>
          </div>
          <div>
            <dt>Disputes</dt>
            <dd className="mono">02</dd>
          </div>
          <div>
            <dt>Avg. confirmation</dt>
            <dd className="mono">18 MIN</dd>
          </div>
        </dl>
        <div className="recommendation">
          <span>Recommendation</span>
          <strong>VERIFY</strong>
          <p>Confirm D7 before the van leaves Okhla.</p>
        </div>
      </div>
    </section>
  );
}

export function CapacityAndPacking() {
  return (
    <section
      className="packing-section reveal-section"
      aria-labelledby="packing-heading"
    >
      <div className="section-heading-row">
        <div>
          <span className="eyebrow">Physical operation</span>
          <h2 id="packing-heading">Load the van</h2>
        </div>
        <p>Deliveries go in first. Returns stay accessible.</p>
      </div>
      <div className="packing-grid">
        <div className="capacity-panel">
          <div className="panel-kicker">Van capacity</div>
          <strong className="mono">{tripSummary.usedCapacity}%</strong>
          <div className="capacity-track">
            <span style={{ width: `${tripSummary.usedCapacity}%` }} />
          </div>
          <div className="capacity-labels mono">
            <span>0 KG</span>
            <span>{tripSummary.capacityKg} KG</span>
          </div>
          <div className="reserved-space">
            <RotateCcw size={18} />
            <div>
              <strong>{tripSummary.returnSpaceLitres} L return space</strong>
              <span>Reserved for predicted returns</span>
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
              {["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"].map(
                (id, index) => (
                  <div
                    className="cargo delivery-cargo"
                    key={id}
                    style={{ animationDelay: `${index * 60}ms` }}
                  >
                    <small className="mono">
                      {String(index + 1).padStart(2, "0")}
                    </small>
                    <strong className="mono">{id}</strong>
                  </div>
                ),
              )}
              <div className="return-bay">
                <span>Reserved return space</span>
                <div>
                  <b className="mono">R4</b>
                  <b className="mono">R3</b>
                  <b className="mono">R2</b>
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

export function RouteIntelligence() {
  const checks = [
    "Route feasible",
    "Capacity feasible",
    "Time windows satisfied",
    "Depot return confirmed",
  ];
  return (
    <div className="route-checks">
      {checks.map((check, index) => (
        <div key={check}>
          <span>
            <Check size={14} />
          </span>
          <strong>{check}</strong>
          <small className="mono">
            CHECK {String(index + 1).padStart(2, "0")}
          </small>
        </div>
      ))}
    </div>
  );
}

export function DriverPreview() {
  const [delivered, setDelivered] = useState(false);
  return (
    <section
      className="driver-section reveal-section"
      aria-labelledby="driver-heading"
    >
      <div className="driver-copy">
        <span className="eyebrow">Driver mode</span>
        <h2 id="driver-heading">
          Complex engine.
          <br />
          Simple next move.
        </h2>
        <p>
          The driver sees only the next stop, the action, and the risk that
          matters.
        </p>
        <ul>
          <li>
            <Check size={14} />
            No dashboard overload
          </li>
          <li>
            <Check size={14} />
            One clear action
          </li>
          <li>
            <Check size={14} />
            Risk shown at the right moment
          </li>
        </ul>
      </div>
      <div className="phone-shell">
        <div className="phone-status mono">
          <span>12:36</span>
          <span>GM ROUTE · 62%</span>
        </div>
        <div className="phone-progress">
          <span style={{ width: delivered ? "72%" : "62%" }} />
        </div>
        <span className="phone-kicker">
          {delivered ? "Next pickup" : "Next stop"}
        </span>
        <strong className="phone-stop mono">{delivered ? "R3" : "D7"}</strong>
        <h3>{delivered ? "Lajpat Nagar" : "Vasant Kunj"}</h3>
        <p className="phone-eta mono">
          {delivered ? "12:46 PM" : "12:42 PM"} ·{" "}
          {delivered ? "8 MIN" : "6 MIN"}
        </p>
        {!delivered && (
          <div className="phone-risk">
            <AlertTriangle size={16} />
            <div>
              <strong>84% return risk</strong>
              <span>Verify before handoff</span>
            </div>
          </div>
        )}
        {delivered && (
          <div className="phone-success">
            <Check size={17} />
            <div>
              <strong>Delivered</strong>
              <span>D7 confirmed at 12:39</span>
            </div>
          </div>
        )}
        <button
          className="primary-button phone-action"
          onClick={() => setDelivered(!delivered)}
        >
          {delivered ? "Collect return" : "Navigate"}
          <ArrowDown className="rotate-icon" size={17} />
        </button>
      </div>
    </section>
  );
}
