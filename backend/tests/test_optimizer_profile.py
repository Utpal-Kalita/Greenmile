from app.benchmarks.datasets import REQUIRED_WORKLOADS, generate_scenario
from app.benchmarks.profile_local_search import _worst_case_candidates_per_iteration, profile_local_search


def test_profile_generator_is_deterministic_for_required_workloads():
    assert REQUIRED_WORKLOADS == (100, 500, 1_000, 2_500, 5_000)
    first = generate_scenario(100, seed=42)
    second = generate_scenario(100, seed=42)

    assert first == second
    assert len(first.stops) == 100
    assert len({stop.external_id for stop in first.stops}) == 100
    assert len({stop.id for stop in first.stops}) == 100


def test_worst_case_candidate_estimate_matches_current_window():
    assert _worst_case_candidates_per_iteration(0) == 0
    assert _worst_case_candidates_per_iteration(3) == 1
    assert _worst_case_candidates_per_iteration(4) == 3


def test_local_search_profile_counts_distance_calls_and_segments():
    profile = profile_local_search(100, seed=42, cprofile_limit=5)

    assert profile.algorithm == "baseline-v1"
    assert profile.stop_count == 100
    assert profile.totals["segments"] == 2
    assert profile.totals["distance_calls"] > 0
    assert profile.totals["estimated_candidates_evaluated"] > 0
    assert profile.totals["local_optimization_wall_ms"] > 0
    assert profile.cprofile_top
    assert all(segment.stop_count > 0 for segment in profile.segment_profiles)
    assert all(segment.estimated_candidates_evaluated == segment.distance_calls // 4 for segment in profile.segment_profiles)
