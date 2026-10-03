"""Frontend response contract for acoustic disposition decisions."""

from pydantic import BaseModel, Field

from app.routing.channel_router import DecisionStrength, RecommendedChannel
from app.schemas import RiskBand


class DecisionAcoustic(BaseModel):
    acoustic_knock_score: int = Field(..., ge=0, le=100)
    risk_band: RiskBand
    model_name: str = Field(..., min_length=1)


class DecisionValuation(BaseModel):
    base_wholesale_value: float = Field(..., gt=0)
    acoustic_delta_pct: float = Field(
        ..., description="Fractional rate; 0.00325 represents a 0.325% adjustment."
    )
    acoustic_delta_amount: float
    adjusted_wholesale_value: float = Field(..., ge=0)
    policy_type: str = Field(..., min_length=1)
    policy_version: str = Field(..., min_length=1)
    policy_note: str = Field(..., min_length=1)


class DecisionEconomics(BaseModel):
    acv_expected_value: float = Field(..., ge=0)
    copart_expected_value: float = Field(..., ge=0)
    # Positive values mean Copart has the higher expected value; negative means ACV.
    value_difference: float


class DecisionRecommendation(BaseModel):
    recommended_channel: RecommendedChannel
    decision_strength: DecisionStrength
    minimum_switch_advantage: float = Field(..., ge=0)
    rationale: str = Field(..., min_length=1)


class DecisionResponse(BaseModel):
    vehicle_id: str = Field(..., min_length=1)
    acoustic: DecisionAcoustic
    valuation: DecisionValuation
    economics: DecisionEconomics
    decision: DecisionRecommendation
    disclaimer: str
