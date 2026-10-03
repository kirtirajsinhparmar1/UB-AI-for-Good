"""Mobile upload endpoint for local acoustic self-inspection."""

import os
from pathlib import Path, PurePosixPath
from tempfile import NamedTemporaryFile
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.self_inspection.models import SelfInspectionResult
from app.self_inspection.service import (
    SelfInspectionAudioError,
    SelfInspectionModelUnavailableError,
    analyze_self_inspection,
)


MAX_UPLOAD_BYTES = int(os.getenv("ACOUSTIC_MAX_UPLOAD_BYTES", 10 * 1024 * 1024))
UPLOAD_CHUNK_BYTES = 64 * 1024

router = APIRouter()


def _invalid_audio(message: str) -> HTTPException:
    return HTTPException(
        status_code=400,
        detail={"code": "invalid_audio", "message": message},
    )


def _display_filename(filename: Optional[str]) -> str:
    if not filename:
        raise _invalid_audio("An audio filename is required.")
    normalized = filename.replace("\\", "/")
    safe_name = PurePosixPath(normalized).name
    if not safe_name:
        raise _invalid_audio("An audio filename is required.")
    if PurePosixPath(safe_name).suffix.lower() != ".wav":
        raise _invalid_audio("Only .wav files are supported.")
    return safe_name


def _save_upload(upload: UploadFile) -> tuple[Path, str]:
    filename = _display_filename(upload.filename)
    temporary_file = NamedTemporaryFile(
        mode="wb", suffix=".wav", prefix="self-inspection-", delete=False
    )
    audio_path = Path(temporary_file.name)
    try:
        with temporary_file:
            size = 0
            while True:
                chunk = upload.file.read(UPLOAD_CHUNK_BYTES)
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
        return audio_path, filename
    except Exception:
        audio_path.unlink(missing_ok=True)
        raise


@router.post(
    "/v1/self-inspection/analyze",
    response_model=SelfInspectionResult,
    summary="Assess acoustic knock risk from a mobile WAV recording",
    description=(
        "Upload a WAV engine recording with a vehicle_id field. The recording is "
        "analyzed by the local knock model and the temporary upload is deleted afterward."
    ),
    responses={
        400: {"description": "The vehicle ID, WAV file, or capture quality is invalid."},
        413: {"description": "The WAV file exceeds the upload size limit."},
        500: {"description": "Local knock inference failed."},
        503: {"description": "The local knock model is unavailable."},
    },
)
def analyze_mobile_self_inspection(
    vehicle_id: str = Form(...),
    audio_file: UploadFile = File(...),
) -> SelfInspectionResult:
    normalized_vehicle_id = vehicle_id.strip()
    if not normalized_vehicle_id:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_vehicle_id",
                "message": "vehicle_id must not be empty.",
            },
        )

    audio_path, filename = _save_upload(audio_file)
    try:
        try:
            return analyze_self_inspection(
                normalized_vehicle_id,
                audio_path,
                filename=filename,
            )
        except SelfInspectionAudioError as error:
            raise _invalid_audio(str(error)) from error
        except SelfInspectionModelUnavailableError as error:
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "model_not_ready",
                    "component": "knock_model",
                    "message": str(error),
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
    finally:
        audio_path.unlink(missing_ok=True)
