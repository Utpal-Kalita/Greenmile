from pydantic import BaseModel
from typing import List, Optional

class Stop(BaseModel):
    stop_id: str
    type: str # DELIVERY or RETURN
    lat: float
    lng: float
    weight_kg: float
    volume_l: float
    time_window_start: str
    time_window_end: str
    cluster_id: str
    return_count_30d: int
    avg_delivery_confirm_minutes: int
    dispute_history_count: int
    address: str

class OptimizationRequest(BaseModel):
    stops: List[Stop]
