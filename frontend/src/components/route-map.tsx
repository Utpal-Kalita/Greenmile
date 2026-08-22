"use client";

import { useId } from "react";
import { MapPin, PackageCheck, RotateCcw } from "lucide-react";
import { stops } from "@/data/mock-data";
import { cn } from "@/lib/utils";

interface RouteMapProps {
  optimized?: boolean;
  before?: boolean;
  compact?: boolean;
  className?: string;
  activeStop?: string;
}

const afterPath =
  "M 500 770 C 470 680, 405 575, 400 470 C 375 390, 298 420, 300 380 C 270 300, 340 225, 360 230 C 300 160, 190 180, 170 160 C 290 225, 470 330, 560 350 C 620 385, 700 420, 700 450 C 690 525, 635 580, 660 620 C 630 710, 550 740, 500 770";
const deliveryPath =
  "M 500 770 C 480 650, 410 560, 400 470 C 360 405, 315 410, 300 380 C 260 310, 330 245, 360 230 C 300 185, 220 170, 170 160";
const returnPath =
  "M 500 770 C 610 700, 680 640, 660 620 C 710 565, 735 490, 700 450 C 680 400, 610 355, 560 350 C 535 470, 520 650, 500 770";

export function RouteMap({
  optimized = false,
  before = false,
  compact = false,
  className,
  activeStop,
}: RouteMapProps) {
  const patternId = useId().replace(/:/g, "");
  return (
    <div
      className={cn(
        "route-map",
        compact && "is-compact",
        optimized && "is-optimized",
        className,
      )}
      role="img"
      aria-label={
        before
          ? "Map comparing separate delivery and return trips"
          : optimized
            ? "Optimized bidirectional route through Delhi NCR"
            : "Map of delivery and return stops in Delhi NCR"
      }
    >
      <svg
        className="map-canvas"
        viewBox="0 0 1000 800"
        preserveAspectRatio="xMidYMid slice"
        aria-hidden="true"
      >
        <defs>
          <pattern
            id={patternId}
            width="84"
            height="84"
            patternUnits="userSpaceOnUse"
            patternTransform="rotate(18)"
          >
            <path d="M 0 42 H 84 M 42 0 V 84" className="map-grid-line" />
          </pattern>
          <filter
            id={`${patternId}-glow`}
            x="-40%"
            y="-40%"
            width="180%"
            height="180%"
          >
            <feGaussianBlur stdDeviation="5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <rect width="1000" height="800" className="map-ground" />
        <rect width="1000" height="800" fill={`url(#${patternId})`} />
        <g className="map-blocks">
          <path d="M-20 630 C160 555 230 625 385 540 S690 445 1020 535" />
          <path d="M70 -20 C160 160 175 290 335 425 S520 680 580 830" />
          <path d="M-20 270 C180 305 310 250 470 315 S735 340 1020 190" />
          <path d="M780 -20 C690 170 685 300 760 455 S865 650 820 830" />
          <path d="M230 -20 C250 135 390 180 520 165 S800 95 1020 135" />
        </g>
        {before ? (
          <g className="route-before">
            <path d={deliveryPath} className="route-line delivery-line" />
            <path d={returnPath} className="route-line wasted-line" />
          </g>
        ) : (
          <>
            <path
              d={afterPath}
              className={cn(
                "route-line",
                optimized ? "optimized-line" : "ghost-line",
              )}
              filter={optimized ? `url(#${patternId}-glow)` : undefined}
            />
            {!optimized && (
              <path d={deliveryPath} className="route-line draft-line" />
            )}
          </>
        )}
      </svg>

      {stops.map((stop, index) => (
        <div
          key={stop.id}
          className={cn(
            "map-stop",
            `is-${stop.kind}`,
            stop.risk && `risk-${stop.risk}`,
            activeStop === stop.id && "is-active",
          )}
          style={{
            left: `${stop.x}%`,
            top: `${stop.y}%`,
            animationDelay: `${index * 55}ms`,
          }}
          title={`${stop.id} · ${stop.name}`}
        >
          <span className="stop-core">
            {stop.kind === "warehouse" ? (
              <MapPin size={14} />
            ) : stop.kind === "delivery" ? (
              <PackageCheck size={11} />
            ) : (
              <RotateCcw size={11} />
            )}
          </span>
          {(stop.kind === "warehouse" ||
            activeStop === stop.id ||
            stop.risk === "high") && (
            <span className="stop-label">
              {stop.id === "DEPOT" ? "DEPOT" : stop.id}
            </span>
          )}
        </div>
      ))}

      <div className="map-location-label label-one">HAUZ KHAS</div>
      <div className="map-location-label label-two">OKHLA</div>
      <div className="map-location-label label-three">SAKET</div>
      <div className="map-coordinates mono">
        28.5355° N<br />
        77.2100° E
      </div>
      <div className="map-scale mono">
        <span /> 5 KM
      </div>
      {!compact && (
        <div className="map-legend">
          <span>
            <i className="legend-dot delivery" />
            Delivery
          </span>
          <span>
            <i className="legend-dot returns" />
            Return
          </span>
          <span>
            <i className="legend-dot warning" />
            Risk
          </span>
        </div>
      )}
    </div>
  );
}
