import type {
  GeoJSONSource,
  Map as MapLibreMap,
} from "maplibre-gl";
import type {
  GeoJSONFeatureCollection,
  MapPayload,
} from "../../types/api";
import { EMPTY_FEATURE_COLLECTION, featureCollection } from "./map-utils";

export type MapMode = "before" | "after" | "compare";

export const MAP_SOURCE_IDS = {
  stops: "greenmile-stops",
  warehouse: "greenmile-warehouse",
  baselineDelivery: "greenmile-baseline-delivery",
  baselineReturn: "greenmile-baseline-return",
  optimized: "greenmile-optimized",
  animation: "greenmile-route-animation",
  change: "greenmile-route-change",
  events: "greenmile-events",
} as const;

export const MAP_LAYER_IDS = {
  baselineDelivery: "greenmile-baseline-delivery-line",
  baselineReturn: "greenmile-baseline-return-line",
  optimizedShadow: "greenmile-optimized-shadow",
  optimized: "greenmile-optimized-line",
  animation: "greenmile-route-animation-line",
  change: "greenmile-route-change-line",
  riskHalo: "greenmile-risk-halo",
  deliveryStops: "greenmile-delivery-stops",
  returnStops: "greenmile-return-stops",
  selectedStop: "greenmile-selected-stop",
  stopLabels: "greenmile-stop-labels",
  warehouse: "greenmile-warehouse-dot",
  warehouseLabel: "greenmile-warehouse-label",
  events: "greenmile-event-halo",
} as const;

export function installMapLayers(map: MapLibreMap): void {
  addSource(map, MAP_SOURCE_IDS.baselineDelivery);
  addSource(map, MAP_SOURCE_IDS.baselineReturn);
  addSource(map, MAP_SOURCE_IDS.optimized);
  addSource(map, MAP_SOURCE_IDS.animation, true);
  addSource(map, MAP_SOURCE_IDS.change, true);
  addSource(map, MAP_SOURCE_IDS.stops);
  addSource(map, MAP_SOURCE_IDS.warehouse);
  addSource(map, MAP_SOURCE_IDS.events);

  addLayer(map, {
    id: MAP_LAYER_IDS.baselineDelivery,
    type: "line",
    source: MAP_SOURCE_IDS.baselineDelivery,
    paint: {
      "line-color": "#70A7FF",
      "line-width": 3,
      "line-opacity": 0.68,
    },
    layout: { "line-cap": "round", "line-join": "round" },
  });
  addLayer(map, {
    id: MAP_LAYER_IDS.baselineReturn,
    type: "line",
    source: MAP_SOURCE_IDS.baselineReturn,
    paint: {
      "line-color": "#E37754",
      "line-width": 3,
      "line-opacity": 0.62,
      "line-dasharray": [2, 2],
    },
    layout: { "line-cap": "round", "line-join": "round" },
  });
  addLayer(map, {
    id: MAP_LAYER_IDS.optimizedShadow,
    type: "line",
    source: MAP_SOURCE_IDS.optimized,
    paint: {
      "line-color": "#0F8F4F",
      "line-width": 9,
      "line-opacity": 0.3,
      "line-blur": 2,
    },
    layout: { "line-cap": "round", "line-join": "round" },
  });
  addLayer(map, {
    id: MAP_LAYER_IDS.optimized,
    type: "line",
    source: MAP_SOURCE_IDS.optimized,
    paint: {
      "line-color": "#45F27A",
      "line-width": 5,
      "line-opacity": 0.95,
    },
    layout: { "line-cap": "round", "line-join": "round" },
  });
  addLayer(map, {
    id: MAP_LAYER_IDS.animation,
    type: "line",
    source: MAP_SOURCE_IDS.animation,
    paint: {
      "line-color": "#9BFFB9",
      "line-width": 6,
      "line-opacity": 1,
    },
    layout: { "line-cap": "round", "line-join": "round" },
  });
  addLayer(map, {
    id: MAP_LAYER_IDS.change,
    type: "line",
    source: MAP_SOURCE_IDS.change,
    paint: {
      "line-color": "#F5B84B",
      "line-width": 7,
      "line-opacity": 0.92,
      "line-dasharray": [1.4, 1.2],
    },
    layout: { "line-cap": "round", "line-join": "round" },
  });
  addLayer(map, {
    id: MAP_LAYER_IDS.riskHalo,
    type: "circle",
    source: MAP_SOURCE_IDS.stops,
    filter: [
      "any",
      ["==", ["get", "risk"], "HIGH"],
      [">=", ["coalesce", ["get", "return_probability"], 0], 0.7],
    ],
    paint: {
      "circle-radius": 13,
      "circle-color": "rgba(245,184,75,0.12)",
      "circle-stroke-color": "#F5B84B",
      "circle-stroke-width": 2,
      "circle-opacity": 0.8,
    },
  });
  addLayer(map, {
    id: MAP_LAYER_IDS.deliveryStops,
    type: "circle",
    source: MAP_SOURCE_IDS.stops,
    filter: ["==", ["get", "type"], "DELIVERY"],
    paint: {
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 8, 3, 14, 7],
      "circle-color": "#70A7FF",
      "circle-stroke-color": "#07110D",
      "circle-stroke-width": 1.5,
    },
  });
  addLayer(map, {
    id: MAP_LAYER_IDS.returnStops,
    type: "circle",
    source: MAP_SOURCE_IDS.stops,
    filter: ["in", ["get", "type"], ["literal", ["RETURN", "PICKUP"]]],
    paint: {
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 8, 3.5, 14, 7.5],
      "circle-color": "#45F27A",
      "circle-stroke-color": "#07110D",
      "circle-stroke-width": 1.5,
    },
  });
  addLayer(map, {
    id: MAP_LAYER_IDS.selectedStop,
    type: "circle",
    source: MAP_SOURCE_IDS.stops,
    filter: ["==", ["get", "database_id"], ""],
    paint: {
      "circle-radius": 15,
      "circle-color": "rgba(69,242,122,0.08)",
      "circle-stroke-color": "#F3F7F4",
      "circle-stroke-width": 2,
    },
  });
  addLayer(map, {
    id: MAP_LAYER_IDS.stopLabels,
    type: "symbol",
    source: MAP_SOURCE_IDS.stops,
    minzoom: 12,
    layout: {
      "text-field": ["get", "stop_id"],
      "text-size": 10,
      "text-offset": [0, 1.25],
      "text-allow-overlap": false,
    },
    paint: {
      "text-color": "#F3F7F4",
      "text-halo-color": "#07110D",
      "text-halo-width": 1.5,
    },
  });
  addLayer(map, {
    id: MAP_LAYER_IDS.warehouse,
    type: "circle",
    source: MAP_SOURCE_IDS.warehouse,
    paint: {
      "circle-radius": 11,
      "circle-color": "#07110D",
      "circle-stroke-color": "#45F27A",
      "circle-stroke-width": 3,
    },
  });
  addLayer(map, {
    id: MAP_LAYER_IDS.warehouseLabel,
    type: "symbol",
    source: MAP_SOURCE_IDS.warehouse,
    layout: {
      "text-field": "W  WAREHOUSE",
      "text-size": 11,
      "text-offset": [0, 1.7],
      "text-anchor": "top",
    },
    paint: {
      "text-color": "#45F27A",
      "text-halo-color": "#07110D",
      "text-halo-width": 2,
    },
  });
  addLayer(map, {
    id: MAP_LAYER_IDS.events,
    type: "circle",
    source: MAP_SOURCE_IDS.events,
    paint: {
      "circle-radius": 16,
      "circle-color": "rgba(255,92,92,0.12)",
      "circle-stroke-color": "#FF5C5C",
      "circle-stroke-width": 3,
    },
  });
}

export function updateMapSources(map: MapLibreMap, data: MapPayload): void {
  setSourceData(map, MAP_SOURCE_IDS.stops, data.stops);
  setSourceData(
    map,
    MAP_SOURCE_IDS.warehouse,
    featureCollection([data.warehouse]),
  );
  setSourceData(
    map,
    MAP_SOURCE_IDS.baselineDelivery,
    data.routes.baseline_delivery,
  );
  setSourceData(
    map,
    MAP_SOURCE_IDS.baselineReturn,
    data.routes.baseline_return,
  );
  setSourceData(map, MAP_SOURCE_IDS.optimized, data.routes.optimized);
  setSourceData(map, MAP_SOURCE_IDS.events, data.events);
}

export function setSourceData(
  map: MapLibreMap,
  sourceId: string,
  data: GeoJSONFeatureCollection,
): void {
  const source = map.getSource(sourceId) as GeoJSONSource | undefined;
  source?.setData(data as Parameters<GeoJSONSource["setData"]>[0]);
}

export function setMapMode(map: MapLibreMap, mode: MapMode): void {
  const showBaseline = mode !== "after";
  const showOptimized = mode !== "before";
  setVisibility(map, MAP_LAYER_IDS.baselineDelivery, showBaseline);
  setVisibility(map, MAP_LAYER_IDS.baselineReturn, showBaseline);
  setVisibility(map, MAP_LAYER_IDS.optimizedShadow, showOptimized);
  setVisibility(map, MAP_LAYER_IDS.optimized, showOptimized);
  setVisibility(map, MAP_LAYER_IDS.animation, showOptimized);
  setVisibility(map, MAP_LAYER_IDS.change, showOptimized);
  if (map.getLayer(MAP_LAYER_IDS.baselineDelivery)) {
    map.setPaintProperty(
      MAP_LAYER_IDS.baselineDelivery,
      "line-opacity",
      mode === "compare" ? 0.3 : 0.68,
    );
  }
  if (map.getLayer(MAP_LAYER_IDS.baselineReturn)) {
    map.setPaintProperty(
      MAP_LAYER_IDS.baselineReturn,
      "line-opacity",
      mode === "compare" ? 0.28 : 0.62,
    );
  }
}

export function setSelectedStop(map: MapLibreMap, databaseId: string | null): void {
  if (!map.getLayer(MAP_LAYER_IDS.selectedStop)) return;
  map.setFilter(MAP_LAYER_IDS.selectedStop, [
    "==",
    ["get", "database_id"],
    databaseId ?? "",
  ]);
}

export function fitMapToPayload(
  map: MapLibreMap,
  data: MapPayload,
  compact: boolean,
): void {
  const { west, south, east, north } = data.map.bounds;
  map.fitBounds(
    [
      [west, south],
      [east, north],
    ],
    {
      padding: compact ? 36 : 70,
      maxZoom: 14,
      duration: 650,
    },
  );
}

function addSource(
  map: MapLibreMap,
  sourceId: string,
  lineMetrics = false,
): void {
  if (map.getSource(sourceId)) return;
  map.addSource(sourceId, {
    type: "geojson",
    data: EMPTY_FEATURE_COLLECTION as Parameters<GeoJSONSource["setData"]>[0],
    lineMetrics,
    promoteId: sourceId === MAP_SOURCE_IDS.stops ? "database_id" : undefined,
  });
}

function addLayer(
  map: MapLibreMap,
  layer: Parameters<MapLibreMap["addLayer"]>[0],
): void {
  if (!map.getLayer(layer.id)) map.addLayer(layer);
}

function setVisibility(
  map: MapLibreMap,
  layerId: string,
  visible: boolean,
): void {
  if (map.getLayer(layerId)) {
    map.setLayoutProperty(layerId, "visibility", visible ? "visible" : "none");
  }
}
