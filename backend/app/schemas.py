"""Stable request-independent API result contracts."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


RiskBand = Literal["low", "medium", "high"]


class ModelSignals(BaseModel):
    knock_model: Optional[str] = None
    anomaly_model: Optional[str] = None


class VehicleAnalysisResult(BaseModel):
    vehicle_id: str = Field(..., min_length=1)
    filename: str
    knock_probability: Optional[float] = Field(..., ge=0.0, le=1.0)
    general_anomaly_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    acoustic_risk_score: int = Field(..., ge=0, le=100)
    risk_band: RiskBand
    model_signals: ModelSignals
    warnings: List[str] = Field(default_factory=list)


class RiskRankingEntry(BaseModel):
    vehicle_id: str
    acoustic_risk_score: int = Field(..., ge=0, le=100)
    rank: int = Field(..., ge=1)


class ComparisonResponse(BaseModel):
    results: List[VehicleAnalysisResult]
    ranking: List[RiskRankingEntry]
    lowest_acoustic_risk_vehicle: Optional[str] = None

    @classmethod
    def from_results(cls, results: List[VehicleAnalysisResult]) -> "ComparisonResponse":
        ordered = sorted(results, key=lambda result: result.acoustic_risk_score)
        ranking = [
            RiskRankingEntry(
                vehicle_id=result.vehicle_id,
                acoustic_risk_score=result.acoustic_risk_score,
                rank=index,
            )
            for index, result in enumerate(ordered, start=1)
        ]
        return cls(
            results=results,
            ranking=ranking,
            lowest_acoustic_risk_vehicle=ranking[0].vehicle_id if ranking else None,
        )
