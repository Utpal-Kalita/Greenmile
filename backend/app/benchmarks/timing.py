from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from time import perf_counter

STAGES = (
    "request_parsing_ms",
    "database_access_ms",
    "validation_ms",
    "clustering_ms",
    "distance_calculation_ms",
    "route_construction_ms",
    "local_optimization_ms",
    "constraint_validation_ms",
    "metrics_ms",
    "persistence_ms",
    "serialization_ms",
    "deterministic_total_ms",
)


@dataclass
class StageTimer:
    timings: dict[str, float] = field(default_factory=lambda: dict.fromkeys(STAGES, 0.0))

    @contextmanager
    def measure(self, stage: str) -> Iterator[None]:
        if stage not in self.timings:
            raise KeyError(f"Unknown benchmark stage: {stage}")
        started = perf_counter()
        try:
            yield
        finally:
            self.timings[stage] = round(self.timings[stage] + (perf_counter() - started) * 1_000, 3)
