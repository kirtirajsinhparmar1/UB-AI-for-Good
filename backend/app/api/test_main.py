"""API orchestration tests using mocked model interfaces."""

from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import wave

from fastapi.testclient import TestClient

from app.api import main as api
from app.model import ModelNotReadyError


def _wav_bytes() -> bytes:
    output = BytesIO()
    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16_000)
        wav_file.writeframes(b"\x00\x00" * 64)
    return output.getvalue()


def _knock_result(probability: float) -> SimpleNamespace:
    return SimpleNamespace(knock_probability=probability, model_name="mock-knock")


def test_health_does_not_run_models(monkeypatch) -> None:
    def unexpected_call(*_args):
        raise AssertionError("health must not run inference")

    monkeypatch.setattr(api, "analyze_knock", unexpected_call)
    monkeypatch.setattr(api, "analyze_anomaly", unexpected_call)

    with TestClient(api.app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "acoustic-intelligence"}


def test_local_frontend_origin_passes_cors_preflight() -> None:
    with TestClient(api.app) as client:
        response = client.options(
            "/v1/audio/analyze",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_analyze_returns_scored_result_and_cleans_temp_file(monkeypatch) -> None:
    captured_paths = []

    def analyze_knock(path: Path) -> SimpleNamespace:
        captured_paths.append(path)
        return _knock_result(0.12)

    def anomaly_unavailable(_path: Path):
        raise ModelNotReadyError("optional model unavailable")

    monkeypatch.setattr(api, "analyze_knock", analyze_knock)
    monkeypatch.setattr(api, "analyze_anomaly", anomaly_unavailable)

    with TestClient(api.app) as client:
        response = client.post(
            "/v1/audio/analyze",
            data={"vehicle_id": "vehicle-A"},
            files={"audio_file": ("engine.wav", _wav_bytes(), "audio/wav")},
        )

    assert response.status_code == 200
    result = response.json()
    assert result["vehicle_id"] == "vehicle-A"
    assert result["filename"] == "engine.wav"
    assert result["knock_probability"] == 0.12
    assert result["general_anomaly_score"] is None
    assert result["acoustic_risk_score"] == 12
    assert result["risk_band"] == "low"
    assert result["model_signals"]["anomaly_model"] is None
    assert result["warnings"]
    assert len(captured_paths) == 1
    assert captured_paths[0].suffix == ".wav"
    assert not captured_paths[0].exists()


def test_compare_ranks_lowest_acoustic_risk_first(monkeypatch) -> None:
    probabilities = iter((0.12, 0.50, 0.86))
    monkeypatch.setattr(api, "analyze_knock", lambda _path: _knock_result(next(probabilities)))

    def anomaly_unavailable(_path: Path):
        raise ModelNotReadyError("not configured")

    monkeypatch.setattr(api, "analyze_anomaly", anomaly_unavailable)

    multipart = [
        ("vehicle_ids", (None, "A")),
        ("vehicle_ids", (None, "B")),
        ("vehicle_ids", (None, "C")),
        ("audio_files", ("A.wav", _wav_bytes(), "audio/wav")),
        ("audio_files", ("B.wav", _wav_bytes(), "audio/wav")),
        ("audio_files", ("C.wav", _wav_bytes(), "audio/wav")),
    ]
    with TestClient(api.app) as client:
        response = client.post("/v1/audio/compare", files=multipart)

    assert response.status_code == 200
    result = response.json()
    assert [item["vehicle_id"] for item in result["results"]] == ["A", "B", "C"]
    assert [item["knock_probability"] for item in result["results"]] == [0.12, 0.50, 0.86]
    assert [item["acoustic_risk_score"] for item in result["results"]] == [12, 50, 86]
    assert [item["vehicle_id"] for item in result["ranking"]] == ["A", "B", "C"]
    assert [item["rank"] for item in result["ranking"]] == [1, 2, 3]
    assert result["lowest_acoustic_risk_vehicle"] == "A"


def test_rejects_unsupported_file(monkeypatch) -> None:
    monkeypatch.setattr(api, "analyze_knock", lambda _path: _knock_result(0.1))

    with TestClient(api.app) as client:
        response = client.post(
            "/v1/audio/analyze",
            data={"vehicle_id": "A"},
            files={"audio_file": ("engine.mp3", b"not wav", "audio/mpeg")},
        )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_audio"


def test_rejects_mismatched_compare_fields() -> None:
    multipart = [
        ("vehicle_ids", (None, "A")),
        ("vehicle_ids", (None, "B")),
        ("audio_files", ("A.wav", _wav_bytes(), "audio/wav")),
    ]
    with TestClient(api.app) as client:
        response = client.post("/v1/audio/compare", files=multipart)

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "mismatched_compare_fields"


def test_knock_model_not_ready_returns_structured_503_and_cleans_temp_file(monkeypatch) -> None:
    captured_paths = []

    def unavailable(path: Path):
        captured_paths.append(path)
        raise ModelNotReadyError("model weights unavailable")

    monkeypatch.setattr(api, "analyze_knock", unavailable)

    with TestClient(api.app) as client:
        response = client.post(
            "/v1/audio/analyze",
            data={"vehicle_id": "A"},
            files={"audio_file": ("engine.wav", _wav_bytes(), "audio/wav")},
        )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "model_not_ready"
    assert response.json()["detail"]["component"] == "knock_model"
    assert len(captured_paths) == 1
    assert not captured_paths[0].exists()


def test_knock_inference_error_returns_structured_500(monkeypatch) -> None:
    def failed(_path: Path):
        raise RuntimeError("internal detail")

    monkeypatch.setattr(api, "analyze_knock", failed)

    with TestClient(api.app) as client:
        response = client.post(
            "/v1/audio/analyze",
            data={"vehicle_id": "A"},
            files={"audio_file": ("engine.wav", _wav_bytes(), "audio/wav")},
        )

    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "knock_inference_failed"
