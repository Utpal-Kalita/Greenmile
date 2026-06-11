"""
Gemini AI — Natural Language Route Summary.

Generates a 3-sentence briefing for fleet managers.
Uses google-genai SDK (official, lighter).
Falls back to a templated summary if GEMINI_API_KEY is not set.
"""
import os
import json

# ─── Try to initialise Gemini ─────────────────────────────────────────────────
_client = None

def _init_client():
    global _client
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("⚠ [Summary] GEMINI_API_KEY not set — will use template fallback")
        return None
    try:
        from google import genai
        _client = genai.Client(api_key=api_key)
        print(f"✅ [Summary] Gemini client initialized (key: ...{api_key[-6:]})")
        return _client
    except ImportError:
        print("⚠ [Summary] google-genai not installed — will use template fallback")
        print("  Run: pip install google-genai")
        return None
    except Exception as e:
        print(f"⚠ [Summary] Gemini init failed: {e} — will use template fallback")
        return None


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
    global _client
    if _client is None:
        _init_client()

    if _client is None:
        print("  📝 [Summary] Using template fallback")
        return _template_summary(route_data)

    try:
        print("\n📝 [Summary] Generating Gemini AI route briefing...")

        prompt = SUMMARY_SYSTEM_PROMPT + "\n\nRoute data:\n" + json.dumps(route_data)

        response = _client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )

        summary = response.text.strip()
        print(f"  🤖 [Gemini] Summary: {summary[:80]}...")
        return summary
    except Exception as e:
        print(f"  ⚠ [Gemini] Summary call failed: {e} — using template")
        return _template_summary(route_data)
