"""
Gemini AI — Return Anomaly & Fraud Detector.

Sends structured stop metadata to gemini-2.0-flash and gets back:
  { risk_score: 0.0–1.0, flag: bool, reason: str, suggested_action: HOLD|VERIFY|PROCEED }

Uses google-genai SDK (official, lighter).
Falls back to heuristic scoring if GEMINI_API_KEY is not set or call fails.
"""
import os
import json

# ─── Try to initialise Gemini ─────────────────────────────────────────────────
_client = None

def _init_client():
    global _client
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("⚠ [Anomaly] GEMINI_API_KEY not set — will use heuristic fallback")
        return None
    try:
        from google import genai
        _client = genai.Client(api_key=api_key)
        print(f"✅ [Anomaly] Gemini client initialized (key: ...{api_key[-6:]})")
        return _client
    except ImportError:
        print("⚠ [Anomaly] google-genai not installed — will use heuristic fallback")
        print("  Run: pip install google-genai")
        return None
    except Exception as e:
        print(f"⚠ [Anomaly] Gemini init failed: {e} — will use heuristic fallback")
        return None


# ─── Prompt ───────────────────────────────────────────────────────────────────
ANOMALY_SYSTEM_PROMPT = """You are a logistics fraud analyst for Indian last-mile delivery.
Analyse stop return data and respond ONLY with valid JSON, no preamble, no markdown.

Input fields:
  stop_id, address, return_count_30d, avg_delivery_confirm_minutes,
  dispute_history_count, cluster_return_rate

Expected output schema:
{
  "risk_score": <float 0.0-1.0>,
  "flag": <boolean>,
  "reason": "<one sentence plain-English explanation>",
  "suggested_action": "<HOLD | VERIFY | PROCEED>"
}

Scoring guide:
- return_count_30d >= 3  → strong signal, +0.3
- dispute_history_count >= 1 → strong signal, +0.25
- avg_delivery_confirm_minutes >= 15 → moderate signal, +0.15
- HOLD   if risk_score > 0.75
- VERIFY if risk_score 0.50–0.75
- PROCEED if risk_score < 0.50
"""

# ─── Heuristic fallback ───────────────────────────────────────────────────────
def _heuristic(stop_data: dict) -> dict:
    score = 0.0
    score += min(stop_data.get("return_count_30d", 0) * 0.12, 0.36)
    score += min(stop_data.get("dispute_history_count", 0) * 0.25, 0.50)
    score += 0.15 if stop_data.get("avg_delivery_confirm_minutes", 0) >= 15 else 0.0
    score = min(round(score, 2), 1.0)

    if score > 0.75:
        action, flag = "HOLD", True
        reason = f"{stop_data.get('return_count_30d',0)} returns in 30 days with dispute history – high fraud risk."
    elif score > 0.50:
        action, flag = "VERIFY", True
        reason = f"Elevated return frequency or delivery delays detected at this address."
    else:
        action, flag = "PROCEED", False
        reason = "Normal delivery and return pattern."

    return {"risk_score": score, "flag": flag, "reason": reason, "suggested_action": action}


# ─── Public API ───────────────────────────────────────────────────────────────
async def analyse_anomaly(stop_data: dict) -> dict:
    """Analyse a single stop for return anomaly / fraud risk."""
    global _client
    if _client is None:
        _init_client()

    if _client is None:
        return _heuristic(stop_data)

    try:
        from google import genai

        prompt = ANOMALY_SYSTEM_PROMPT + "\n\nStop data:\n" + json.dumps(stop_data)

        response = _client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
                max_output_tokens=256,
            ),
        )

        result = json.loads(response.text)
        # Ensure all required keys exist
        result.setdefault("risk_score", 0.0)
        result.setdefault("flag", False)
        result.setdefault("reason", "")
        result.setdefault("suggested_action", "PROCEED")

        print(f"  🤖 [Gemini] {stop_data.get('stop_id')}: risk={result['risk_score']} action={result['suggested_action']}")
        return result
    except Exception as e:
        print(f"  ⚠ [Gemini] Call failed for {stop_data.get('stop_id')}: {e} — using heuristic")
        return _heuristic(stop_data)


async def analyse_batch(stops: list) -> list:
    """Run anomaly analysis on a list of return stops, return annotated list."""
    results = []
    cluster_return_rate = len([s for s in stops if s.get("type") == "RETURN"]) / max(len(stops), 1)

    return_stops = [s for s in stops if s.get("type") == "RETURN"]
    if return_stops:
        print(f"\n🔍 [Anomaly] Analysing {len(return_stops)} return stops...")

    for stop in stops:
        if stop.get("type") != "RETURN":
            results.append({**stop, "risk_score": 0.0, "flag": False,
                            "reason": "Delivery stop", "suggested_action": "PROCEED"})
            continue

        payload = {
            "stop_id": stop.get("stop_id"),
            "address": stop.get("address"),
            "return_count_30d": stop.get("return_count_30d", 0),
            "avg_delivery_confirm_minutes": stop.get("avg_delivery_confirm_minutes", 0),
            "dispute_history_count": stop.get("dispute_history_count", 0),
            "cluster_return_rate": round(cluster_return_rate, 3),
        }
        analysis = await analyse_anomaly(payload)
        results.append({**stop, **analysis})

    return results
