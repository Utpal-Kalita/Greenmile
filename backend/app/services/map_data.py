from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.domain.enums import RouteAction, StopType
from app.schemas import (
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    MapBounds,
    MapCenter,
    MapPayload,
    MapPerformance,
    MapRoutes,
    MapViewport,
    ProviderAvailability,
    RunMetrics,
    ScenarioRead,
    StopRead,
)


class MapDataService:
    """Convert Greenmile domain results into MapLibre-ready GeoJSON."""

    def build(
        self,
        *,
        scenario: ScenarioRead,
        stops: Sequence[StopRead],
        baseline_routes: Sequence[Sequence[Any]],
        optimized_route: Sequence[Any] = (),
        events: Sequence[Any] = (),
        predictions: Sequence[dict[str, Any]] = (),
        metrics: RunMetrics | None = None,
        optimization_latency_ms: float | None = None,
        reoptimization_latency_ms: float | None = None,
        run_id: str | None = None,
        system_state: str = "SCENARIO_READY",
        intelligence: ProviderAvailability | None = None,
    ) -> MapPayload:
        prediction_by_stop = {
            str(item.get("stop_id")): item
            for item in predictions
            if item.get("stop_id") is not None
        }
        stop_features = [
            self._stop_feature(stop, prediction_by_stop.get(stop.external_id))
            for stop in stops
        ]
        warehouse = GeoJSONFeature(
            geometry={
                "type": "Point",
                "coordinates": [scenario.depot_lng, scenario.depot_lat],
            },
            properties={
                "kind": "WAREHOUSE",
                "stop_id": "DEPOT",
                "address": scenario.depot_address,
            },
        )

        delivery_features: list[GeoJSONFeature] = []
        return_features: list[GeoJSONFeature] = []
        for route in baseline_routes:
            feature = self._route_feature(route, scenario, optimized=False)
            if feature is None:
                continue
            if feature.properties["route_kind"] == "DELIVERY":
                delivery_features.append(feature)
            else:
                return_features.append(feature)

        return MapPayload(
            scenario_id=scenario.id,
            run_id=run_id,
            system_state=system_state,
            map=self._viewport(scenario, stops),
            stops=GeoJSONFeatureCollection(features=stop_features),
            warehouse=warehouse,
            routes=MapRoutes(
                baseline_delivery=GeoJSONFeatureCollection(features=delivery_features),
                baseline_return=GeoJSONFeatureCollection(features=return_features),
                optimized=GeoJSONFeatureCollection(
                    features=self._optimized_features(optimized_route, scenario)
                ),
            ),
            events=self._event_features(events, stops),
            metrics=metrics,
            performance=MapPerformance(
                optimization_latency_ms=optimization_latency_ms,
                reoptimization_latency_ms=reoptimization_latency_ms,
            ),
            intelligence=intelligence,
        )

    @staticmethod
    def _stop_feature(
        stop: StopRead,
        prediction: dict[str, Any] | None,
    ) -> GeoJSONFeature:
        prediction = prediction or {}
        return GeoJSONFeature(
            geometry={"type": "Point", "coordinates": [stop.lng, stop.lat]},
            properties={
                "database_id": str(stop.id),
                "stop_id": stop.external_id,
                "type": MapDataService._value(stop.type),
                "address": stop.address,
                "weight_kg": stop.weight_kg,
                "volume_l": stop.volume_l,
                "status": MapDataService._value(stop.status),
                "return_probability": prediction.get("return_probability"),
                "risk": prediction.get("risk"),
                "recommended_action": prediction.get("recommended_action"),
                "expected_return_weight_kg": prediction.get(
                    "expected_return_weight_kg"
                ),
                "reason": prediction.get("reason"),
            },
        )

    def _route_feature(
        self,
        route: Sequence[Any],
        scenario: ScenarioRead,
        *,
        optimized: bool,
    ) -> GeoJSONFeature | None:
        if not route:
            return None
        operational = [
            item
            for item in route
            if self._value(getattr(item, "action", ""))
            not in {RouteAction.DEPOT_START.value, RouteAction.DEPOT_END.value}
        ]
        if not operational:
            return None
        coordinates = [[float(item.lng), float(item.lat)] for item in route]
        depot = [scenario.depot_lng, scenario.depot_lat]
        if coordinates[0] != depot:
            coordinates.insert(0, depot)
        if coordinates[-1] != depot:
            coordinates.append(depot)
        route_kind = "DELIVERY"
        if self._value(getattr(operational[0], "type", "")) != StopType.DELIVERY.value:
            route_kind = "RETURN"
        return GeoJSONFeature(
            geometry={"type": "LineString", "coordinates": coordinates},
            properties={
                "route_kind": "OPTIMIZED" if optimized else route_kind,
                "vehicle_sequence": int(getattr(route[0], "vehicle_sequence", 1)),
                "stop_ids": [
                    str(getattr(item, "external_id", "")) for item in operational
                ],
                "distance_km": round(
                    sum(
                        float(getattr(item, "distance_from_previous_km", 0))
                        for item in route
                    ),
                    3,
                ),
                "geometry_kind": "STRAIGHT_LINE_STOP_SEQUENCE",
            },
        )

    def _optimized_features(
        self,
        route: Sequence[Any],
        scenario: ScenarioRead,
    ) -> list[GeoJSONFeature]:
        grouped: dict[int, list[Any]] = {}
        for item in route:
            grouped.setdefault(int(getattr(item, "vehicle_sequence", 1)), []).append(item)
        features: list[GeoJSONFeature] = []
        for vehicle_sequence in sorted(grouped):
            ordered = sorted(
                grouped[vehicle_sequence],
                key=lambda item: int(getattr(item, "sequence_number", 0)),
            )
            feature = self._route_feature(ordered, scenario, optimized=True)
            if feature is not None:
                features.append(feature)
        return features

    @staticmethod
    def _event_features(
        events: Sequence[Any],
        stops: Sequence[StopRead],
    ) -> GeoJSONFeatureCollection:
        stops_by_id = {str(stop.id): stop for stop in stops}
        features: list[GeoJSONFeature] = []
        for event in events:
            stop_id = getattr(event, "stop_id", None)
            stop = stops_by_id.get(str(stop_id)) if stop_id else None
            if stop is None:
                continue
            features.append(
                GeoJSONFeature(
                    geometry={"type": "Point", "coordinates": [stop.lng, stop.lat]},
                    properties={
                        "event_id": str(getattr(event, "id", "")),
                        "event_type": MapDataService._value(
                            getattr(event, "event_type", "")
                        ),
                        "stop_id": stop.external_id,
                        "created_at": str(getattr(event, "created_at", "")),
                    },
                )
            )
        return GeoJSONFeatureCollection(features=features)

    @staticmethod
    def _viewport(
        scenario: ScenarioRead,
        stops: Sequence[StopRead],
    ) -> MapViewport:
        latitudes = [scenario.depot_lat, *(stop.lat for stop in stops)]
        longitudes = [scenario.depot_lng, *(stop.lng for stop in stops)]
        south, north = min(latitudes), max(latitudes)
        west, east = min(longitudes), max(longitudes)
        lat_padding = max((north - south) * 0.08, 0.002)
        lng_padding = max((east - west) * 0.08, 0.002)
        return MapViewport(
            center=MapCenter(lat=(south + north) / 2, lng=(west + east) / 2),
            bounds=MapBounds(
                south=south - lat_padding,
                west=west - lng_padding,
                north=north + lat_padding,
                east=east + lng_padding,
            ),
        )

    @staticmethod
    def _value(value: Any) -> str:
        return str(getattr(value, "value", value))
