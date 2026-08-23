"use client";

import { useMemo, useState } from "react";
import { Check, Gauge, ShieldCheck, Timer } from "lucide-react";
import round2Report from "@/data/round2-benchmark-results.json";

const workloads = round2Report.workloads;

export function PerformanceLab() {
  const [workload, setWorkload] = useState(500);
  const benchmark = useMemo(
    () => workloads.find((item) => item.stop_count === workload) ?? workloads[0],
    [workload],
  );
  const generatedAt = new Date(round2Report.generated_at).toLocaleDateString(
    "en-IN",
    { day: "2-digit", month: "short", year: "numeric" },
  );

  return (
    <div className="content-page performance-page">
      <header className="page-hero performance-hero">
        <div>
          <span className="eyebrow">Greenmile performance / Round 2</span>
          <h1>
            We measure
            <br />
            our own optimizer.
          </h1>
        </div>
        <div className="hero-proof">
          <span className="mono">ROUND 2 ARTIFACT</span>
          <strong className="mono">{formatSpeedupValue(benchmark.speedup)}</strong>
          <p>{`faster at ${benchmark.stop_count.toLocaleString()} stops`}</p>
        </div>
      </header>
      <section className="workload-section">
        <div className="section-heading-row">
          <div>
            <span className="eyebrow">Workload</span>
            <h2>Choose the measured artifact.</h2>
          </div>
          <p>
            Values are read from <code>{round2Report.source_file}</code>, generated {generatedAt}.
          </p>
        </div>
        <div className="workload-tabs">
          {workloads.map((item) => (
            <button
              key={item.stop_count}
              className={workload === item.stop_count ? "is-active" : ""}
              onClick={() => setWorkload(item.stop_count)}
            >
              <strong className="mono">{item.stop_count.toLocaleString()}</strong>
              <span>stops</span>
            </button>
          ))}
        </div>
      </section>
      <section className="benchmark-section">
        <div className="benchmark-head">
          <span>Measured value</span>
          <span>Baseline</span>
          <span>Optimized</span>
          <span>Change</span>
        </div>
        <BenchmarkRow
          label="P50 execution latency"
          before={formatMs(benchmark.baseline_latency_ms)}
          after={formatMs(benchmark.optimized_latency_ms)}
          change={formatSpeedup(benchmark.speedup)}
        />
        <BenchmarkRow
          label="P95 execution latency"
          before={formatMs(benchmark.baseline_p95_latency_ms)}
          after={formatMs(benchmark.optimized_p95_latency_ms)}
          change={formatSpeedup(benchmark.speedup_p95)}
        />
        <BenchmarkRow
          label="P99 execution latency"
          before={formatMs(benchmark.baseline_p99_latency_ms)}
          after={formatMs(benchmark.optimized_p99_latency_ms)}
          change={formatSpeedup(benchmark.speedup_p99)}
        />
        <BenchmarkRow
          label="Route distance"
          before={formatKm(benchmark.baseline_distance_km)}
          after={formatKm(benchmark.optimized_distance_km)}
          change={`${benchmark.quality_delta_percent.toFixed(1)}% quality delta`}
        />
      </section>
      <section className="tradeoff-section">
        <div className="section-heading-row">
          <div>
            <span className="eyebrow">Correctness guardrail</span>
            <h2>Speed, with proof.</h2>
          </div>
          <p>
            Baseline and optimized numbers come from the same Round 2 dataset, seed, and benchmark artifact.
          </p>
        </div>
        <div className="quality-grid">
          <article>
            <Timer size={18} />
            <span>Optimized P50</span>
            <strong className="mono">{formatMs(benchmark.optimized_latency_ms).toUpperCase()}</strong>
          </article>
          <article>
            <Gauge size={18} />
            <span>Route quality delta</span>
            <strong className="mono">{benchmark.quality_delta_percent.toFixed(2)}%</strong>
          </article>
          <article>
            <ShieldCheck size={18} />
            <span>Correctness parity</span>
            <strong className="mono">{benchmark.correctness_equal ? "MATCH" : "CHECK"}</strong>
          </article>
          <article>
            <Check size={18} />
            <span>Dataset</span>
            <strong className="mono">{benchmark.dataset_version}</strong>
          </article>
        </div>
      </section>
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

function formatMs(value: number) {
  return `${value.toLocaleString("en-IN", { maximumFractionDigits: 3 })} ms`;
}

function formatKm(value: number) {
  return `${value.toLocaleString("en-IN", { maximumFractionDigits: 3 })} km`;
}

function formatSpeedup(value: number) {
  return `${formatSpeedupValue(value)} faster`;
}

function formatSpeedupValue(value: number) {
  return `${value.toFixed(2)}×`;
}