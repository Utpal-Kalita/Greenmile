from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence

from app.optimizer.engine import RoutePlan, StopLike


def validate_benchmark_route(plan: RoutePlan, required_stops: Sequence[StopLike]) -> dict[str, object]:
    """Fail closed when a measured route is incomplete or numerically invalid."""
    expected = Counter(stop.external_id for stop in required_stops)
    actual = Counter(item.external_id for item in plan.stops if item.stop is not None)
    violations: list[str] = []
    if expected != actual:
        missing = sorted((expected - actual).elements())
        duplicate_or_foreign = sorted((actual - expected).elements())
        if missing:
            violations.append(f"missing stops: {', '.join(missing[:10])}")
        if duplicate_or_foreign:
            violations.append(f"duplicate or foreign stops: {', '.join(duplicate_or_foreign[:10])}")
    for route in plan.routes:
        if not route or route[0].external_id != "DEPOT" or route[-1].external_id != "DEPOT":
            violations.append("route does not start and end at depot")
            break
    numeric_values = [plan.total_distance_km]
    numeric_values.extend(item.distance_from_previous_km for item in plan.stops)
    if not all(math.isfinite(value) and value >= 0 for value in numeric_values):
        violations.append("route contains invalid numeric values")
    violations.extend(f"{item.type}: {item.message}" for item in plan.constraints.violations)
    return {
        "valid": not violations,
        "required_stop_count": len(required_stops),
        "routed_stop_count": sum(actual.values()),
        "constraint_violations": len(plan.constraints.violations),
        "violations": violations,
    }
