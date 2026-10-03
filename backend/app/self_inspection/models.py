"""Response models for consumer acoustic self-inspection."""

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas import RiskBand


CaptureQualityStatus = Literal["good", "warning", "invalid"]


class CaptureAssessment(BaseModel):
    duration_seconds: float = Field(..., ge=0)
    sample_rate: int = Field(..., ge=0)
    channels: int = Field(..., ge=0)
    quality_status: CaptureQualityStatus
    quality_warnings: list[str] = Field(default_factory=list)


class AcousticAssessment(BaseModel):
    knock_probability: float = Field(..., ge=0.0, le=1.0)
    acoustic_risk_score: int = Field(..., ge=0, le=100)
    risk_band: RiskBand
    model_name: str


class SelfInspectionResult(BaseModel):
    vehicle_id: str = Field(..., min_length=1)
    filename: str
    capture: CaptureAssessment
    acoustic: AcousticAssessment
    status: Literal["ready"]
