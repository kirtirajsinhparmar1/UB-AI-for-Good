"""FastAPI application and upload orchestration."""

from pathlib import Path
import os
import math
from tempfile import NamedTemporaryFile
from typing import List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.api.self_inspection_router import router as self_inspection_router
from app.decision.models import DecisionResponse
from app.decision.service import analyze_decision
from app.model import ModelNotReadyError
from app.model.anomaly_model import analyze_anomaly
from app.model.audio_io import AudioValidationError, validate_wav
from app.model.knock_model import analyze_knock
from app.schemas import ComparisonResponse, ModelSignals, VehicleAnalysisResult
from app.scoring.acoustic_score import score_acoustic_risk


MAX_UPLOAD_BYTES = int(os.getenv("ACOUSTIC_MAX_UPLOAD_BYTES", 10 * 1024 * 1024))
MAX_COMPARE_FILES = 5
DEFAULT_CORS_ORIGINS = ("http://localhost:3000", "http://localhost:5173")


def _cors_origins() -> List[str]:
    configured_origins = os.getenv("ACOUSTIC_CORS_ORIGINS")
    if configured_origins is None:
        return list(DEFAULT_CORS_ORIGINS)
    return [origin.strip() for origin in configured_origins.split(",") if origin.strip()]


app = FastAPI(title="Acoustic Intelligence")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(self_inspection_router)


@app.get("/health", description="Lightweight service check; does not load or run models.")
def health() -> dict:
    return {"status": "ok", "service": "acoustic-intelligence"}


def _invalid_audio(message: str) -> HTTPException:
    return HTTPException(
        status_code=400,
        detail={"code": "invalid_audio", "message": message},
    )


def _save_upload(upload: UploadFile) -> Path:
    filename = upload.filename
    if not filename:
        raise _invalid_audio("An audio filename is required.")
    if Path(filename).suffix.lower() != ".wav":
        raise _invalid_audio("Only .wav files are supported.")

    temporary_file = NamedTemporaryFile(suffix=".wav", delete=False)
    audio_path = Path(temporary_file.name)
    try:
        with temporary_file:
            size = 0
            while True:
                chunk = upload.file.read(64 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail={
                            "code": "audio_too_large",
                            "message": f"Audio uploads must be no larger than {MAX_UPLOAD_BYTES} bytes.",
                        },
                    )
                temporary_file.write(chunk)
        return audio_path
    except Exception:
        audio_path.unlink(missing_ok=True)
        raise


def _analyze_upload(upload: UploadFile, vehicle_id: str) -> VehicleAnalysisResult:
    filename = upload.filename
    if not filename:
        raise _invalid_audio("An audio filename is required.")

    audio_path = _save_upload(upload)
    try:
        try:
            validate_wav(str(audio_path))
        except AudioValidationError as error:
            raise _invalid_audio(str(error)) from error

        try:
            knock = analyze_knock(audio_path)
        except ModelNotReadyError as error:
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "model_not_ready",
                    "component": "knock_model",
                    "message": str(error) or "Knock inference model is unavailable.",
                },
            ) from error
        except Exception as error:
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "knock_inference_failed",
                    "component": "knock_model",
                    "message": "Knock inference failed.",
                },
            ) from error

        anomaly = None
        warnings: List[str] = []
        try:
            anomaly = analyze_anomaly(audio_path)
        except ModelNotReadyError:
            warnings.append("Anomaly model is unavailable; the anomaly score was omitted.")
        except Exception:
            warnings.append("Anomaly inference failed; the anomaly score was omitted.")

        anomaly_score = anomaly.general_anomaly_score if anomaly else None
        try:
            score = score_acoustic_risk(knock.knock_probability, anomaly_score)
        except (TypeError, ValueError) as error:
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "invalid_model_output",
                    "component": "knock_model",
                    "message": "The model returned an invalid score.",
                },
            ) from error

        return VehicleAnalysisResult(
            vehicle_id=vehicle_id,
            filename=filename,
            knock_probability=knock.knock_probability,
            general_anomaly_score=anomaly_score,
            acoustic_risk_score=score.acoustic_risk_score,
            risk_band=score.risk_band,
            model_signals=ModelSignals(
                knock_model=knock.model_name,
                anomaly_model=anomaly.model_name if anomaly else None,
            ),
            warnings=warnings,
        )
    finally:
        audio_path.unlink(missing_ok=True)


def _validated_vehicle_id(vehicle_id: str) -> str:
    normalized = vehicle_id.strip()
    if not normalized:
        raise HTTPException(
            status_code=400,
            detail={"code": "invalid_vehicle_id", "message": "vehicle_id must not be empty."},
        )
    return normalized


def _validated_decision_value(value: float, field: str, *, allow_zero: bool) -> float:
    valid = math.isfinite(value) and (value >= 0 if allow_zero else value > 0)
    if not valid:
        code = {
            "base_wholesale_value": "invalid_base_wholesale_value",
            "copart_expected_gross": "invalid_copart_expected_gross",
            "minimum_switch_advantage": "invalid_minimum_switch_advantage",
        }[field]
        qualifier = "nonnegative" if allow_zero else "greater than zero"
        raise HTTPException(
            status_code=400,
            detail={"code": code, "message": f"{field} must be a finite value {qualifier}."},
        )
    return value


@app.post(
    "/v1/decision/analyze",
    response_model=DecisionResponse,
    summary="Analyze engine audio and recommend a disposition channel",
    description=(
        "Upload a WAV file and caller-supplied value estimates. The local knock model, "
        "prototype Acoustic Value Delta policy, and ACV/Copart router produce one decision."
    ),
    responses={
        400: {"description": "Vehicle, audio, or economic inputs are invalid."},
        413: {"description": "The WAV file exceeds the upload size limit."},
        422: {"description": "A required multipart field is missing or malformed."},
        503: {"description": "Required local knock inference is not ready."},
    },
)
def decision_analyze(
    vehicle_id: str = Form(...),
    audio_file: UploadFile = File(...),
    base_wholesale_value: float = Form(...),
    copart_expected_gross: float = Form(...),
    minimum_switch_advantage: float = Form(500),
) -> DecisionResponse:
    normalized_vehicle_id = _validated_vehicle_id(vehicle_id)
    base_wholesale_value = _validated_decision_value(
        base_wholesale_value, "base_wholesale_value", allow_zero=False
    )
    copart_expected_gross = _validated_decision_value(
        copart_expected_gross, "copart_expected_gross", allow_zero=True
    )
    minimum_switch_advantage = _validated_decision_value(
        minimum_switch_advantage, "minimum_switch_advantage", allow_zero=True
    )

    audio_path = _save_upload(audio_file)
    try:
        try:
            validate_wav(str(audio_path))
        except AudioValidationError as error:
            raise _invalid_audio(str(error)) from error

        try:
            return analyze_decision(
                audio_path=audio_path,
                vehicle_id=normalized_vehicle_id,
                base_wholesale_value=base_wholesale_value,
                copart_expected_gross=copart_expected_gross,
                minimum_switch_advantage=minimum_switch_advantage,
            )
        except ModelNotReadyError as error:
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "model_not_ready",
                    "component": "knock_model",
                    "message": str(error) or "Knock inference model is unavailable.",
                },
            ) from error
        except (TypeError, ValueError) as error:
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "invalid_model_output",
                    "component": "decision_analysis",
                    "message": "The model or decision modules returned invalid values.",
                },
            ) from error
        except Exception as error:
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "decision_analysis_failed",
                    "component": "decision_analysis",
                    "message": "The disposition decision could not be completed.",
                },
            ) from error
    finally:
        audio_path.unlink(missing_ok=True)


@app.post(
    "/v1/audio/analyze",
    response_model=VehicleAnalysisResult,
    summary="Analyze engine audio for one vehicle",
    description=(
        "Upload one WAV file with a vehicle_id field. Files are limited to "
        f"{MAX_UPLOAD_BYTES} bytes and are deleted after analysis."
    ),
    responses={
        400: {"description": "The vehicle ID or WAV file is invalid."},
        413: {"description": "The WAV file exceeds the upload size limit."},
        503: {"description": "Required knock inference is not ready."},
    },
)
def analyze_audio(
    audio_file: UploadFile = File(...),
    vehicle_id: str = Form(...),
) -> VehicleAnalysisResult:
    return _analyze_upload(audio_file, _validated_vehicle_id(vehicle_id))


@app.post(
    "/v1/audio/compare",
    response_model=ComparisonResponse,
    summary="Compare acoustic risk across vehicles",
    description=(
        "Send 2 to 5 repeated vehicle_ids fields aligned with 2 to 5 repeated "
        "audio_files WAV uploads. Results are ranked lowest acoustic risk first."
    ),
    responses={
        400: {"description": "Vehicle IDs and WAV files are malformed or misaligned."},
        413: {"description": "A WAV file exceeds the upload size limit."},
        503: {"description": "Required knock inference is not ready."},
    },
)
def compare_audio(
    vehicle_ids: List[str] = Form(...),
    audio_files: List[UploadFile] = File(...),
) -> ComparisonResponse:
    if len(vehicle_ids) != len(audio_files):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "mismatched_compare_fields",
                "message": "Provide one vehicle_id for each audio_file.",
            },
        )
    if not 2 <= len(audio_files) <= MAX_COMPARE_FILES:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_compare_count",
                "message": f"Comparison requires 2 to {MAX_COMPARE_FILES} vehicles.",
            },
        )

    normalized_ids = [_validated_vehicle_id(vehicle_id) for vehicle_id in vehicle_ids]
    if len(set(normalized_ids)) != len(normalized_ids):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "duplicate_vehicle_id",
                "message": "Each vehicle_id must be unique within a comparison.",
            },
        )

    results = [
        _analyze_upload(audio_file, vehicle_id)
        for vehicle_id, audio_file in zip(normalized_ids, audio_files)
    ]
    return ComparisonResponse.from_results(results)
