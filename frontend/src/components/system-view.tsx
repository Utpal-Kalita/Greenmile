"use client";

import { useState } from "react";
import {
  BrainCircuit,
  Check,
  ChevronDown,
  CircleDot,
  Clock3,
  Database,
  GitBranch,
  MapPinned,
  PackageCheck,
  Route,
  Sparkles,
  Truck,
} from "lucide-react";
import { engineEvents } from "@/data/mock-data";
import { cn } from "@/lib/utils";

const nodes = [
  { id: "input", label: "Input", detail: "500 stops", icon: Database },
  {
    id: "data",
    label: "Data engine",
    detail: "Validate · normalize",
    icon: GitBranch,
  },
  {
    id: "cluster",
    label: "Geo clustering",
    detail: "DBSCAN · 6 zones",
    icon: MapPinned,
  },
  {
    id: "route",
    label: "Route optimization",
    detail: "NN seed · 2-opt",
    icon: Route,
  },
];

export function SystemView() {
  const [selected, setSelected] = useState("route");
  const [eventsOpen, setEventsOpen] = useState(true);

  return (
    <div className="content-page system-page">
      <header className="page-hero system-hero">
        <div>
          <span className="eyebrow">Inside Greenmile</span>
          <h1>
            One visible system.
            <br />
            Four layers of depth.
          </h1>
        </div>
        <p>
          Follow one route from raw stops to a driver-ready operational plan.
          Every major decision stays inspectable.
        </p>
      </header>

      <section
        className="architecture-section"
        aria-labelledby="architecture-heading"
      >
        <div className="section-heading-row">
          <div>
            <span className="eyebrow">Live architecture</span>
            <h2 id="architecture-heading">From input to movement.</h2>
          </div>
          <span className="engine-status">
            <span className="status-dot" />
            Trace complete
          </span>
        </div>
        <div className="architecture-flow">
          {nodes.map((node, index) => {
            const Icon = node.icon;
            return (
              <div className="architecture-step-wrap" key={node.id}>
                <button
                  className={cn(
                    "architecture-node",
                    selected === node.id && "is-selected",
                  )}
                  onClick={() => setSelected(node.id)}
                >
                  <span className="node-index mono">0{index + 1}</span>
                  <Icon size={24} />
                  <strong>{node.label}</strong>
                  <small className="mono">{node.detail}</small>
                  <i>
                    <CircleDot size={12} />
                    Complete
                  </i>
                </button>
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
                <h3>Make the route physical.</h3>
              </div>
            </header>
            <ul>
              <li>
                <Check size={13} />
                Capacity planning
              </li>
              <li>
                <Check size={13} />
                Time windows
              </li>
              <li>
                <Check size={13} />
                Packing sequence
              </li>
              <li>
                <Check size={13} />
                Driver workflow
              </li>
            </ul>
            <div className="branch-result">
              <Truck size={18} />
              <span>Driver-ready plan</span>
            </div>
          </article>
          <div className="branch-junction">
            <span />
            <i>ROUTE READY</i>
            <span />
          </div>
          <article className="ai-branch">
            <header>
              <BrainCircuit size={20} />
              <div>
                <span className="eyebrow intelligence">Intelligence</span>
                <h3>See beyond distance.</h3>
              </div>
            </header>
            <ul>
              <li>
                <Check size={13} />
                Return probability
              </li>
              <li>
                <Check size={13} />
                Anomaly detection
              </li>
              <li>
                <Check size={13} />
                Risk explanation
              </li>
              <li>
                <Check size={13} />
                Action briefing
              </li>
            </ul>
            <div className="branch-result">
              <Sparkles size={18} />
              <span>Operational context</span>
            </div>
          </article>
        </div>
        <div className="architecture-result">
          <span>Operations</span>
          <i />
          <strong>GREENMILE</strong>
          <i />
          <span>Intelligence</span>
        </div>
      </section>

      <section className="event-section">
        <button
          className="event-toggle"
          onClick={() => setEventsOpen(!eventsOpen)}
          aria-expanded={eventsOpen}
        >
          <div>
            <Clock3 size={18} />
            <span>
              <small className="eyebrow">Technical drawer</small>
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
            {engineEvents.map((event) => (
              <div className="event-row" key={event.timestamp}>
                <time className="mono">{event.timestamp}</time>
                <strong className="mono">{event.type}</strong>
                <span>{event.value}</span>
                <span className="event-status">
                  <Check size={12} />
                  {event.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="principle-strip">
        <span className="mono">SYSTEM PRINCIPLE / 01</span>
        <p>
          <strong>The route never waits for AI.</strong> The operational result
          is useful on its own; intelligence enriches it asynchronously.
        </p>
      </section>
    </div>
  );
}
