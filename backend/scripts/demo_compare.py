"""Validate demo WAVs and compare them once model interfaces are implemented."""

import argparse
import json
from pathlib import Path
import sys

from app.model import ModelNotReadyError
from app.model.anomaly_model import analyze_anomaly
from app.model.audio_io import AudioValidationError, validate_wav
from app.model.knock_model import analyze_knock
from app.schemas import ComparisonResponse, ModelSignals, VehicleAnalysisResult
from app.scoring.acoustic_score import score_acoustic_risk


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", nargs="+", type=Path, help="WAV files to compare")
    args = parser.parse_args()

    results = []
    for audio_path in args.audio:
        try:
            validate_wav(str(audio_path))
            knock = analyze_knock(audio_path)
        except (AudioValidationError, ModelNotReadyError) as error:
            print(str(error), file=sys.stderr)
            return 1

        try:
            anomaly = analyze_anomaly(audio_path)
        except ModelNotReadyError:
            anomaly = None
        anomaly_score = anomaly.general_anomaly_score if anomaly else None
        score = score_acoustic_risk(knock.knock_probability, anomaly_score)
        results.append(
            VehicleAnalysisResult(
                vehicle_id=audio_path.stem,
                filename=audio_path.name,
                knock_probability=knock.knock_probability,
                general_anomaly_score=anomaly_score,
                acoustic_risk_score=score.acoustic_risk_score,
                risk_band=score.risk_band,
                model_signals=ModelSignals(
                    knock_model=knock.model_name,
                    anomaly_model=anomaly.model_name if anomaly else None,
                ),
                warnings=["Anomaly model inference is not configured."] if anomaly is None else [],
            )
        )

    comparison = ComparisonResponse.from_results(results)
    print(comparison.json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
