from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .models import Stop, OptimizationRequest
from typing import List
import pandas as pd
import io
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import optimizer modules
from .optimizer.dbscan import cluster_stops
from .optimizer.route import build_bidirectional_loop
from .optimizer.return_predictor import predict_return_probability

# Import AI modules (relative to backend/ root since uvicorn runs from there)
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ai.anomaly import analyse_batch
from ai.summary import generate_summary

app = FastAPI(
    title="Greenmile API",
    description="Bidirectional Last-Mile Logistics Optimizer",
    version="2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health check ──────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    gemini_configured = bool(os.environ.get("GEMINI_API_KEY"))
    return {
        "message": "Welcome to Greenmile API",
        "version": "2.0",
        "status": "healthy",
        "gemini": "configured" if gemini_configured else "not configured (heuristic fallback active)",
    }


# ─── CSV Upload ────────────────────────────────────────────────────────────────

REQUIRED_COLUMNS = [
    "stop_id", "type", "lat", "lng", "weight_kg", "volume_l",
    "time_window_start", "time_window_end", "cluster_id",
    "return_count_30d", "avg_delivery_confirm_minutes",
    "dispute_history_count", "address",
]

@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {str(e)}")

    # Validate required columns
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(missing)}",
        )

    # Validate stop types
    invalid = df[~df["type"].isin(["DELIVERY", "RETURN"])]
    if not invalid.empty:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid type values found: {invalid['type'].unique().tolist()}. Must be DELIVERY or RETURN.",
        )

    # Validate lat/lng ranges
    bad_lat = df[(df["lat"] < -90) | (df["lat"] > 90)]
    bad_lng = df[(df["lng"] < -180) | (df["lng"] > 180)]
    if not bad_lat.empty or not bad_lng.empty:
        raise HTTPException(status_code=400, detail="Invalid lat/lng values detected.")

    stops = df.to_dict(orient="records")
    delivery_count = len([s for s in stops if s["type"] == "DELIVERY"])
    return_count = len([s for s in stops if s["type"] == "RETURN"])

    return {
        "status": "success",
        "message": f"CSV uploaded: {len(stops)} stops parsed ({delivery_count} deliveries, {return_count} returns)",
        "data": stops,
        "delivery_count": delivery_count,
        "return_count": return_count,
    }


# ─── Optimize ──────────────────────────────────────────────────────────────────

@app.post("/optimize")
async def optimize_route(request: OptimizationRequest):
    if not request.stops:
        raise HTTPException(status_code=400, detail="No stops provided")

    # Convert Pydantic models → plain dicts for optimizer functions
    stops = [s.dict() for s in request.stops]

    # ── Step 1: DBSCAN geographic clustering ──────────────────────────────────
    clustered = cluster_stops(stops, eps_km=3.0, min_samples=2)

    # Group stops by cluster
    clusters: dict[str, list] = {}
    for stop in clustered:
        cid = stop.get("cluster_id", "Zone_A")
        clusters.setdefault(cid, []).append(stop)

    # ── Step 2: NN + 2-opt bidirectional loop per cluster ─────────────────────
    all_optimized: list = []
    total_metrics = {
        "total_distance_km": 0.0,
        "delivery_count": 0,
        "return_count": 0,
        "total_stops": 0,
        "estimated_fuel_l": 0.0,
        "estimated_fuel_cost": 0.0,
        "estimated_co2_kg": 0.0,
    }

    for _cid, cluster_stops_list in clusters.items():
        loop, metrics = build_bidirectional_loop(cluster_stops_list)
        all_optimized.extend(loop)
        for key in total_metrics:
            total_metrics[key] = round(total_metrics[key] + metrics.get(key, 0), 4)

    # Round final totals
    total_metrics["total_distance_km"] = round(total_metrics["total_distance_km"], 2)
    total_metrics["estimated_fuel_l"] = round(total_metrics["estimated_fuel_l"], 2)
    total_metrics["estimated_fuel_cost"] = round(total_metrics["estimated_fuel_cost"], 0)
    total_metrics["estimated_co2_kg"] = round(total_metrics["estimated_co2_kg"], 2)

    # ── Step 3: Return Probability Prediction (F10) ────────────────────────────
    all_with_prob = predict_return_probability(all_optimized)

    # Count pre-staged return slots
    pre_staged_count = sum(1 for s in all_with_prob if s.get("pre_stage_return"))

    # ── Step 4: Gemini anomaly detection ──────────────────────────────────────
    annotated_route = await analyse_batch(all_with_prob)

    # ── Step 5: Gemini NL route summary ───────────────────────────────────────
    flagged_stops = [s for s in annotated_route if s.get("flag", False)]
    top_zone = list(clusters.keys())[0].replace("Zone_", "") if clusters else "B"

    route_data = {
        "zone_id": top_zone,
        "stop_count": total_metrics["total_stops"],
        "optimized_distance_km": total_metrics["total_distance_km"],
        "estimated_completion_time": "2:45 PM",
        "delivery_count": total_metrics["delivery_count"],
        "return_count": total_metrics["return_count"],
        "flagged_stops": flagged_stops[:1],
    }
    nl_summary = await generate_summary(route_data)

    return {
        "status": "success",
        "message": "Route optimized via Greenmile bidirectional loop engine",
        "route": annotated_route,
        "metrics": total_metrics,
        "nl_summary": nl_summary,
        "flagged_count": len(flagged_stops),
        "cluster_count": len(clusters),
        "pre_staged_returns": pre_staged_count,
    }
