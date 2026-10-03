"""Self-inspection service and isolated router tests with a mocked model."""

from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from typing import Optional
import wave

import pytest

from app.model import ModelNotReadyError
from app.self_inspection import service


def _write_wav(
    path: Path,
    *,
    duration_seconds: float = 2.0,
    sample_rate: int = 16_000,
    channels: int = 1,
) -> None:
    frame_count = int(duration_seconds * sample_rate)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * frame_count * channels)


def _wav_bytes(duration_seconds: float = 2.0, sample_rate: int = 16_000) -> bytes:
    output = BytesIO()
    frame_count = int(duration_seconds * sample_rate)
    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * frame_count)
    return output.getvalue()


def _knock_result(probability: float = 0.12) -> SimpleNamespace:
    return SimpleNamespace(knock_probability=probability, model_name="mock-local-model")


def _router_client():
    pytest.importorskip("fastapi")
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.api.self_inspection_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_valid_wav_preserves_probability_and_uses_existing_scoring(monkeypatch, tmp_path: Path) -> None:
    audio_path = tmp_path / "engine.wav"
    _write_wav(audio_path, channels=2)
    monkeypatch.setattr(service, "analyze_knock", lambda path: _knock_result(0.67))

    result = service.analyze_self_inspection(" vehicle-A ", audio_path)

    assert result.vehicle_id == "vehicle-A"
    assert result.filename == "engine.wav"
    assert result.capture.duration_seconds == 2.0
    assert result.capture.sample_rate == 16_000
    assert result.capture.channels == 2
    assert result.capture.quality_status == "good"
    assert result.acoustic.knock_probability == 0.67
    assert result.acoustic.acoustic_risk_score == 67
    assert result.acoustic.risk_band == "high"
    assert result.acoustic.model_name == "mock-local-model"
    assert result.status == "ready"


def test_invalid_extension_is_rejected_without_inference(monkeypatch, tmp_path: Path) -> None:
    audio_path = tmp_path / "engine.mp3"
    audio_path.write_bytes(_wav_bytes())
    monkeypatch.setattr(service, "analyze_knock", lambda _path: pytest.fail("must not infer"))

    with pytest.raises(service.SelfInspectionAudioError, match=r"Only \.wav"):
        service.analyze_self_inspection("vehicle-A", audio_path)


def test_missing_file_is_rejected_without_inference(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(service, "analyze_knock", lambda _path: pytest.fail("must not infer"))

    with pytest.raises(service.SelfInspectionAudioError, match="does not exist"):
        service.analyze_self_inspection("vehicle-A", tmp_path / "missing.wav")


def test_corrupt_wav_is_rejected_without_inference(monkeypatch, tmp_path: Path) -> None:
    audio_path = tmp_path / "broken.wav"
    audio_path.write_bytes(b"not a WAV file")
    monkeypatch.setattr(service, "analyze_knock", lambda _path: pytest.fail("must not infer"))

    with pytest.raises(service.SelfInspectionAudioError, match="readable WAV"):
        service.analyze_self_inspection("vehicle-A", audio_path)


def test_too_short_capture_is_returned_with_quality_warning(monkeypatch, tmp_path: Path) -> None:
    audio_path = tmp_path / "short.wav"
    _write_wav(audio_path, duration_seconds=1.0)
    monkeypatch.setattr(service, "analyze_knock", lambda _path: _knock_result())

    result = service.analyze_self_inspection("vehicle-A", audio_path)

    assert result.capture.quality_status == "warning"
    assert any(
        "shorter than the recommended 2 seconds" in warning
        for warning in result.capture.quality_warnings
    )


def test_long_capture_warns_and_maximum_duration_is_enforced(monkeypatch, tmp_path: Path) -> None:
    long_path = tmp_path / "long.wav"
    _write_wav(long_path, duration_seconds=31.0)
    monkeypatch.setattr(service, "analyze_knock", lambda _path: _knock_result())

    result = service.analyze_self_inspection("vehicle-A", long_path)
    assert result.capture.quality_status == "warning"
    assert any("longer than 30 seconds" in warning for warning in result.capture.quality_warnings)

    overlong_path = tmp_path / "overlong.wav"
    _write_wav(overlong_path, duration_seconds=61.0)
    with pytest.raises(service.SelfInspectionAudioError, match="must not exceed 60 seconds"):
        service.analyze_self_inspection("vehicle-A", overlong_path)


def test_very_low_sample_rate_is_rejected(monkeypatch, tmp_path: Path) -> None:
    audio_path = tmp_path / "low-rate.wav"
    _write_wav(audio_path, sample_rate=4_000)
    monkeypatch.setattr(service, "analyze_knock", lambda _path: pytest.fail("must not infer"))

    with pytest.raises(service.SelfInspectionAudioError, match="at least 8000 Hz"):
        service.analyze_self_inspection("vehicle-A", audio_path)


def test_model_unavailable_is_exposed_as_service_error(monkeypatch, tmp_path: Path) -> None:
    audio_path = tmp_path / "engine.wav"
    _write_wav(audio_path)

    def unavailable(_path: Path):
        raise ModelNotReadyError("local weights are unavailable")

    monkeypatch.setattr(service, "analyze_knock", unavailable)
    with pytest.raises(service.SelfInspectionModelUnavailableError, match="local weights"):
        service.analyze_self_inspection("vehicle-A", audio_path)


def test_router_imports_without_main_and_deletes_upload_temp_file(monkeypatch) -> None:
    pytest.importorskip("fastapi")
    captured_paths = []

    def analyze(vehicle_id: str, audio_path: Path, *, filename: Optional[str] = None):
        captured_paths.append(audio_path)
        return service.SelfInspectionResult(
            vehicle_id=vehicle_id,
            filename=filename or audio_path.name,
            capture=service.CaptureAssessment(
                duration_seconds=2.0,
                sample_rate=16_000,
                channels=1,
                quality_status="good",
            ),
            acoustic=service.AcousticAssessment(
                knock_probability=0.12,
                acoustic_risk_score=12,
                risk_band="low",
                model_name="mock-local-model",
            ),
            status="ready",
        )

    monkeypatch.setattr("app.api.self_inspection_router.analyze_self_inspection", analyze)
    with _router_client() as client:
        response = client.post(
            "/v1/self-inspection/analyze",
            data={"vehicle_id": "vehicle-A"},
            files={"audio_file": ("../../engine.wav", _wav_bytes(), "audio/wav")},
        )

    assert response.status_code == 200
    result = response.json()
    assert result["filename"] == "engine.wav"
    assert result["acoustic"]["knock_probability"] == 0.12
    assert len(captured_paths) == 1
    assert captured_paths[0].suffix == ".wav"
    assert not captured_paths[0].exists()


def test_router_model_unavailable_returns_503_and_cleans_upload(monkeypatch) -> None:
    pytest.importorskip("fastapi")
    captured_paths = []

    def unavailable(vehicle_id: str, audio_path: Path, *, filename: Optional[str] = None):
        captured_paths.append(audio_path)
        raise service.SelfInspectionModelUnavailableError("local model unavailable")

    monkeypatch.setattr("app.api.self_inspection_router.analyze_self_inspection", unavailable)
    with _router_client() as client:
        response = client.post(
            "/v1/self-inspection/analyze",
            data={"vehicle_id": "vehicle-A"},
            files={"audio_file": ("engine.wav", _wav_bytes(), "audio/wav")},
        )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "model_not_ready"
    assert len(captured_paths) == 1
    assert not captured_paths[0].exists()


def test_router_rejects_unsupported_format_and_inference_failure(monkeypatch) -> None:
    pytest.importorskip("fastapi")
    monkeypatch.setattr(
        "app.api.self_inspection_router.analyze_self_inspection",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("private detail")),
    )
    with _router_client() as client:
        unsupported = client.post(
            "/v1/self-inspection/analyze",
            data={"vehicle_id": "vehicle-A"},
            files={"audio_file": ("engine.m4a", b"not WAV", "audio/mp4")},
        )
        failed = client.post(
            "/v1/self-inspection/analyze",
            data={"vehicle_id": "vehicle-A"},
            files={"audio_file": ("engine.wav", _wav_bytes(), "audio/wav")},
        )

    assert unsupported.status_code == 400
    assert unsupported.json()["detail"]["code"] == "invalid_audio"
    assert failed.status_code == 500
    assert failed.json()["detail"]["code"] == "knock_inference_failed"
    assert "private detail" not in failed.text


def test_router_invalid_wav_returns_400(monkeypatch) -> None:
    monkeypatch.setattr(service, "analyze_knock", lambda _path: pytest.fail("must not infer"))

    with _router_client() as client:
        response = client.post(
            "/v1/self-inspection/analyze",
            data={"vehicle_id": "vehicle-A"},
            files={"audio_file": ("engine.wav", b"not a WAV file", "audio/wav")},
        )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_audio"
