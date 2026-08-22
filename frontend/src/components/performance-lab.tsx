"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  Check,
  Gauge,
  Play,
  ShieldCheck,
  Timer,
} from "lucide-react";
import { api } from "@/lib/api";
import type { Benchmark, Scenario } from "@/types/api";

export function PerformanceLab() {
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [benchmarks, setBenchmarks] = useState<Benchmark[]>([]);
  const [workload, setWorkload] = useState(500);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    void Promise.all([api.getDemoScenario(), api.getBenchmarks()])
      .then(([demo, records]) => {
        setScenario(demo);
        setBenchmarks(latestByWorkload(records));
      })
      .catch((reason) =>
        setError(
          reason instanceof Error ? reason.message : "Backend unavailable",
        ),
      );
  }, []);
  const benchmark = useMemo(
    () => benchmarks.find((item) => item.stop_count === workload),
    [benchmarks, workload],
  );
  const improvement = benchmark
    ? (1 - benchmark.optimized_latency_ms / benchmark.baseline_latency_ms) * 100
    : null;
  async function runBenchmark() {
    if (!scenario) return;
    setRunning(true);
    setError("");
    try {
      const records = await api.runBenchmarks(scenario.id, [workload]);
      setBenchmarks((current) => latestByWorkload([...records, ...current]));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Benchmark failed");
    } finally {
      setRunning(false);
    }
  }
  return (
    <div className="content-page performance-page">
      <header className="page-hero performance-hero">
        <div>
          <span className="eyebrow">Greenmile performance / measured</span>
          <h1>
            We measure
            <br />
            our own optimizer.
          </h1>
        </div>
        <div className="hero-proof">
          <span className="mono">POSTGRESQL BENCHMARK</span>
          <strong className="mono">
            {improvement == null ? "—" : `${improvement.toFixed(1)}%`}
          </strong>
          <p>
            {benchmark
              ? `faster at ${benchmark.stop_count.toLocaleString()} stops`
              : "Run a workload to generate evidence"}
          </p>
        </div>
      </header>
      <section className="workload-section">
        <div className="section-heading-row">
          <div>
            <span className="eyebrow">Workload</span>
            <h2>Choose the pressure.</h2>
          </div>
          <p>
            Every value comes from executing the algorithms and persisting the
            result.
          </p>
        </div>
        <div className="workload-tabs">
          {[100, 500, 1000, 5000].map((value) => (
            <button
              key={value}
              className={workload === value ? "is-active" : ""}
              onClick={() => setWorkload(value)}
            >
              <strong className="mono">{value.toLocaleString()}</strong>
              <span>stops</span>
            </button>
          ))}
        </div>
        <button
          className="primary-button"
          style={{ marginTop: 18 }}
          onClick={runBenchmark}
          disabled={!scenario || running}
        >
          <Play size={15} />
          {running
            ? "Measuring…"
            : `Run ${workload.toLocaleString()}-stop benchmark`}
        </button>
        {error && (
          <p className="eyebrow danger" style={{ marginLeft: 16 }}>
            <AlertCircle size={12} />
            {error}
          </p>
        )}
      </section>
      {benchmark ? (
        <>
          <section className="benchmark-section">
            <div className="benchmark-head">
              <span>Measured value</span>
              <span>Baseline</span>
              <span>Optimized</span>
              <span>Change</span>
            </div>
            <BenchmarkRow
              label="Execution latency"
              before={`${benchmark.baseline_latency_ms.toFixed(1)} ms`}
              after={`${benchmark.optimized_latency_ms.toFixed(1)} ms`}
              change={`${improvement!.toFixed(1)}% faster`}
            />
            <BenchmarkRow
              label="Route distance"
              before={`${benchmark.baseline_distance_km.toFixed(1)} km`}
              after={`${benchmark.optimized_distance_km.toFixed(1)} km`}
              change={`${benchmark.route_quality_delta.toFixed(1)}%`}
            />
            <BenchmarkRow
              label="p95 latency"
              before="—"
              after={`${benchmark.p95_latency_ms.toFixed(1)} ms`}
              change="measured"
            />
            <BenchmarkRow
              label="Memory"
              before="—"
              after={`${benchmark.memory_usage_mb.toFixed(1)} MB`}
              change="observed"
            />
          </section>
          <section className="tradeoff-section">
            <div className="section-heading-row">
              <div>
                <span className="eyebrow">Correctness guardrail</span>
                <h2>Speed, with proof.</h2>
              </div>
              <p>
                Optimization only counts when route quality and feasibility
                remain visible.
              </p>
            </div>
            <div className="quality-grid">
              <article>
                <Timer size={18} />
                <span>Critical path</span>
                <strong className="mono">
                  {benchmark.optimized_latency_ms.toFixed(1)} MS
                </strong>
              </article>
              <article>
                <Gauge size={18} />
                <span>Route quality delta</span>
                <strong className="mono">
                  {benchmark.route_quality_delta.toFixed(2)}%
                </strong>
              </article>
              <article>
                <ShieldCheck size={18} />
                <span>Constraints</span>
                <strong className="mono">
                  {benchmark.constraint_violations} VIOLATIONS
                </strong>
              </article>
              <article>
                <Check size={18} />
                <span>Dataset</span>
                <strong className="mono">{benchmark.dataset_version}</strong>
              </article>
            </div>
          </section>
        </>
      ) : (
        <section className="route-loading" style={{ minHeight: 360 }}>
          <span className="eyebrow">No fabricated benchmark</span>
          <h1 style={{ fontSize: 48 }}>
            Run the engine to see measured evidence.
          </h1>
        </section>
      )}
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
function latestByWorkload(records: Benchmark[]) {
  const seen = new Set<number>();
  return [...records]
    .sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at))
    .filter((item) => !seen.has(item.stop_count) && seen.add(item.stop_count));
}
