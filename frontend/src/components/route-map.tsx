"use client";

import { useId, useMemo } from "react";
import { MapPin, PackageCheck, RotateCcw } from "lucide-react";
import { cn } from "@/lib/utils";
import type { RouteStop, Scenario, Stop } from "@/types/api";

interface RouteMapProps {
  scenario?: Scenario | null;
  stops?: Stop[];
  route?: RouteStop[];
  before?: boolean;
  compact?: boolean;
  className?: string;
  activeStop?: string;
}

type Point = {
  id: string;
  name: string;
  kind: "delivery" | "return" | "warehouse";
  x: number;
  y: number;
};

export function RouteMap({
  scenario,
  stops = [],
  route = [],
  before = false,
  compact = false,
  className,
  activeStop,
}: RouteMapProps) {
  const patternId = useId().replace(/:/g, "");
  const points = useMemo(
    () => projectPoints(scenario, stops, route),
    [scenario, stops, route],
  );
  const optimizedPath = useMemo(
    () => pathForRoute(scenario, route, points),
    [scenario, route, points],
  );
  const deliveryPath = useMemo(() => pathForKind(points, "delivery"), [points]);
  const returnPath = useMemo(() => pathForKind(points, "return"), [points]);

  return (
    <div
      className={cn(
        "route-map",
        compact && "is-compact",
        route.length > 0 && "is-optimized",
        className,
      )}
      role="img"
      aria-label={
        before
          ? "Map comparing separate delivery and return routes"
          : route.length
            ? "Computed Greenmile route"
            : "Scenario stops map"
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
        </g>
        {before ? (
          <g className="route-before">
            {deliveryPath && (
              <path d={deliveryPath} className="route-line delivery-line" />
            )}
            {returnPath && (
              <path d={returnPath} className="route-line wasted-line" />
            )}
          </g>
        ) : optimizedPath ? (
          <path
            d={optimizedPath}
            className="route-line optimized-line"
            filter={`url(#${patternId}-glow)`}
          />
        ) : null}
      </svg>
      {points.map((point, index) => (
        <div
          key={`${point.id}-${index}`}
          className={cn(
            "map-stop",
            `is-${point.kind}`,
            activeStop === point.id && "is-active",
          )}
          style={{
            left: `${point.x}%`,
            top: `${point.y}%`,
            animationDelay: `${Math.min(index, 25) * 25}ms`,
          }}
          title={`${point.id} · ${point.name}`}
        >
          <span className="stop-core">
            {point.kind === "warehouse" ? (
              <MapPin size={14} />
            ) : point.kind === "delivery" ? (
              <PackageCheck size={11} />
            ) : (
              <RotateCcw size={11} />
            )}
          </span>
          {(point.kind === "warehouse" || activeStop === point.id) && (
            <span className="stop-label">{point.id}</span>
          )}
        </div>
      ))}
      <div className="map-coordinates mono">
        {scenario ? `${scenario.depot_lat.toFixed(4)}° N` : "—"}
        <br />
        {scenario ? `${scenario.depot_lng.toFixed(4)}° E` : "—"}
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
        </div>
      )}
    </div>
  );
}

function projectPoints(
  scenario: Scenario | null | undefined,
  stops: Stop[],
  route: RouteStop[],
): Point[] {
  if (!scenario) return [];
  const source = route.length
    ? uniqueRoute(route)
    : stops
        .slice(0, 80)
        .map((stop) => ({
          id: stop.external_id,
          name: stop.address,
          kind:
            stop.type === "DELIVERY"
              ? ("delivery" as const)
              : ("return" as const),
          lat: stop.lat,
          lng: stop.lng,
        }));
  const coordinates = [
    { lat: scenario.depot_lat, lng: scenario.depot_lng },
    ...source,
  ];
  const lats = coordinates.map((point) => point.lat);
  const lngs = coordinates.map((point) => point.lng);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLng = Math.min(...lngs);
  const maxLng = Math.max(...lngs);
  const project = (lat: number, lng: number) => ({
    x: 8 + ((lng - minLng) / Math.max(maxLng - minLng, 0.0001)) * 84,
    y: 8 + ((maxLat - lat) / Math.max(maxLat - minLat, 0.0001)) * 84,
  });
  return [
    {
      id: "DEPOT",
      name: scenario.depot_address,
      kind: "warehouse",
      ...project(scenario.depot_lat, scenario.depot_lng),
    },
    ...source
      .slice(0, 120)
      .map((item) => ({
        id: item.id,
        name: item.name,
        kind: item.kind,
        ...project(item.lat, item.lng),
      })),
  ];
}

function uniqueRoute(route: RouteStop[]) {
  const seen = new Set<string>();
  return route
    .filter(
      (item) =>
        item.external_id !== "DEPOT" &&
        !seen.has(item.external_id) &&
        seen.add(item.external_id),
    )
    .map((item) => ({
      id: item.external_id,
      name: item.name,
      kind:
        item.type === "DELIVERY" ? ("delivery" as const) : ("return" as const),
      lat: item.lat,
      lng: item.lng,
    }));
}
function pathForRoute(
  scenario: Scenario | null | undefined,
  route: RouteStop[],
  points: Point[],
) {
  if (!scenario || !route.length || !points.length) return "";
  const lookup = new Map(points.map((point) => [point.id, point]));
  return route
    .filter((item) => item.vehicle_sequence === 1)
    .map((item, index) => {
      const point = lookup.get(item.external_id) ?? points[0];
      return `${index ? "L" : "M"} ${point.x * 10} ${point.y * 8}`;
    })
    .join(" ");
}
function pathForKind(points: Point[], kind: Point["kind"]) {
  const selected = [
    points[0],
    ...points.filter((point) => point.kind === kind),
    points[0],
  ].filter(Boolean);
  return selected
    .map(
      (point, index) => `${index ? "L" : "M"} ${point.x * 10} ${point.y * 8}`,
    )
    .join(" ");
}
