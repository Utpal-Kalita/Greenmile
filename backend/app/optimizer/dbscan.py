"""
DBSCAN geographic clustering.
Groups stop lat/lng points into spatial clusters using scikit-learn DBSCAN
with haversine metric (earth-radius-normalised radians).
"""
import math
import numpy as np
from sklearn.cluster import DBSCAN


def cluster_stops(stops: list, eps_km: float = 3.0, min_samples: int = 2) -> list:
    """
    Assign a cluster_id to each stop using DBSCAN.

    Parameters
    ----------
    stops       : list of dicts with 'lat', 'lng', 'stop_id' keys
    eps_km      : neighbourhood radius in km  (default 3 km)
    min_samples : minimum points to form a cluster (default 2)

    Returns
    -------
    stops list with 'cluster_id' field updated (Zone_A, Zone_B, … or Outlier_N)
    """
    if len(stops) == 0:
        return stops

    # Convert km radius → radians for haversine metric
    eps_rad = eps_km / 6371.0

    coords = np.array([[math.radians(s["lat"]), math.radians(s["lng"])] for s in stops])

    db = DBSCAN(eps=eps_rad, min_samples=min_samples, algorithm="ball_tree", metric="haversine")
    labels = db.fit_predict(coords)

    zone_letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    result = []
    outlier_idx = 0
    for stop, label in zip(stops, labels):
        s = dict(stop)
        if label == -1:
            s["cluster_id"] = f"Outlier_{outlier_idx}"
            outlier_idx += 1
        else:
            s["cluster_id"] = f"Zone_{zone_letters[label % 26]}"
        result.append(s)
    return result
