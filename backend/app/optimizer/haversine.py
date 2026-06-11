"""
Haversine distance between two (lat, lng) coordinate pairs — returns km.
"""
import math


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return great-circle distance in kilometres between two lat/lng points."""
    R = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def build_distance_matrix(stops: list) -> list[list[float]]:
    """Build an N×N distance matrix for a list of stops (dicts with lat/lng)."""
    n = len(stops)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine(stops[i]["lat"], stops[i]["lng"], stops[j]["lat"], stops[j]["lng"])
            matrix[i][j] = d
            matrix[j][i] = d
    return matrix
