import { describe, expect, it } from "vitest";
import type { GeoJSONFeatureCollection } from "../../types/api";
import {
  changedRouteCollection,
  fallbackMapStyle,
  mapTilerStyleUrl,
  routeAnimationFrame,
} from "./map-utils";

function route(
  coordinates: number[][],
  stopIds: string[],
  vehicleSequence = 1,
): GeoJSONFeatureCollection {
  return {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        geometry: { type: "LineString", coordinates },
        properties: {
          route_kind: "OPTIMIZED",
          vehicle_sequence: vehicleSequence,
          stop_ids: stopIds,
        },
      },
    ],
  };
}

describe("map utilities", () => {
  it("builds a protected-key MapTiler Dataviz Dark style URL", () => {
    expect(mapTilerStyleUrl("public-domain-restricted-key")).toBe(
      "https://api.maptiler.com/maps/dataviz-dark/style.json?key=public-domain-restricted-key",
    );
  });

  it("provides a local dark style when map tiles are unavailable", () => {
    expect(fallbackMapStyle()).toMatchObject({
      version: 8,
      sources: {},
      layers: [{ id: "greenmile-background", type: "background" }],
    });
  });

  it("reveals route coordinates progressively after computation", () => {
    const collection = route(
      [
        [77.2, 28.5],
        [77.21, 28.51],
        [77.22, 28.52],
        [77.23, 28.53],
      ],
      ["D1", "D2"],
    );

    const halfway = routeAnimationFrame(collection, 0.5);

    expect(halfway.features[0].geometry.coordinates).toEqual([
      [77.2, 28.5],
      [77.21, 28.51],
    ]);
  });

  it("returns only the affected segment for incremental route animation", () => {
    const previous = route(
      [
        [77.2, 28.5],
        [77.21, 28.51],
        [77.22, 28.52],
        [77.23, 28.53],
        [77.24, 28.54],
        [77.2, 28.5],
      ],
      ["A", "B", "C", "D"],
    );
    const updated = route(
      [
        [77.2, 28.5],
        [77.21, 28.51],
        [77.22, 28.52],
        [77.25, 28.55],
        [77.24, 28.54],
        [77.2, 28.5],
      ],
      ["A", "B", "E", "D"],
    );

    const changed = changedRouteCollection(previous, updated);

    expect(changed.features).toHaveLength(1);
    expect(changed.features[0].geometry.coordinates).toEqual([
      [77.22, 28.52],
      [77.25, 28.55],
      [77.24, 28.54],
    ]);
  });
});
