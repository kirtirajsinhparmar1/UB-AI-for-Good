"""Run and present one local acoustic vehicle-disposition decision."""

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Optional, Sequence


# Keep the demo local and prevent first-use model downloads.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.decision.service import analyze_decision  # noqa: E402
from app.model import ModelNotReadyError  # noqa: E402
from app.model.audio_io import AudioValidationError, validate_wav  # noqa: E402


def _parse_arguments(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze one WAV recording and recommend ACV, COPART, or REVIEW."
    )
    parser.add_argument("--vehicle", required=True, help="vehicle display name or ID")
    parser.add_argument("--audio", required=True, type=Path, help="engine WAV file")
    parser.add_argument("--base-wholesale", required=True, type=float)
    parser.add_argument("--copart-gross", required=True, type=float)
    parser.add_argument("--minimum-switch-advantage", type=float, default=500)
    parser.add_argument("--json", action="store_true", help="emit decision JSON")
    return parser.parse_args(argv)


def _currency(value: float) -> str:
    if round(value, 2).is_integer():
        return f"${value:,.0f}"
    return f"${value:,.2f}"


def _signed_currency(value: float) -> str:
    sign = "+" if value >= 0 else "-"
    return sign + _currency(abs(value))


def _print_decision(result) -> None:
    print("VEHICLE DISPOSITION INTELLIGENCE")
    print("------------------------------------------------")
    print()
    print(result.vehicle_id)
    print()
    print(f"{'Acoustic Knock Score':<28}{result.acoustic.acoustic_knock_score:>3} / 100")
    print(f"{'Acoustic Risk':<28}{result.acoustic.risk_band.upper()}")
    print()
    print(f"{'Base Wholesale Value':<28}{_currency(result.valuation.base_wholesale_value)}")
    print(f"{'Acoustic Value Delta':<28}{_signed_currency(result.valuation.acoustic_delta_amount)}")
    print()
    print(f"{'Adjusted ACV Value':<28}{_currency(result.economics.acv_expected_value)}")
    print(f"{'Copart Expected Value':<28}{_currency(result.economics.copart_expected_value)}")
    print()
    print(f"RECOMMENDED CHANNEL         {result.decision.recommended_channel}")
    print()
    print("Reason:")
    print(result.decision.rationale)
    print("------------------------------------------------")
    print(f"Policy: {result.valuation.policy_type}")
    print(result.disclaimer)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_arguments(argv)
    vehicle_id = args.vehicle.strip()
    if not vehicle_id:
        print("ERROR: --vehicle must not be empty.", file=sys.stderr)
        return 2

    audio_path = args.audio.expanduser()
    try:
        validate_wav(str(audio_path))
    except (AudioValidationError, OSError) as error:
        print(f"ERROR: {audio_path} is not a readable WAV file: {error}", file=sys.stderr)
        return 2

    try:
        result = analyze_decision(
            audio_path=audio_path,
            vehicle_id=vehicle_id,
            base_wholesale_value=args.base_wholesale,
            copart_expected_gross=args.copart_gross,
            minimum_switch_advantage=args.minimum_switch_advantage,
        )
    except ModelNotReadyError as error:
        print(f"ERROR: local knock model is not ready: {error}", file=sys.stderr)
        return 1
    except (TypeError, ValueError) as error:
        print(f"ERROR: invalid decision input or model output: {error}", file=sys.stderr)
        return 2
    except Exception as error:
        print(f"ERROR: disposition decision failed: {error}", file=sys.stderr)
        return 1

    if args.json:
        print(result.model_dump_json(indent=2))
    else:
        _print_decision(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
