"""FastAPI application and upload orchestration."""

from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from app.model import ModelNotReadyError
from app.model.anomaly_model import analyze_anomaly
from app.model.audio_io import AudioValidationError, validate_wav
from app.model.knock_model import analyze_knock
from app.schemas import ComparisonResponse, ModelSignals, VehicleAnalysisResult
from app.scoring.acoustic_score import score_acoustic_risk


app = FastAPI(title="Acoustic Intelligence")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "acoustic-intelligence"}


def _analyze_upload(upload: UploadFile, vehicle_id: Optional[str]) -> VehicleAnalysisResult:
    filename = upload.filename
    if not filename:
        raise HTTPException(
            status_code=400,
            detail={"code": "invalid_audio", "message": "An audio filename is required."},
        )

    suffix = Path(filename).suffix.lower()
    if suffix != ".wav":
        raise HTTPException(
            status_code=400,
            detail={"code": "invalid_audio", "message": "Only .wav files are supported."},
        )

    with TemporaryDirectory() as temporary_directory:
        audio_path = Path(temporary_directory) / ("upload" + suffix)
        with audio_path.open("wb") as destination:
            shutil.copyfileobj(upload.file, destination)
        try:
            validate_wav(str(audio_path))
        except AudioValidationError as error:
            raise HTTPException(
                status_code=400,
                detail={"code": "invalid_audio", "message": str(error)},
            ) from error

        try:
            knock = analyze_knock(audio_path)
        except ModelNotReadyError as error:
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "model_not_ready",
                    "component": "knock_model",
                    "message": str(error),
                },
            ) from error

        anomaly = None
        warnings = []
        try:
            anomaly = analyze_anomaly(audio_path)
        except ModelNotReadyError:
            warnings.append("Anomaly model inference is not configured.")

        anomaly_score = anomaly.general_anomaly_score if anomaly else None
        score = score_acoustic_risk(knock.knock_probability, anomaly_score)
        return VehicleAnalysisResult(
            vehicle_id=vehicle_id or Path(filename).stem,
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


@app.post(
    "/v1/audio/analyze",
    response_model=VehicleAnalysisResult,
    responses={503: {"description": "Required knock model is not ready."}},
)
def analyze_audio(
    file: UploadFile = File(...),
    vehicle_id: Optional[str] = Form(default=None),
) -> VehicleAnalysisResult:
    return _analyze_upload(file, vehicle_id)


@app.post(
    "/v1/audio/compare",
    response_model=ComparisonResponse,
    responses={503: {"description": "Required knock model is not ready."}},
)
def compare_audio(files: List[UploadFile] = File(...)) -> ComparisonResponse:
    results = [_analyze_upload(file, None) for file in files]
    return ComparisonResponse.from_results(results)
