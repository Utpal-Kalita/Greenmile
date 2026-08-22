"use client";

import { useMemo, useState } from "react";
import {
  ArrowDown,
  Check,
  Gauge,
  ShieldCheck,
  Sparkles,
  Timer,
} from "lucide-react";
import { benchmarks } from "@/data/mock-data";
import { cn, formatPercent, formatSeconds } from "@/lib/utils";

type Mode = "turbo" | "balanced" | "quality";

const modes: Record<Mode, { speed: number; quality: number; note: string }> = {
  turbo: {
    speed: 83,
    quality: 2.1,
    note: "Fastest route generation for live dispatch.",
  },
  balanced: {
    speed: 77,
    quality: 0.2,
    note: "Recommended balance of speed and route quality.",
  },
  quality: {
    speed: 58,
    quality: -1.4,
    note: "Longer search for the shortest possible route.",
  },
};

export function PerformanceLab() {
  const [workload, setWorkload] = useState(500);
  const [mode, setMode] = useState<Mode>("balanced");
  const benchmark = useMemo(
    () =>
      benchmarks.find((item) => item.workload === workload) ?? benchmarks[1],
    [workload],
  );
  const improvement =
    (1 - benchmark.after.fullResult / benchmark.before.fullResult) * 100;
  const profile = modes[mode];

  return (
    <div className="content-page performance-page">
      <header className="page-hero performance-hero">
        <div>
          <span className="eyebrow">Greenmile performance / Round 2</span>
          <h1>
            We optimized
            <br />
            our own optimizer.
          </h1>
        </div>
        <div className="hero-proof">
          <span className="mono">BENCHMARK / DELHI-NCR</span>
          <strong className="mono">{formatPercent(improvement)}</strong>
          <p>faster full result at {workload.toLocaleString()} stops</p>
        </div>
      </header>

      <section className="workload-section">
        <div className="section-heading-row">
          <div>
            <span className="eyebrow">Workload</span>
            <h2>Choose the pressure.</h2>
          </div>
          <p>
            Measured mock benchmark based on the documented Round 2 scenario.
          </p>
        </div>
        <div className="workload-tabs">
          {benchmarks.map((item) => (
            <button
              key={item.workload}
              className={workload === item.workload ? "is-active" : ""}
              onClick={() => setWorkload(item.workload)}
            >
              <strong className="mono">{item.workload.toLocaleString()}</strong>
              <span>stops</span>
            </button>
          ))}
        </div>
      </section>

      <section className="benchmark-section">
        <div className="benchmark-head">
          <span>Measured stage</span>
          <span>Before</span>
          <span>After</span>
          <span>Change</span>
        </div>
        <BenchmarkRow
          label="Route ready"
          before={formatSeconds(benchmark.before.routeReady)}
          after={formatSeconds(benchmark.after.routeReady)}
          change={`${Math.round((1 - benchmark.after.routeReady / benchmark.before.routeReady) * 100)}% faster`}
        />
        <BenchmarkRow
          label="Full result"
          before={formatSeconds(benchmark.before.fullResult)}
          after={formatSeconds(benchmark.after.fullResult)}
          change={`${Math.round(improvement)}% faster`}
        />
        <BenchmarkRow
          label="AI blocking"
          before="YES"
          after="NO"
          change="Async"
        />
        <BenchmarkRow
          label="Route quality"
          before={`${benchmark.before.routeQuality.toFixed(1)} km`}
          after={`${benchmark.after.routeQuality.toFixed(1)} km`}
          change={`+${((benchmark.after.routeQuality / benchmark.before.routeQuality - 1) * 100).toFixed(1)}%`}
        />
      </section>

      <section className="timing-section">
        <div className="section-heading-row">
          <div>
            <span className="eyebrow">Where the time went</span>
            <h2>The same work. Less waiting.</h2>
          </div>
          <p>
            Candidate search is bounded. Distance is cached. AI runs after route
            readiness.
          </p>
        </div>
        <div className="timing-grid">
          <TimingChart
            title="Before"
            total={benchmark.before.fullResult}
            items={[
              { label: "2-opt", value: 58, color: "danger" },
              { label: "Distance", value: 18, color: "neutral" },
              { label: "Prediction", value: 9, color: "blue" },
              { label: "AI", value: 15, color: "amber" },
            ]}
          />
          <TimingChart
            title="After"
            total={benchmark.after.fullResult}
            items={[
              { label: "2-opt", value: 47, color: "green" },
              { label: "Distance", value: 12, color: "neutral" },
              { label: "Prediction", value: 8, color: "blue" },
              { label: "AI · ASYNC", value: 4, color: "amber" },
            ]}
          />
        </div>
      </section>

      <section className="tradeoff-section">
        <div className="section-heading-row">
          <div>
            <span className="eyebrow">Optimization profile</span>
            <h2>Speed without blind spots.</h2>
          </div>
          <p>
            Change the search profile to see the speed ↔ route-quality tradeoff.
          </p>
        </div>
        <div className="mode-selector">
          {(["turbo", "balanced", "quality"] as Mode[]).map((item) => (
            <button
              key={item}
              onClick={() => setMode(item)}
              className={mode === item ? "is-active" : ""}
            >
              <span className="mono">{item.toUpperCase()}</span>
              <small>{modes[item].note}</small>
            </button>
          ))}
        </div>
        <div className="quality-grid">
          <article>
            <Timer size={18} />
            <span>Speed</span>
            <strong className="mono">{profile.speed}% FASTER</strong>
          </article>
          <article>
            <Gauge size={18} />
            <span>Route quality</span>
            <strong className="mono">
              {profile.quality > 0 ? "+" : ""}
              {profile.quality}% DISTANCE
            </strong>
          </article>
          <article>
            <ShieldCheck size={18} />
            <span>Constraints</span>
            <strong className="mono">0 VIOLATIONS</strong>
          </article>
          <article>
            <Sparkles size={18} />
            <span>AI dependency</span>
            <strong className="mono">NON-BLOCKING</strong>
          </article>
        </div>
      </section>

      <footer className="performance-footer">
        <Check size={18} />
        <p>
          The route appears first. Intelligence arrives next.
          <br />
          <strong>Fast feedback, without losing operational context.</strong>
        </p>
        <a href="/system">
          See inside the system <ArrowDown className="rotate-icon" size={16} />
        </a>
      </footer>
    </div>
  );
}

function BenchmarkRow({
  label,
  before,
  after,
  change,
}: {
  label: string;
  before: string;
  after: string;
  change: string;
}) {
  return (
    <div className="benchmark-row">
      <strong>{label}</strong>
      <span className="mono before-value">{before}</span>
      <span className="mono after-value">{after}</span>
      <span className="change-value mono">{change}</span>
    </div>
  );
}

function TimingChart({
  title,
  total,
  items,
}: {
  title: string;
  total: number;
  items: Array<{ label: string; value: number; color: string }>;
}) {
  return (
    <article className={cn("timing-chart", title === "After" && "is-after")}>
      <header>
        <span className="eyebrow">{title}</span>
        <strong className="mono">{formatSeconds(total)}</strong>
      </header>
      <div className="timing-bars">
        {items.map((item) => (
          <div key={item.label} className="timing-bar-row">
            <span>{item.label}</span>
            <div>
              <i
                className={`bar-${item.color}`}
                style={{ width: `${item.value}%` }}
              />
            </div>
            <small className="mono">{item.value}%</small>
          </div>
        ))}
      </div>
    </article>
  );
}
