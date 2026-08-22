"use client";

import { Check, Circle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { StageEvent } from "@/types/api";

const stages = [
  ["LOADING_DATA", "Stops loaded"],
  ["VALIDATING", "Data validated"],
  ["CLUSTERING", "Geographic zones created"],
  ["BUILDING_ROUTE", "Initial routes built"],
  ["OPTIMIZING", "Best loops found"],
  ["CHECKING_CONSTRAINTS", "Constraints checked"],
  ["CALCULATING_METRICS", "Impact calculated"],
  ["PERSISTING", "Result persisted"],
  ["ROUTE_READY", "Route ready"],
] as const;

export function EngineProgress({ events }: { events: StageEvent[] }) {
  const names = new Set(events.map((event) => event.event_type));
  const activeIndex = Math.min(names.size, stages.length - 1);
  return (
    <section
      className="engine-progress"
      aria-live="polite"
      aria-label="Optimization progress"
    >
      <div className="panel-kicker">Greenmile engine</div>
      <div className="engine-stage-list">
        {stages.map(([id, label], index) => {
          const event = events.find((item) => item.event_type === id);
          const complete = names.has(id);
          const active = !complete && index === activeIndex;
          return (
            <div
              key={id}
              className={cn(
                "engine-stage",
                complete && "is-complete",
                active && "is-active",
              )}
            >
              <span className="stage-icon">
                {complete ? (
                  <Check size={13} />
                ) : (
                  <Circle size={10} fill={active ? "currentColor" : "none"} />
                )}
              </span>
              <span className="stage-copy">
                <strong>{label}</strong>
                <small>
                  {event
                    ? summarize(event.payload)
                    : active
                      ? "Backend is working…"
                      : "Waiting"}
                </small>
              </span>
              <span className="stage-duration mono">
                {event?.duration_ms != null
                  ? `${event.duration_ms.toFixed(1)} MS`
                  : complete
                    ? "DONE"
                    : active
                      ? "RUNNING"
                      : "PENDING"}
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
function summarize(payload: Record<string, unknown>) {
  return (
    Object.entries(payload)
      .slice(0, 2)
      .map(([key, value]) => `${key.replaceAll("_", " ")} ${String(value)}`)
      .join(" · ") || "Complete"
  );
}
