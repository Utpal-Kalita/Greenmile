import type { StyleSpecification } from "maplibre-gl";
import type {
  GeoJSONFeature,
  GeoJSONFeatureCollection,
  GeoJSONPosition,
} from "../../types/api";

export const EMPTY_FEATURE_COLLECTION: GeoJSONFeatureCollection = {
  type: "FeatureCollection",
  features: [],
};

export function mapTilerStyleUrl(apiKey: string): string {
  return `https://api.maptiler.com/maps/dataviz-dark/style.json?key=${encodeURIComponent(apiKey)}`;
}

export function fallbackMapStyle(): StyleSpecification {
  return {
    version: 8,
    name: "Greenmile route fallback",
    sources: {},
    layers: [
      {
        id: "greenmile-background",
        type: "background",
        paint: { "background-color": "#07110D" },
      },
    ],
  };
}

export function routeAnimationFrame(
  collection: GeoJSONFeatureCollection,
  progress: number,
): GeoJSONFeatureCollection {
  const clamped = Math.max(0, Math.min(progress, 1));
  return {
    type: "FeatureCollection",
    features: collection.features.flatMap((feature) => {
      if (feature.geometry.type !== "LineString") return [feature];
      const coordinates = feature.geometry.coordinates as GeoJSONPosition[];
      if (clamped <= 0 || coordinates.length < 2) return [];
      const visible = Math.max(2, Math.ceil(coordinates.length * clamped));
      return [
        {
          ...feature,
          geometry: {
            ...feature.geometry,
            coordinates: coordinates.slice(0, visible),
          },
        },
      ];
    }),
  };
}

export function changedRouteCollection(
  previous: GeoJSONFeatureCollection,
  updated: GeoJSONFeatureCollection,
): GeoJSONFeatureCollection {
  const previousByVehicle = new Map(
    previous.features.map((feature) => [
      Number(feature.properties.vehicle_sequence ?? 1),
      feature,
    ]),
  );
  const features: GeoJSONFeature[] = [];

  for (const feature of updated.features) {
    const vehicle = Number(feature.properties.vehicle_sequence ?? 1);
    const prior = previousByVehicle.get(vehicle);
    const nextIds = stringArray(feature.properties.stop_ids);
    const priorIds = prior ? stringArray(prior.properties.stop_ids) : [];
    if (!prior || feature.geometry.type !== "LineString") {
      features.push(feature);
      continue;
    }
    if (sameStrings(priorIds, nextIds)) continue;

    let prefix = 0;
    while (
      prefix < priorIds.length &&
      prefix < nextIds.length &&
      priorIds[prefix] === nextIds[prefix]
    ) {
      prefix += 1;
    }
    let suffix = 0;
    while (
      suffix < priorIds.length - prefix &&
      suffix < nextIds.length - prefix &&
      priorIds[priorIds.length - 1 - suffix] ===
        nextIds[nextIds.length - 1 - suffix]
    ) {
      suffix += 1;
    }

    const coordinates = feature.geometry.coordinates as GeoJSONPosition[];
    const start = Math.max(0, prefix);
    const end = Math.min(coordinates.length, nextIds.length - suffix + 2);
    const changedCoordinates = coordinates.slice(start, Math.max(start + 2, end));
    if (changedCoordinates.length < 2) continue;
    features.push({
      ...feature,
      geometry: { ...feature.geometry, coordinates: changedCoordinates },
      properties: { ...feature.properties, route_kind: "ROUTE_UPDATE" },
    });
  }

  return { type: "FeatureCollection", features };
}

export function featureCollection(
  features: GeoJSONFeature[] = [],
): GeoJSONFeatureCollection {
  return { type: "FeatureCollection", features };
}

function stringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function sameStrings(first: string[], second: string[]): boolean {
  return (
    first.length === second.length &&
    first.every((value, index) => value === second[index])
  );
}
