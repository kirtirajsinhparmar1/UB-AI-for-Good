"""Frontend decision API tests with local model inference mocked."""

from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import wave

from fastapi.testclient import TestClient

from app.api import main as api
from app.api import self_inspection_router as inspection_api
from app.decision import service as decision_service
from app.model import ModelNotReadyError
from app.self_inspection.models import (
    AcousticAssessment,
    CaptureAssessment,
    SelfInspectionResult,
)


def _wav_bytes() -> bytes:
    output = BytesIO()
    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16_000)
        wav_file.writeframes(b"\x00\x00" * 64)
    return output.getvalue()


def _post_decision(client, **overrides):
    data = {
        "vehicle_id": "vehicle-a",
        "base_wholesale_value": "15000",
        "copart_expected_gross": "11000",
        "acv_costs": "500",
        "copart_costs": "700",
    }
    data.update(overrides)
    return client.post(
        "/v1/decision/analyze",
        data=data,
        files={"audio_file": ("engine.wav", _wav_bytes(), "audio/wav")},
    )


def _knock_result(probability: float) -> SimpleNamespace:
    return SimpleNamespace(knock_probability=probability, model_name="mock-knock")


def test_clean_scenario_routes_to_acv_with_prototype_policy_and_cleanup(monkeypatch) -> None:
    captured_paths = []

    def analyze_knock(path: Path):
        captured_paths.append(path)
        return _knock_result(0.27)

    monkeypatch.setattr(decision_service, "analyze_knock", analyze_knock)
    with TestClient(api.app) as client:
        response = _post_decision(client)

    assert response.status_code == 200
    result = response.json()
    assert result["vehicle_id"] == "vehicle-a"
    assert result["acoustic"] == {
        "acoustic_knock_score": 27,
        "risk_band": "low",
        "model_name": "mock-knock",
    }
    assert result["valuation"]["acoustic_delta_amount"] == 48.75
    assert result["valuation"]["acoustic_delta_pct"] == 0.00325
    assert result["valuation"]["adjusted_wholesale_value"] == 15048.75
    assert result["valuation"]["policy_type"] == "prototype_demo_policy"
    assert "empirical calibration" in result["disclaimer"]
    assert result["economics"]["acv_expected_net"] == 14548.75
    assert result["economics"]["copart_expected_net"] == 10300
    assert result["decision"]["recommended_channel"] == "ACV"
    assert len(captured_paths) == 1
    assert not captured_paths[0].exists()


def test_high_acoustic_risk_scenario_routes_to_copart(monkeypatch) -> None:
    monkeypatch.setattr(
        decision_service, "analyze_knock", lambda _path: _knock_result(0.96)
    )
    with TestClient(api.app) as client:
        response = _post_decision(
            client,
            copart_expected_gross="15000",
        )

    assert response.status_code == 200
    result = response.json()
    assert result["acoustic"]["acoustic_knock_score"] == 96
    assert result["acoustic"]["risk_band"] == "high"
    assert result["valuation"]["acoustic_delta_amount"] == -2040
    assert result["valuation"]["adjusted_wholesale_value"] == 12960
    assert result["decision"]["recommended_channel"] == "COPART"


def test_narrow_net_difference_routes_to_review(monkeypatch) -> None:
    monkeypatch.setattr(
        decision_service, "analyze_knock", lambda _path: _knock_result(0.27)
    )
    with TestClient(api.app) as client:
        response = _post_decision(
            client,
            copart_expected_gross="15498.75",
        )

    assert response.status_code == 200
    result = response.json()
    assert result["economics"]["net_difference"] == 250
    assert result["decision"]["recommended_channel"] == "REVIEW"
    assert result["decision"]["decision_strength"] == "weak"


def test_invalid_base_wholesale_value_returns_structured_error() -> None:
    with TestClient(api.app) as client:
        response = _post_decision(client, base_wholesale_value="0")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_base_wholesale_value"


def test_invalid_copart_gross_returns_structured_error() -> None:
    with TestClient(api.app) as client:
        response = _post_decision(client, copart_expected_gross="-1")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_copart_expected_gross"


def test_invalid_wav_is_rejected_before_inference(monkeypatch) -> None:
    def unexpected_inference(_path):
        raise AssertionError("invalid WAV must not reach inference")

    monkeypatch.setattr(decision_service, "analyze_knock", unexpected_inference)
    with TestClient(api.app) as client:
        response = client.post(
            "/v1/decision/analyze",
            data={
                "vehicle_id": "vehicle-a",
                "base_wholesale_value": "15000",
                "copart_expected_gross": "11000",
            },
            files={"audio_file": ("engine.wav", b"not a wav", "audio/wav")},
        )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_audio"


def test_unavailable_model_returns_503_and_cleans_temporary_file(monkeypatch) -> None:
    captured_paths = []

    def unavailable(path: Path):
        captured_paths.append(path)
        raise ModelNotReadyError("cached model weights unavailable")

    monkeypatch.setattr(decision_service, "analyze_knock", unavailable)
    with TestClient(api.app) as client:
        response = _post_decision(client)

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "model_not_ready"
    assert len(captured_paths) == 1
    assert not captured_paths[0].exists()


def test_self_inspection_route_is_mounted_and_uses_its_service(monkeypatch) -> None:
    captured_paths = []

    def inspect(vehicle_id: str, audio_path: Path, *, filename: str):
        captured_paths.append(audio_path)
        return SelfInspectionResult(
            vehicle_id=vehicle_id,
            filename=filename,
            capture=CaptureAssessment(
                duration_seconds=2,
                sample_rate=16_000,
                channels=1,
                quality_status="good",
            ),
            acoustic=AcousticAssessment(
                knock_probability=0.27,
                acoustic_risk_score=27,
                risk_band="low",
                model_name="mock-knock",
            ),
            status="ready",
        )

    monkeypatch.setattr(inspection_api, "analyze_self_inspection", inspect)
    with TestClient(api.app) as client:
        response = client.post(
            "/v1/self-inspection/analyze",
            data={"vehicle_id": "mobile-vehicle"},
            files={"audio_file": ("engine.wav", _wav_bytes(), "audio/wav")},
        )

    assert response.status_code == 200
    assert response.json()["vehicle_id"] == "mobile-vehicle"
    assert len(captured_paths) == 1
    assert not captured_paths[0].exists()
