"""Interface for the automotive engine-knock model."""

from dataclasses import dataclass
from pathlib import Path

from app.model import ModelNotReadyError


KNOCK_MODEL_NAME = "cxlrd/revix-AST-engine-knock"


@dataclass(frozen=True)
class KnockModelResult:
    knock_probability: float
    model_name: str


def analyze_knock(audio_path: Path) -> KnockModelResult:
    """Analyze a WAV file; inference is implemented by Session A."""
    raise ModelNotReadyError("Knock model inference is not configured yet.")
