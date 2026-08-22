# Greenmile Optimization

## Baseline

The baseline is computed from the selected scenario, not a constant. For each vehicle it creates a closed depot route for delivery work and another closed depot route for returns/pickups. Their combined distance and operating time represent the conventional two-trip approach.

## Greenmile route

The deterministic v1 pipeline is:

1. Cluster latitude/longitude coordinates with DBSCAN and Haversine distance.
2. Partition work deterministically across configured vehicles.
3. Visit delivery stops before return/pickup stops.
4. Build each segment with nearest neighbour.
5. Improve it with bounded 2-opt edge-delta evaluation.
6. Close every route at the depot.
7. Validate capacity, time windows, precedence, depot closure, and driver hours.
8. Calculate distance, fuel, fuel cost, CO₂, driver time, labor cost, and total savings.
9. Persist the route, metrics, constraints, provider identity, and stage timings.

The engine is isolated behind `RouteOptimizer` and `RoutingProvider` interfaces. Haversine can later be replaced by OSRM without changing API or persistence layers.

## Reproducibility

- Algorithm version: `greenmile-haversine-v1`
- Demo seed: `20260822`
- Default DBSCAN radius: 3 km
- Default bounded 2-opt iterations: 60
- Logistics/economic assumptions are environment-configurable

## Incremental updates

A trip event is stored before reoptimization. Failed or cancelled stops are removed from the remaining problem and the affected route state is rebuilt, validated, measured, and persisted. `REOPTIMIZING` and `ROUTE_UPDATED` events expose the transition.

## Known limitation

Haversine is straight-line distance. Results disclose the provider and must not be presented as road-network distance. A future road provider can implement the existing interface.
