"""Convert model outputs to the MVP acoustic risk score and band."""

from dataclasses import dataclass
from typing import Optional

from app.schemas import RiskBand


@dataclass(frozen=True)
class AcousticScore:
    acoustic_risk_score: int
    risk_band: RiskBand


def risk_band_for_score(score: int) -> RiskBand:
    if not 0 <= score <= 100:
        raise ValueError("Acoustic risk score must be between 0 and 100.")
    if score <= 33:
        return "low"
    if score <= 66:
        return "medium"
    return "high"


def score_acoustic_risk(
    knock_probability: float,
    general_anomaly_score: Optional[float] = None,
) -> AcousticScore:
    if not 0.0 <= knock_probability <= 1.0:
        raise ValueError("Knock probability must be between 0.0 and 1.0.")
    if general_anomaly_score is not None and not 0.0 <= general_anomaly_score <= 1.0:
        raise ValueError("General anomaly score must be between 0.0 and 1.0.")

    score = round(knock_probability * 100)
    return AcousticScore(score, risk_band_for_score(score))
