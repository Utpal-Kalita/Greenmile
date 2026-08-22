"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type {
  DivIcon,
  LayerGroup,
  Map as LeafletMap,
  Marker,
} from "leaflet";
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

type LeafletModule = typeof import("leaflet");
type PointKind = "delivery" | "return";

type MapPoint = {
  id: string;
  name: string;
  address: string;
  kind: PointKind;
  lat: number;
  lng: number;
  sequence?: number;
  vehicle?: number;
};

const DELHI_CENTER: [number, number] = [28.6139, 77.209];
const ROUTE_COLORS = ["#45f27a", "#70a7ff", "#f5b84b", "#c084fc", "#22d3ee"];

export function RouteMap({
  scenario,
  stops = [],
  route = [],
  before = false,
  compact = false,
  className,
  activeStop,
}: RouteMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<LeafletMap | null>(null);
  const layersRef = useRef<LayerGroup | null>(null);
  const leafletRef = useRef<LeafletModule | null>(null);
  const interactionTimerRef = useRef<number | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const [isInteracting, setIsInteracting] = useState(false);
  const points = useMemo(() => mapPoints(stops, route), [stops, route]);

  function beginInteraction() {
    if (interactionTimerRef.current !== null) {
      window.clearTimeout(interactionTimerRef.current);
    }
    setIsInteracting(true);
  }

  function finishInteraction() {
    if (interactionTimerRef.current !== null) {
      window.clearTimeout(interactionTimerRef.current);
    }
    interactionTimerRef.current = window.setTimeout(() => {
      setIsInteracting(false);
      interactionTimerRef.current = null;
    }, 500);
  }

  useEffect(() => {
    let cancelled = false;
    let map: LeafletMap | null = null;

    void import("leaflet").then((L) => {
      if (cancelled || !containerRef.current) return;

      map = L.map(containerRef.current, {
        center: DELHI_CENTER,
        zoom: 11,
        zoomControl: false,
        preferCanvas: true,
      });
      L.tileLayer(
        "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        {
          attribution:
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
          className: "greenmile-basemap",
          maxZoom: 20,
          subdomains: "abcd",
        },
      ).addTo(map);
      L.control.zoom({ position: "bottomright" }).addTo(map);
      L.control.scale({ imperial: false, position: "bottomleft" }).addTo(map);

      leafletRef.current = L;
      mapRef.current = map;
      layersRef.current = L.layerGroup().addTo(map);
      setMapReady(true);
      window.setTimeout(() => map?.invalidateSize(false), 0);
    });

    return () => {
      cancelled = true;
      if (interactionTimerRef.current !== null) {
        window.clearTimeout(interactionTimerRef.current);
      }
      map?.remove();
      mapRef.current = null;
      layersRef.current = null;
      leafletRef.current = null;
    };
  }, []);

  useEffect(() => {
    const L = leafletRef.current;
    const map = mapRef.current;
    const layers = layersRef.current;
    if (!mapReady || !L || !map || !layers) return;

    layers.clearLayers();
    if (!scenario) {
      map.setView(DELHI_CENTER, 11, { animate: false });
      return;
    }

    const depot: [number, number] = [scenario.depot_lat, scenario.depot_lng];
    drawRoutes(L, layers, depot, stops, route, before);

    const depotMarker = L.marker(depot, {
      icon: depotIcon(L),
      title: `Depot: ${scenario.depot_address}`,
      zIndexOffset: 1000,
    }).addTo(layers);
    bindPopup(depotMarker, "DEPOT", "Warehouse", scenario.depot_address);

    for (const point of points) {
      const marker = L.marker([point.lat, point.lng], {
        icon: stopIcon(L, point, activeStop === point.id),
        riseOnHover: true,
        title: `${point.id}: ${point.name}`,
      }).addTo(layers);
      const detail = [
        point.kind === "delivery" ? "Delivery" : "Return",
        point.vehicle ? `Vehicle ${point.vehicle}` : null,
        point.sequence !== undefined ? `Stop ${point.sequence}` : null,
      ]
        .filter(Boolean)
        .join(" · ");
      bindPopup(marker, point.id, detail, point.address);
      if (activeStop === point.id) {
        marker.openPopup();
        map.panTo([point.lat, point.lng], { animate: true });
      }
    }

    const bounds = L.latLngBounds([
      depot,
      ...points.map((point) => [point.lat, point.lng] as [number, number]),
    ]);
    if (points.length) {
      map.fitBounds(bounds, {
        animate: false,
        maxZoom: 14,
        padding: compact ? [34, 34] : [64, 64],
      });
    } else {
      map.setView(depot, 13, { animate: false });
    }
    window.setTimeout(() => map.invalidateSize(false), 0);
  }, [activeStop, before, compact, mapReady, points, route, scenario, stops]);

  return (
    <div
      className={cn(
        "route-map",
        compact && "is-compact",
        route.length > 0 && "is-optimized",
        isInteracting && "is-interacting",
        className,
      )}
      onBlur={finishInteraction}
      onKeyDown={beginInteraction}
      onKeyUp={finishInteraction}
      onPointerCancel={finishInteraction}
      onPointerDown={beginInteraction}
      onPointerLeave={finishInteraction}
      onPointerUp={finishInteraction}
      onWheel={() => {
        beginInteraction();
        finishInteraction();
      }}
      role="region"
      aria-label={
        before
          ? "Interactive map comparing separate delivery and return routes"
          : route.length
            ? "Interactive map of the computed Greenmile routes"
            : "Interactive map of scenario stops"
      }
    >
      <div ref={containerRef} className="map-canvas" />
      {!mapReady && <div className="map-loading mono">LOADING OPENSTREETMAP</div>}
      <div className="map-status-panel">
        <span className="map-status-live mono">
          <i /> OPENSTREETMAP
        </span>
        <strong>{scenario?.city || "Delhi"}</strong>
        <span className="map-status-detail mono">
          {scenario
            ? `${points.length} STOPS · ${scenario.depot_lat.toFixed(4)}, ${scenario.depot_lng.toFixed(4)}`
            : "BASEMAP READY"}
        </span>
      </div>
      <div className={cn("map-legend", compact && "is-compact")}>
        <span>
          <i className="legend-dot depot" />
          Depot
        </span>
        <span>
          <i className="legend-dot delivery" />
          Delivery
        </span>
        <span>
          <i className="legend-dot returns" />
          Return
        </span>
        {(before || route.length > 0) && (
          <span>
            <i className={cn("legend-route", before && "is-before")} />
            {before ? "Separate routes" : "Vehicle routes"}
          </span>
        )}
      </div>
    </div>
  );
}

function mapPoints(stops: Stop[], route: RouteStop[]): MapPoint[] {
  if (!route.length) {
    return stops.map((stop) => ({
      id: stop.external_id,
      name: stop.address,
      address: stop.address,
      kind: stop.type === "DELIVERY" ? "delivery" : "return",
      lat: stop.lat,
      lng: stop.lng,
    }));
  }

  const seen = new Set<string>();
  return route.flatMap((stop) => {
    if (
      stop.type === "WAREHOUSE" ||
      stop.external_id === "DEPOT" ||
      seen.has(stop.external_id)
    ) {
      return [];
    }
    seen.add(stop.external_id);
    return [
      {
        id: stop.external_id,
        name: stop.name,
        address: stop.address,
        kind: stop.type === "DELIVERY" ? ("delivery" as const) : ("return" as const),
        lat: stop.lat,
        lng: stop.lng,
        sequence: stop.sequence_number,
        vehicle: stop.vehicle_sequence,
      },
    ];
  });
}

function drawRoutes(
  L: LeafletModule,
  layers: LayerGroup,
  depot: [number, number],
  stops: Stop[],
  route: RouteStop[],
  before: boolean,
) {
  if (before) {
    const deliveries = stops
      .filter((stop) => stop.type === "DELIVERY")
      .map((stop) => [stop.lat, stop.lng] as [number, number]);
    const returns = stops
      .filter((stop) => stop.type !== "DELIVERY")
      .map((stop) => [stop.lat, stop.lng] as [number, number]);
    addPolyline(
      L,
      layers,
      [depot, ...deliveries, depot],
      "#70a7ff",
      "Deliveries",
      undefined,
      4,
      "is-baseline-delivery",
    );
    addPolyline(
      L,
      layers,
      [depot, ...returns, depot],
      "#e37754",
      "Returns",
      "8 8",
      4,
      "is-baseline-return",
    );
    return;
  }

  const vehicles = new Map<number, RouteStop[]>();
  for (const stop of route) {
    const vehicleStops = vehicles.get(stop.vehicle_sequence) ?? [];
    vehicleStops.push(stop);
    vehicles.set(stop.vehicle_sequence, vehicleStops);
  }
  [...vehicles.entries()]
    .sort(([first], [second]) => first - second)
    .forEach(([vehicle, vehicleStops], index) => {
      const coordinates = vehicleStops
        .sort((first, second) => first.sequence_number - second.sequence_number)
        .map((stop) => [stop.lat, stop.lng] as [number, number]);
      if (!coordinates.length || !sameCoordinate(coordinates[0], depot)) {
        coordinates.unshift(depot);
      }
      if (!sameCoordinate(coordinates.at(-1), depot)) coordinates.push(depot);

      const color = ROUTE_COLORS[index % ROUTE_COLORS.length];
      L.polyline(coordinates, {
        className: "greenmile-route-shadow",
        color: "#07100c",
        opacity: 0.55,
        weight: 10,
        lineCap: "round",
        lineJoin: "round",
      }).addTo(layers);
      addPolyline(
        L,
        layers,
        coordinates,
        color,
        `Vehicle ${vehicle}`,
        undefined,
        5,
        "is-optimized",
      );
    });
}

function addPolyline(
  L: LeafletModule,
  layers: LayerGroup,
  coordinates: [number, number][],
  color: string,
  label: string,
  dashArray?: string,
  weight = 4,
  className?: string,
) {
  if (coordinates.length < 3) return;
  L.polyline(coordinates, {
    className: cn("greenmile-route-line", className),
    color,
    dashArray,
    opacity: 0.9,
    weight,
    lineCap: "round",
    lineJoin: "round",
  })
    .bindTooltip(label, { className: "greenmile-route-tooltip", sticky: true })
    .addTo(layers);
}

function sameCoordinate(
  first: [number, number] | undefined,
  second: [number, number],
) {
  return first?.[0] === second[0] && first[1] === second[1];
}

function depotIcon(L: LeafletModule): DivIcon {
  return L.divIcon({
    className: "greenmile-div-icon",
    html: '<span class="leaflet-depot-marker"><b>W</b></span>',
    iconAnchor: [18, 18],
    iconSize: [36, 36],
  });
}

function stopIcon(L: LeafletModule, point: MapPoint, active: boolean): DivIcon {
  const numbered = point.sequence !== undefined;
  return L.divIcon({
    className: "greenmile-div-icon",
    html: `<span class="leaflet-stop-marker is-${point.kind}${active ? " is-active" : ""}">${numbered ? `<b>${point.sequence}</b>` : ""}</span>`,
    iconAnchor: numbered ? [14, 14] : [9, 9],
    iconSize: numbered ? [28, 28] : [18, 18],
  });
}

function bindPopup(marker: Marker, title: string, detail: string, address: string) {
  const popup = document.createElement("div");
  const heading = document.createElement("strong");
  const meta = document.createElement("span");
  const location = document.createElement("small");
  heading.textContent = title;
  meta.textContent = detail;
  location.textContent = address;
  popup.append(heading, meta, location);
  marker.bindPopup(popup, { className: "greenmile-map-popup" });
}
