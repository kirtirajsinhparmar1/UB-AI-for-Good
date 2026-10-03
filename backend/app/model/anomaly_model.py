"""Optional interface for a general acoustic anomaly model."""

from dataclasses import dataclass
from pathlib import Path

from app.model import ModelNotReadyError


@dataclass(frozen=True)
class AnomalyModelResult:
    general_anomaly_score: float
    model_name: str


def analyze_anomaly(audio_path: Path) -> AnomalyModelResult:
    """Analyze a WAV file; optional inference is implemented by Session B."""
    raise ModelNotReadyError("Anomaly model inference is not configured yet.")
