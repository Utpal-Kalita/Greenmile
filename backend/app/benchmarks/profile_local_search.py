from __future__ import annotations

import argparse
import cProfile
import io
import json
import pstats
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any

from app.benchmarks.datasets import REQUIRED_WORKLOADS, generate_scenario
from app.core.config import Settings
from app.optimizer.engine import HaversineProvider, Location, RouteOptimizer, StopLike

BASELINE_VERSION = "baseline-v1"


@dataclass
class PhaseCounters:
    distance_calls: int = 0


@dataclass
class SegmentProfile:
    vehicle_sequence: int
    segment_type: str
    stop_count: int
    worst_case_candidates_per_iteration: int
    distance_calls: int
    estimated_candidates_evaluated: int
    wall_ms: float
    distance_before_km: float
    distance_after_km: float
    improvement_km: float


@dataclass
class LocalSearchProfile:
    algorithm: str
    dataset: str
    dataset_version: str
    stop_count: int
    vehicle_count: int
    two_opt_max_iterations: int
    segment_profiles: list[SegmentProfile]
    totals: dict[str, float | int]
    cprofile_top: list[dict[str, Any]] = field(default_factory=list)


class CountingProvider:
    name = "HAVERSINE"

    def __init__(self) -> None:
        self.provider = HaversineProvider()
        self.phase = "unscoped"
        self.counters: dict[str, PhaseCounters] = {}

    @contextmanager
    def scoped(self, phase: str) -> Iterator[None]:
        previous = self.phase
        self.phase = phase
        self.counters.setdefault(phase, PhaseCounters())
        try:
            yield
        finally:
            self.phase = previous

    def distance(self, first: Location | StopLike, second: Location | StopLike) -> float:
        self.counters.setdefault(self.phase, PhaseCounters()).distance_calls += 1
        return self.provider.distance(first, second)

    def distance_calls(self, phase: str) -> int:
        return self.counters.get(phase, PhaseCounters()).distance_calls


def profile_local_search(stop_count: int, *, seed: int = 20_260_823, cprofile_limit: int = 12) -> LocalSearchProfile:
    scenario = generate_scenario(stop_count, seed=seed)
    provider = CountingProvider()
    optimizer = RouteOptimizer(provider, Settings())
    labels = optimizer._clusters(scenario.stops)
    clustered = sorted(zip(scenario.stops, labels, strict=True), key=lambda value: (value[1], value[0].external_id))
    groups = optimizer._partition([item[0] for item in clustered], len(scenario.vehicles))

    segments: list[SegmentProfile] = []
    profiler = cProfile.Profile()
    profiler.enable()
    for vehicle_sequence, group in enumerate(groups, start=1):
        deliveries = [stop for stop in group if stop.type.value == "DELIVERY"]
        returns = [stop for stop in group if stop.type.value != "DELIVERY"]
        for segment_type, stops, origin in (
            ("DELIVERY", deliveries, scenario.depot),
            ("RETURN", returns, deliveries[-1] if deliveries else scenario.depot),
        ):
            route = _nearest_neighbour(optimizer, stops, origin)
            phase = f"vehicle_{vehicle_sequence}_{segment_type.lower()}"
            calls_before = provider.distance_calls(phase)
            distance_before = optimizer._sequence_distance(route, origin)
            started = perf_counter()
            with provider.scoped(phase):
                improved = optimizer._two_opt(route, origin)
            wall_ms = (perf_counter() - started) * 1_000
            distance_calls = provider.distance_calls(phase) - calls_before
            distance_after = optimizer._sequence_distance(improved, origin)
            segments.append(
                SegmentProfile(
                    vehicle_sequence=vehicle_sequence,
                    segment_type=segment_type,
                    stop_count=len(route),
                    worst_case_candidates_per_iteration=_worst_case_candidates_per_iteration(len(route)),
                    distance_calls=distance_calls,
                    estimated_candidates_evaluated=distance_calls // 4,
                    wall_ms=round(wall_ms, 3),
                    distance_before_km=round(distance_before, 3),
                    distance_after_km=round(distance_after, 3),
                    improvement_km=round(distance_before - distance_after, 3),
                )
            )
    profiler.disable()

    total_calls = sum(segment.distance_calls for segment in segments)
    total_candidates = sum(segment.estimated_candidates_evaluated for segment in segments)
    total_wall = round(sum(segment.wall_ms for segment in segments), 3)
    total_improvement = round(sum(segment.improvement_km for segment in segments), 3)
    return LocalSearchProfile(
        algorithm=BASELINE_VERSION,
        dataset=scenario.name,
        dataset_version=scenario.version,
        stop_count=stop_count,
        vehicle_count=len(scenario.vehicles),
        two_opt_max_iterations=optimizer.settings.two_opt_max_iterations,
        segment_profiles=segments,
        totals={
            "local_optimization_wall_ms": total_wall,
            "distance_calls": total_calls,
            "estimated_candidates_evaluated": total_candidates,
            "improvement_km": total_improvement,
            "segments": len(segments),
        },
        cprofile_top=_top_profile_entries(profiler, cprofile_limit),
    )


def write_profiles(profiles: Sequence[LocalSearchProfile], output: Path) -> tuple[Path, Path]:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "greenmile-local-search-profile-v1",
        "profiles": [_profile_to_dict(profile) for profile in profiles],
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    markdown = output.with_suffix(".md")
    lines = [
        "# Greenmile Local Search Profile",
        "",
        "> Profiling only. No optimizer changes were applied.",
        "",
        "| Stops | Segments | Local wall ms | Distance calls | Est. candidates | Improvement km |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for profile in profiles:
        totals = profile.totals
        lines.append(
            f"| {profile.stop_count:,} | {totals['segments']} | {totals['local_optimization_wall_ms']} | "
            f"{totals['distance_calls']:,} | {totals['estimated_candidates_evaluated']:,} | {totals['improvement_km']} |"
        )
    markdown.write_text("\n".join(lines) + "\n")
    return output, markdown


def _nearest_neighbour(optimizer: RouteOptimizer, stops: list[StopLike], origin: Location | StopLike) -> list[StopLike]:
    unvisited = list(stops)
    route: list[StopLike] = []
    current = origin
    while unvisited:
        nearest = min(unvisited, key=lambda stop: (optimizer.provider.distance(current, stop), stop.external_id))
        route.append(nearest)
        unvisited.remove(nearest)
        current = nearest
    return route


def _worst_case_candidates_per_iteration(stop_count: int) -> int:
    return sum(max(0, min(stop_count, left + 27) - (left + 2)) for left in range(max(0, stop_count - 2)))


def _top_profile_entries(profiler: cProfile.Profile, limit: int) -> list[dict[str, Any]]:
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream).sort_stats("cumulative")
    stats.print_stats(limit)
    entries: list[dict[str, Any]] = []
    for line in stream.getvalue().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("ncalls", "Ordered by", "function calls")) or "function calls" in stripped:
            continue
        parts = stripped.split(None, 5)
        if len(parts) == 6 and parts[0].replace("/", "").isdigit() and _is_float(parts[1]):
            entries.append(
                {
                    "ncalls": parts[0],
                    "tottime_seconds": float(parts[1]),
                    "percall_tottime_seconds": float(parts[2]),
                    "cumtime_seconds": float(parts[3]),
                    "percall_cumtime_seconds": float(parts[4]),
                    "function": parts[5],
                }
            )
    return entries[:limit]


def _is_float(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


def _profile_to_dict(profile: LocalSearchProfile) -> dict[str, Any]:
    data = asdict(profile)
    data["segment_profiles"] = [asdict(segment) for segment in profile.segment_profiles]
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile baseline-v1 local optimization without changing the optimizer")
    parser.add_argument("--sizes", default="100,500", help="Comma-separated subset of 100,500,1000,2500,5000")
    parser.add_argument("--seed", type=int, default=20_260_823)
    parser.add_argument("--output", type=Path, default=Path("benchmark-results/local-search-profile.json"))
    parser.add_argument("--cprofile-limit", type=int, default=12)
    args = parser.parse_args()
    sizes = tuple(int(value.strip()) for value in args.sizes.split(",") if value.strip())
    if any(size not in REQUIRED_WORKLOADS for size in sizes):
        raise SystemExit(f"sizes must be drawn from {REQUIRED_WORKLOADS}")
    json_path, markdown_path = write_profiles(
        [profile_local_search(size, seed=args.seed, cprofile_limit=args.cprofile_limit) for size in sizes],
        args.output,
    )
    print(f"JSON profile: {json_path}")
    print(f"Markdown profile: {markdown_path}")


if __name__ == "__main__":
    main()
