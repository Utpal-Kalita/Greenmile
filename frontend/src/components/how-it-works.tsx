"use client";

import Link from "next/link";
import {
  ArrowRight,
  Check,
  Database,
  Map,
  PackageOpen,
  Play,
  Route,
  ShieldCheck,
  Sparkles,
  Truck,
} from "lucide-react";
import { useState } from "react";

const steps = [
  {
    number: "01",
    title: "Load",
    text: "Tell Greenmile where deliveries and returns are.",
    detail: "CSV or live operations data",
    icon: Database,
  },
  {
    number: "02",
    title: "Plan",
    text: "Greenmile finds the best continuous loop.",
    detail: "Cluster · sequence · improve",
    icon: Route,
  },
  {
    number: "03",
    title: "Check",
    text: "We check distance, time, capacity and risk.",
    detail: "Constraints before dispatch",
    icon: ShieldCheck,
  },
  {
    number: "04",
    title: "Go",
    text: "Load the van. Follow the route. Come home.",
    detail: "One clear operational plan",
    icon: Truck,
  },
];

const technical = [
  "DBSCAN clustering",
  "Haversine distance",
  "Nearest-neighbour seed",
  "2-opt improvement",
  "Capacity constraints",
  "Time windows",
  "AI risk reasoning",
];

export function HowItWorks() {
  const [active, setActive] = useState(0);
  const ActiveIcon = steps[active].icon;
  return (
    <div className="content-page how-page">
      <header className="page-hero how-hero">
        <div>
          <span className="eyebrow">How it works</span>
          <h1>
            Messy routes in.
            <br />
            One clear loop out.
          </h1>
        </div>
        <p>
          Simple enough to understand in four steps. Deep enough to inspect all
          the way down.
        </p>
      </header>

      <section className="simple-steps" aria-label="Greenmile process">
        <div className="step-tabs">
          {steps.map((step, index) => (
            <button
              key={step.number}
              className={active === index ? "is-active" : ""}
              onClick={() => setActive(index)}
            >
              <span className="mono">{step.number}</span>
              <strong>{step.title}</strong>
            </button>
          ))}
        </div>
        <div className="active-step">
          <div className="active-step-visual">
            <span className="visual-orbit orbit-one" />
            <span className="visual-orbit orbit-two" />
            <ActiveIcon size={52} strokeWidth={1.2} />
            <span className="mono">STEP / {steps[active].number}</span>
          </div>
          <div className="active-step-copy">
            <span className="eyebrow">{steps[active].detail}</span>
            <h2>{steps[active].title}</h2>
            <p>{steps[active].text}</p>
            <div className="step-progress">
              {steps.map((step, index) => (
                <button
                  key={step.number}
                  aria-label={`Show step ${step.number}`}
                  className={active === index ? "is-active" : ""}
                  onClick={() => setActive(index)}
                />
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="concept-loop">
        <div className="section-heading-row">
          <div>
            <span className="eyebrow">The idea in one glance</span>
            <h2>No empty second trip.</h2>
          </div>
          <p>The greenest mile is the one you don’t drive twice.</p>
        </div>
        <div className="concept-comparison">
          <article className="old-concept">
            <span className="concept-label">Before</span>
            <div className="mini-flow">
              <b>
                <PackageOpen size={16} />
                Warehouse
              </b>
              <ArrowRight />
              <b>Deliveries</b>
              <ArrowRight />
              <b>Warehouse</b>
            </div>
            <div className="mini-flow faded">
              <b>
                <PackageOpen size={16} />
                Warehouse
              </b>
              <ArrowRight />
              <b>Returns</b>
              <ArrowRight />
              <b>Warehouse</b>
            </div>
            <strong className="mono">2 TRIPS / EMPTY LEGS</strong>
          </article>
          <ArrowRight className="concept-arrow" />
          <article className="new-concept">
            <span className="concept-label">After</span>
            <div className="loop-diagram">
              <Map size={28} />
              <span>DELIVER</span>
              <i />
              <span>COLLECT</span>
              <i />
              <b>
                <Route size={20} />
                ONE LOOP
              </b>
            </div>
            <strong className="mono">1 TRIP / BOTH WAYS</strong>
          </article>
        </div>
      </section>

      <section className="under-hood">
        <div className="hood-heading">
          <span className="eyebrow">Under the hood</span>
          <h2>Engineering, not magic.</h2>
          <p>
            Each layer has one job. Together, they turn geography and
            constraints into movement.
          </p>
        </div>
        <div className="technical-list">
          {technical.map((item, index) => (
            <div key={item}>
              <span className="mono">{String(index + 1).padStart(2, "0")}</span>
              <strong>{item}</strong>
              <Check size={14} />
            </div>
          ))}
        </div>
      </section>

      <section className="how-cta">
        <div>
          <Sparkles size={20} />
          <span className="eyebrow">Ready in one click</span>
          <h2>Watch the engine build the loop.</h2>
        </div>
        <Link href="/" className="primary-button">
          <Play size={15} fill="currentColor" /> Try Delhi demo
        </Link>
      </section>
    </div>
  );
}
