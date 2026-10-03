import tempfile
import unittest
import wave
from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.main import app
from app.model.audio_io import AudioValidationError, validate_wav
from app.schemas import ComparisonResponse, ModelSignals, VehicleAnalysisResult
from app.scoring.acoustic_score import risk_band_for_score, score_acoustic_risk


def analysis(vehicle_id: str, risk: int) -> VehicleAnalysisResult:
    return VehicleAnalysisResult(
        vehicle_id=vehicle_id,
        filename=vehicle_id + ".wav",
        knock_probability=risk / 100,
        general_anomaly_score=None,
        acoustic_risk_score=risk,
        risk_band=risk_band_for_score(risk),
        model_signals=ModelSignals(knock_model="test-model", anomaly_model=None),
    )


class BootstrapTests(unittest.TestCase):
    def test_result_schema_accepts_valid_values(self) -> None:
        result = analysis("car_a", 12)
        self.assertEqual(result.knock_probability, 0.12)
        self.assertEqual(result.model_signals.anomaly_model, None)

    def test_result_schema_rejects_probability_outside_range(self) -> None:
        with self.assertRaises(ValidationError):
            VehicleAnalysisResult(
                vehicle_id="car_a",
                filename="car_a.wav",
                knock_probability=1.1,
                acoustic_risk_score=12,
                risk_band="low",
                model_signals=ModelSignals(knock_model="test-model"),
            )

    def test_risk_score_range_and_risk_band(self) -> None:
        with self.assertRaises(ValidationError):
            VehicleAnalysisResult(
                vehicle_id="car_a",
                filename="car_a.wav",
                knock_probability=0.12,
                acoustic_risk_score=101,
                risk_band="high",
                model_signals=ModelSignals(knock_model="test-model"),
            )
        with self.assertRaises(ValidationError):
            VehicleAnalysisResult(
                vehicle_id="car_a",
                filename="car_a.wav",
                knock_probability=0.12,
                acoustic_risk_score=12,
                risk_band="unknown",
                model_signals=ModelSignals(knock_model="test-model"),
            )

    def test_scoring_values_and_bands(self) -> None:
        for probability, expected in ((0.12, 12), (0.50, 50), (0.86, 86)):
            self.assertEqual(score_acoustic_risk(probability).acoustic_risk_score, expected)
        self.assertEqual(risk_band_for_score(12), "low")
        self.assertEqual(risk_band_for_score(50), "medium")
        self.assertEqual(risk_band_for_score(86), "high")

    def test_comparison_ranks_lowest_risk_first(self) -> None:
        comparison = ComparisonResponse.from_results(
            [analysis("car_b", 46), analysis("car_a", 14)]
        )
        self.assertEqual([entry.vehicle_id for entry in comparison.ranking], ["car_a", "car_b"])
        self.assertEqual(comparison.lowest_acoustic_risk_vehicle, "car_a")

    def test_wav_validation_rejects_unsupported_extension(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "engine.mp3"
            path.write_bytes(b"audio")
            with self.assertRaisesRegex(AudioValidationError, "Only .wav"):
                validate_wav(str(path))

    def test_wav_validation_reads_basic_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "engine.wav"
            with wave.open(str(path), "wb") as audio:
                audio.setnchannels(1)
                audio.setsampwidth(2)
                audio.setframerate(8000)
                audio.writeframes(b"\x00\x00" * 800)
            metadata = validate_wav(str(path))
            self.assertEqual(metadata.sample_rate, 8000)
            self.assertEqual(metadata.channels, 1)
            self.assertEqual(metadata.duration_seconds, 0.1)

    def test_health_endpoint(self) -> None:
        response = TestClient(app).get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "service": "acoustic-intelligence"},
        )

if __name__ == "__main__":
    unittest.main()
