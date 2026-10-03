"""Offline terminal comparison using the backend's real knock interface."""

import argparse
import importlib
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Callable, List, Optional, Sequence, Tuple


# A live fallback must not attempt to reach Hugging Face or another service.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.model import ModelNotReadyError  # noqa: E402
from app.model.audio_io import AudioValidationError, validate_wav  # noqa: E402
from app.model.knock_model import analyze_knock  # noqa: E402
from app.schemas import ComparisonResponse, ModelSignals, VehicleAnalysisResult  # noqa: E402
from app.scoring.acoustic_score import score_acoustic_risk  # noqa: E402


def _short_error(error: Exception) -> str:
    message = str(error).splitlines()[0].strip() if str(error) else error.__class__.__name__
    return message[:240]


def _load_optional_analyzer() -> Tuple[Optional[Callable[[Path], Any]], Optional[str]]:
    try:
        module = importlib.import_module("app.model.anomaly_model")
        analyzer = getattr(module, "analyze_anomaly")
    except Exception as error:
        return None, _short_error(error)
    return analyzer, None


def _parse_arguments(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare 2–5 WAV recordings with the local knock model. "
            "Inference runs offline and uses the same analyze_knock interface as the API."
        )
    )
    parser.add_argument(
        "--vehicle",
        nargs=2,
        action="append",
        metavar=("ID", "WAV"),
        required=True,
        help="vehicle label and WAV path; repeat once per vehicle (2–5 total)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the existing ComparisonResponse JSON contract",
    )
    return parser.parse_args(argv)


def _validate_vehicles(raw_vehicles: Sequence[Sequence[str]]) -> List[Tuple[str, Path]]:
    if not 2 <= len(raw_vehicles) <= 5:
        raise ValueError("provide between 2 and 5 --vehicle ID WAV entries")

    vehicles: List[Tuple[str, Path]] = []
    seen_ids = set()
    for vehicle_id, raw_path in raw_vehicles:
        vehicle_id = vehicle_id.strip()
        if not vehicle_id:
            raise ValueError("vehicle IDs cannot be empty")
        if vehicle_id in seen_ids:
            raise ValueError(f"vehicle ID '{vehicle_id}' is repeated")
        seen_ids.add(vehicle_id)

        path = Path(raw_path).expanduser()
        try:
            validate_wav(str(path))
        except (AudioValidationError, OSError) as error:
            raise ValueError(f"{path} is not a readable WAV file. {_short_error(error)}") from error
        vehicles.append((vehicle_id, path))
    return vehicles


def _analyze_vehicles(
    vehicles: Sequence[Tuple[str, Path]],
    anomaly_analyzer: Optional[Callable[[Path], Any]],
) -> List[VehicleAnalysisResult]:
    results: List[VehicleAnalysisResult] = []
    for vehicle_id, audio_path in vehicles:
        try:
            knock = analyze_knock(audio_path)
        except ModelNotReadyError as error:
            raise RuntimeError(f"knock model is not ready: {_short_error(error)}") from error
        except Exception as error:
            raise RuntimeError(
                f"knock model failed for {vehicle_id}: {_short_error(error)}"
            ) from error

        anomaly = None
        warnings: List[str] = []
        if anomaly_analyzer is not None:
            try:
                candidate = anomaly_analyzer(audio_path)
                candidate_score = float(candidate.general_anomaly_score)
                if not math.isfinite(candidate_score) or not 0.0 <= candidate_score <= 1.0:
                    raise ValueError("anomaly score must be between 0.0 and 1.0")
                anomaly = candidate
            except Exception as error:
                warning = f"Optional anomaly model unavailable for {vehicle_id}: {_short_error(error)}"
                warnings.append(warning)
                print(f"WARNING: {warning}", file=sys.stderr)

        anomaly_score = float(anomaly.general_anomaly_score) if anomaly is not None else None
        score = score_acoustic_risk(knock.knock_probability, anomaly_score)
        results.append(
            VehicleAnalysisResult(
                vehicle_id=vehicle_id,
                filename=audio_path.name,
                knock_probability=knock.knock_probability,
                general_anomaly_score=anomaly_score,
                acoustic_risk_score=score.acoustic_risk_score,
                risk_band=score.risk_band,
                model_signals=ModelSignals(
                    knock_model=knock.model_name,
                    anomaly_model=anomaly.model_name if anomaly is not None else None,
                ),
                warnings=warnings,
            )
        )
    return results


def _print_table(comparison: ComparisonResponse) -> None:
    by_id = {result.vehicle_id: result for result in comparison.results}
    ordered = [by_id[entry.vehicle_id] for entry in comparison.ranking]
    vehicle_width = max(len("Vehicle"), *(len(result.vehicle_id) for result in ordered))
    header = f"{'Rank':<5}  {'Vehicle':<{vehicle_width}}  {'Knock Risk':<10}  {'Score':<5}  Band"
    separator = "-" * len(header)

    print("ACOUSTIC VEHICLE COMPARISON")
    print(separator)
    print(header)
    for rank, result in enumerate(ordered, start=1):
        print(
            f"{rank:<5}  {result.vehicle_id:<{vehicle_width}}  "
            f"{result.knock_probability:>10.2f}  "
            f"{result.acoustic_risk_score:<5}  {result.risk_band.upper()}"
        )
    print(separator)
    print(f"Lowest acoustic risk: {comparison.lowest_acoustic_risk_vehicle}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_arguments(argv)
    try:
        vehicles = _validate_vehicles(args.vehicle)
    except ValueError as error:
        print(f"ERROR: {_short_error(error)}", file=sys.stderr)
        return 2

    anomaly_analyzer, anomaly_import_error = _load_optional_analyzer()
    if anomaly_analyzer is None:
        message = "Optional anomaly model unavailable"
        if anomaly_import_error:
            message += f": {anomaly_import_error}"
        print(f"WARNING: {message}; continuing with knock risk only.", file=sys.stderr)

    try:
        results = _analyze_vehicles(vehicles, anomaly_analyzer)
    except RuntimeError as error:
        print(f"ERROR: {_short_error(error)}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"ERROR: Could not score model output: {_short_error(error)}", file=sys.stderr)
        return 1

    comparison = ComparisonResponse.from_results(results)
    if args.json:
        print(comparison.json())
    else:
        _print_table(comparison)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
