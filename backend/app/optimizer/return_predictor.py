"""
Return Probability Predictor — F10 (Stretch Goal).

A lightweight heuristic that scores each DELIVERY stop with a
return_probability (0.0–1.0) based on observable stop metadata.
No ML training required — ships in hours, not days.

Heuristic factors:
  - return_count_30d        : direct historical signal at this address
  - dispute_history_count   : strong fraud / dissatisfied customer signal
  - avg_delivery_confirm_minutes : slow confirmations → more likely to return
  - cluster_return_rate     : zone-level return frequency (contextual)
  - weight_kg               : heavier items slightly more return-prone

If return_probability > 0.50:  pre_stage_return = True
    → pre-insert a tentative return bay slot in the packing sequencer
    → fleet manager confirms or cancels before dispatch
"""


def predict_return_probability(stops: list) -> list:
    """
    Annotate each DELIVERY stop with return_probability and pre_stage_return.
    RETURN stops are passed through unchanged (return_probability = None).

    Parameters
    ----------
    stops : list of stop dicts (output of build_bidirectional_loop or cluster_stops)

    Returns
    -------
    Same list with two extra fields on DELIVERY stops:
        return_probability : float 0.0–1.0
        pre_stage_return   : bool
    """
    total = max(len(stops), 1)
    return_count = sum(1 for s in stops if s.get("type") == "RETURN")
    cluster_return_rate = return_count / total  # 0–1 contextual zone signal

    result = []
    for stop in stops:
        if stop.get("type") != "DELIVERY":
            # Return stops — pass through, not scored
            result.append({**stop, "return_probability": None, "pre_stage_return": False})
            continue

        score = 0.0

        # Direct historical signal: past returns at this address
        score += min(stop.get("return_count_30d", 0) * 0.10, 0.30)

        # Dispute history — very strong predictor
        score += min(stop.get("dispute_history_count", 0) * 0.25, 0.50)

        # Slow delivery confirmation (minutes) → reluctant recipient = likely return
        score += min(stop.get("avg_delivery_confirm_minutes", 0) / 60.0, 0.15)

        # Zone-level context: high-return zone raises individual probability
        score += cluster_return_rate * 0.20

        # Weight proxy: heavier packages slightly more return-prone
        score += min(stop.get("weight_kg", 0) / 50.0, 0.05)

        score = round(min(score, 1.0), 2)
        pre_stage = score > 0.50

        result.append({**stop, "return_probability": score, "pre_stage_return": pre_stage})

    return result
