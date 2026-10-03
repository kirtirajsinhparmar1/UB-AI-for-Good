import json
import sys
import wave
from pathlib import Path
from types import SimpleNamespace

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT / "scripts"))

import demo_compare  # noqa: E402
import preflight  # noqa: E402
from app.model.knock_model import KnockModelResult  # noqa: E402


def _write_synthetic_test_wav(path: Path) -> Path:
    """Write a plumbing fixture only; it is not a real engine recording."""
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(b"\x00\x00" * 160)
    return path


def test_cli_compares_two_vehicles_and_ranks_lowest_risk_first(tmp_path, monkeypatch, capsys):
    audio_a = _write_synthetic_test_wav(tmp_path / "synthetic_test_a.wav")
    audio_b = _write_synthetic_test_wav(tmp_path / "synthetic_test_b.wav")
    probabilities = {audio_a: 0.72, audio_b: 0.18}
    calls = []

    def fake_analyze_knock(path):
        calls.append(path)
        return KnockModelResult(probabilities[path], "test-only-mock")

    monkeypatch.setattr(demo_compare, "analyze_knock", fake_analyze_knock)
    monkeypatch.setattr(demo_compare, "_load_optional_analyzer", lambda: (None, "not installed"))

    result = demo_compare.main(
        ["--vehicle", "A", str(audio_a), "--vehicle", "B", str(audio_b)]
    )

    output = capsys.readouterr()
    assert result == 0
    assert calls == [audio_a, audio_b]
    assert "ACOUSTIC VEHICLE COMPARISON" in output.out
    assert "Lowest acoustic risk: B" in output.out
    ranked_rows = [line.split() for line in output.out.splitlines() if line[:1].isdigit()]
    assert [row[1] for row in ranked_rows] == ["B", "A"]
    assert "continuing with knock risk only" in output.err


def test_invalid_wav_path_is_reported_without_traceback(tmp_path, capsys):
    missing = tmp_path / "missing.wav"
    result = demo_compare.main(
        ["--vehicle", "A", str(missing), "--vehicle", "B", str(missing)]
    )
    output = capsys.readouterr()

    assert result == 2
    assert "ERROR:" in output.err
    assert "not a readable WAV file" in output.err
    assert "Traceback" not in output.err


def test_unsupported_file_is_reported_clearly(tmp_path, capsys):
    unsupported = tmp_path / "recording.mp3"
    unsupported.write_bytes(b"audio")
    valid = _write_synthetic_test_wav(tmp_path / "synthetic_test.wav")

    result = demo_compare.main(
        ["--vehicle", "A", str(unsupported), "--vehicle", "B", str(valid)]
    )
    output = capsys.readouterr()

    assert result == 2
    assert "recording.mp3 is not a readable WAV file" in output.err
    assert "Only .wav files are supported" in output.err


def test_unavailable_anomaly_model_does_not_break_comparison(tmp_path, monkeypatch, capsys):
    audio_a = _write_synthetic_test_wav(tmp_path / "synthetic_test_a.wav")
    audio_b = _write_synthetic_test_wav(tmp_path / "synthetic_test_b.wav")
    monkeypatch.setattr(
        demo_compare,
        "analyze_knock",
        lambda path: KnockModelResult(0.25 if path == audio_a else 0.5, "test-only-mock"),
    )
    monkeypatch.setattr(demo_compare, "_load_optional_analyzer", lambda: (None, "missing package"))

    result = demo_compare.main(
        ["--vehicle", "A", str(audio_a), "--vehicle", "B", str(audio_b)]
    )
    output = capsys.readouterr()

    assert result == 0
    assert "Lowest acoustic risk: A" in output.out
    assert "Optional anomaly model unavailable" in output.err


def test_json_output_matches_comparison_contract(tmp_path, monkeypatch, capsys):
    audio_a = _write_synthetic_test_wav(tmp_path / "synthetic_test_a.wav")
    audio_b = _write_synthetic_test_wav(tmp_path / "synthetic_test_b.wav")
    monkeypatch.setattr(
        demo_compare,
        "analyze_knock",
        lambda path: KnockModelResult(0.2 if path == audio_a else 0.7, "test-only-mock"),
    )
    monkeypatch.setattr(demo_compare, "_load_optional_analyzer", lambda: (None, None))

    result = demo_compare.main(
        ["--vehicle", "A", str(audio_a), "--vehicle", "B", str(audio_b), "--json"]
    )
    output = capsys.readouterr()
    payload = json.loads(output.out)

    assert result == 0
    assert set(payload) == {"results", "ranking", "lowest_acoustic_risk_vehicle"}
    assert [entry["vehicle_id"] for entry in payload["ranking"]] == ["A", "B"]
    assert payload["lowest_acoustic_risk_vehicle"] == "A"


def test_preflight_reports_missing_transformers_package(monkeypatch, capsys):
    def fake_load_module(module_name):
        if module_name == "transformers":
            raise ModuleNotFoundError("No module named 'transformers'", name="transformers")
        return SimpleNamespace()

    monkeypatch.setattr(preflight, "_load_module", fake_load_module)

    ready, modules = preflight._check_ml_imports()
    output = capsys.readouterr()

    assert ready is False
    assert "transformers" not in modules
    assert "[FAIL] Transformers" in output.out
    assert "python -m pip install transformers" in output.out
