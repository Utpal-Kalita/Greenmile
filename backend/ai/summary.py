"""
Gemini AI — Natural Language Route Summary.

Generates a 3-sentence briefing for fleet managers.
Falls back to a templated summary if GEMINI_API_KEY is not set.
"""
import os
import logging

logger = logging.getLogger(__name__)

# ─── Try to initialise Gemini ─────────────────────────────────────────────────
_gemini_model = None

def _load_model():
    global _gemini_model
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        _gemini_model = genai.GenerativeModel("gemini-2.0-flash")
        logger.info("Gemini model loaded for NL summary.")
    except Exception as e:
        logger.warning(f"Gemini init failed: {e}")
    return _gemini_model

_load_model()

SUMMARY_SYSTEM_PROMPT = """You are a dispatcher assistant for an Indian last-mile delivery fleet.
Write a 3-sentence route briefing for the fleet manager.
Be direct and practical. Include one flagged anomaly if any exist.
Do NOT use markdown, bullet points, or headers — plain text only.
"""

# ─── Fallback template ────────────────────────────────────────────────────────
def _template_summary(route_data: dict) -> str:
    zone = route_data.get("zone_id", "B")
    count = route_data.get("stop_count", 0)
    dist = route_data.get("optimized_distance_km", 0)
    eta = route_data.get("estimated_completion_time", "2:45 PM")
    flagged = route_data.get("flagged_stops", [])
    del_count = route_data.get("delivery_count", 0)
    ret_count = route_data.get("return_count", 0)

    s1 = f"Your Zone {zone} loop covers {count} stops ({del_count} deliveries + {ret_count} returns) across {dist} km."
    s2 = f"Load returns to the rear bay first, then stack deliveries front-to-back for fastest drop-off — estimated completion by {eta}."
    if flagged:
        top = flagged[0]
        s3 = f"Flag: Stop {top['stop_id']} at {top['address']} has {top['return_count_30d']} returns this month — action: {top['suggested_action']} before dispatch."
    else:
        s3 = "No anomalies detected — all stops are cleared for immediate dispatch."
    return f"{s1} {s2} {s3}"


# ─── Public API ───────────────────────────────────────────────────────────────
async def generate_summary(route_data: dict) -> str:
    """Generate a 3-sentence NL route briefing."""
    model = _gemini_model

    if model is None:
        return _template_summary(route_data)

    try:
        import json
        prompt = SUMMARY_SYSTEM_PROMPT + "\n\nRoute data:\n" + json.dumps(route_data)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.warning(f"Gemini summary call failed ({e}), using template.")
        return _template_summary(route_data)
