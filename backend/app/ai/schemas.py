from typing import Literal

from pydantic import BaseModel, Field


class ReturnInsight(BaseModel):
    stop_id: str
    return_probability: float = Field(ge=0, le=1)
    risk: Literal["LOW", "MEDIUM", "HIGH"]
    expected_return_weight_kg: float = Field(ge=0)
    reason: str = Field(max_length=240)
    recommended_action: Literal["PROCEED", "VERIFY", "RESERVE_CAPACITY", "CONTACT_CUSTOMER"]


class Recommendation(BaseModel):
    priority: Literal["LOW", "MEDIUM", "HIGH"]
    action: str = Field(max_length=120)
    reason: str = Field(max_length=240)


class RouteIntelligence(BaseModel):
    summary: str = Field(max_length=600)
    return_insights: list[ReturnInsight] = Field(max_length=12)
    recommendations: list[Recommendation] = Field(max_length=8)
