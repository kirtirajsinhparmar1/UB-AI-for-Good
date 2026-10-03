"""Orchestrate local-model acoustic self-inspection."""

from pathlib import Path, PurePosixPath
from typing import Optional

from app.model import ModelNotReadyError
from app.model.audio_io import AudioValidationError, validate_wav
from app.model.knock_model import analyze_knock
from app.scoring.acoustic_score import score_acoustic_risk
from app.self_inspection.models import (
    AcousticAssessment,
    CaptureAssessment,
    SelfInspectionResult,
)


MIN_SAMPLE_RATE_HZ = 8_000
MIN_RECOMMENDED_DURATION_SECONDS = 2.0
LONG_CAPTURE_WARNING_SECONDS = 30.0
MAX_CAPTURE_DURATION_SECONDS = 60.0


class SelfInspectionAudioError(ValueError):
    """Raised when an audio file or its capture metadata is not usable."""


class SelfInspectionModelUnavailableError(RuntimeError):
    """Raised when local knock inference is unavailable."""


def _safe_filename(filename: Optional[str], audio_path: Path) -> str:
    candidate = filename if filename else audio_path.name
    # Upload names can use Windows separators even when the backend runs on Unix.
    return PurePosixPath(candidate.replace("\\", "/")).name or "audio.wav"


def _capture_assessment(metadata) -> CaptureAssessment:
    if metadata.duration_seconds <= 0:
        raise SelfInspectionAudioError("WAV audio must have a non-zero duration.")
    if metadata.sample_rate < MIN_SAMPLE_RATE_HZ:
        raise SelfInspectionAudioError(
            f"WAV sample rate must be at least {MIN_SAMPLE_RATE_HZ} Hz."
        )
    if metadata.duration_seconds > MAX_CAPTURE_DURATION_SECONDS:
        raise SelfInspectionAudioError(
            f"WAV duration must not exceed {MAX_CAPTURE_DURATION_SECONDS:g} seconds."
        )

    warnings = []
    if metadata.duration_seconds < MIN_RECOMMENDED_DURATION_SECONDS:
        warnings.append(
            "Recording is shorter than the recommended 2 seconds; "
            "record a longer clip for a more useful acoustic knock risk assessment."
        )
    if metadata.duration_seconds > LONG_CAPTURE_WARNING_SECONDS:
        warnings.append(
            "Recording is longer than 30 seconds; a shorter engine recording is recommended."
        )

    return CaptureAssessment(
        duration_seconds=metadata.duration_seconds,
        sample_rate=metadata.sample_rate,
        channels=metadata.channels,
        quality_status="warning" if warnings else "good",
        quality_warnings=warnings,
    )


def analyze_self_inspection(
    vehicle_id: str,
    audio_path: Path,
    *,
    filename: Optional[str] = None,
) -> SelfInspectionResult:
    """Validate a WAV capture and assess acoustic knock risk with the local model."""
    normalized_vehicle_id = vehicle_id.strip()
    if not normalized_vehicle_id:
        raise ValueError("vehicle_id must not be empty.")

    try:
        metadata = validate_wav(str(audio_path))
    except AudioValidationError as error:
        raise SelfInspectionAudioError(str(error)) from error

    capture = _capture_assessment(metadata)
    try:
        knock = analyze_knock(audio_path)
    except ModelNotReadyError as error:
        raise SelfInspectionModelUnavailableError(
            str(error) or "Knock inference model is unavailable."
        ) from error

    score = score_acoustic_risk(knock.knock_probability)
    return SelfInspectionResult(
        vehicle_id=normalized_vehicle_id,
        filename=_safe_filename(filename, audio_path),
        capture=capture,
        acoustic=AcousticAssessment(
            knock_probability=knock.knock_probability,
            acoustic_risk_score=score.acoustic_risk_score,
            risk_band=score.risk_band,
            model_name=knock.model_name,
        ),
        status="ready",
    )
