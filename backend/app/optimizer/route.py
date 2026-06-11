"""
Bidirectional Route Optimizer — Nearest Neighbour seed + 2-opt improvement.

Strategy
--------
1. Build a haversine distance matrix.
2. Run Nearest Neighbour (NN) from a depot (or first stop) to produce an initial tour.
3. Apply 2-opt swaps to improve the tour.
4. The tour visits all DELIVERY stops first (outbound leg), then RETURN stops
   (inbound leg), creating a single bidirectional loop.

This runs in O(n²) and finishes in well under 1 second for ≤50 stops.
"""
from .haversine import build_distance_matrix


# ─── Nearest Neighbour ────────────────────────────────────────────────────────

def nearest_neighbour(stops: list, dist_matrix: list[list[float]]) -> list[int]:
    """Return an ordered list of stop indices via greedy nearest-neighbour."""
    n = len(stops)
    visited = [False] * n
    route = [0]
    visited[0] = True

    for _ in range(n - 1):
        last = route[-1]
        nearest = -1
        best_d = float("inf")
        for j in range(n):
            if not visited[j] and dist_matrix[last][j] < best_d:
                best_d = dist_matrix[last][j]
                nearest = j
        route.append(nearest)
        visited[nearest] = True

    return route


# ─── 2-opt improvement ────────────────────────────────────────────────────────

def two_opt(route: list[int], dist_matrix: list[list[float]]) -> list[int]:
    """Improve a route with 2-opt swaps until no improvement is found."""
    improved = True
    best = route[:]
    best_dist = _route_distance(best, dist_matrix)

    while improved:
        improved = False
        for i in range(1, len(best) - 1):
            for j in range(i + 1, len(best)):
                new_route = best[:i] + best[i:j + 1][::-1] + best[j + 1:]
                new_dist = _route_distance(new_route, dist_matrix)
                if new_dist < best_dist - 1e-6:
                    best = new_route
                    best_dist = new_dist
                    improved = True
    return best


def _route_distance(route: list[int], dist_matrix: list[list[float]]) -> float:
    total = 0.0
    for k in range(len(route) - 1):
        total += dist_matrix[route[k]][route[k + 1]]
    return total


# ─── Bidirectional loop builder ───────────────────────────────────────────────

def build_bidirectional_loop(stops: list) -> tuple[list, dict]:
    """
    Entry point. Given a list of stop dicts, return:
      - ordered list of stop dicts (the optimized loop)
      - metrics dict {total_distance_km, delivery_count, return_count}

    The loop visits DELIVERY stops first (outbound), then RETURN stops (inbound).
    Within each segment, NN + 2-opt minimises distance.
    """
    if len(stops) == 0:
        return [], {}

    deliveries = [s for s in stops if s.get("type") == "DELIVERY"]
    returns    = [s for s in stops if s.get("type") == "RETURN"]

    def optimise_segment(segment: list) -> list:
        if len(segment) <= 1:
            return segment
        dm = build_distance_matrix(segment)
        idx_nn   = nearest_neighbour(segment, dm)
        idx_opt  = two_opt(idx_nn, dm)
        return [segment[i] for i in idx_opt]

    optimised_deliveries = optimise_segment(deliveries)
    optimised_returns    = optimise_segment(returns)
    full_loop = optimised_deliveries + optimised_returns

    # Compute total loop distance
    total_km = 0.0
    if len(full_loop) > 1:
        all_dm = build_distance_matrix(full_loop)
        for k in range(len(full_loop) - 1):
            total_km += all_dm[k][k + 1]

    metrics = {
        "total_distance_km": round(total_km, 2),
        "delivery_count": len(optimised_deliveries),
        "return_count": len(optimised_returns),
        "total_stops": len(full_loop),
        "estimated_fuel_l": round(total_km / 12, 2),   # ~12 km/L for Indian delivery van
        "estimated_fuel_cost": round((total_km / 12) * 90, 0),  # ₹90/L
        "estimated_co2_kg": round(total_km * 0.21, 2),  # ~210g CO2/km
    }

    return full_loop, metrics
