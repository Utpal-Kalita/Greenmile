"use client";

import { Check, Circle } from "lucide-react";
import { engineStages } from "@/data/mock-data";
import { cn } from "@/lib/utils";

export function EngineProgress({ activeIndex }: { activeIndex: number }) {
  return (
    <section
      className="engine-progress"
      aria-live="polite"
      aria-label="Optimization progress"
    >
      <div className="panel-kicker">Greenmile engine</div>
      <div className="engine-stage-list">
        {engineStages.map((stage, index) => {
          const complete = index < activeIndex;
          const active = index === activeIndex;
          return (
            <div
              key={stage.id}
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
                <strong>{stage.label}</strong>
                <small>{stage.detail}</small>
              </span>
              <span className="stage-duration mono">
                {complete ? stage.duration : active ? "RUNNING" : "PENDING"}
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
