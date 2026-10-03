"""Deterministic wholesale-value deltas using a configurable demo policy."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from app.scoring.acoustic_score import risk_band_for_score


@dataclass(frozen=True)
class AcousticValueBreakpoint:
    """One acoustic-risk score and its adjustment in percentage points."""

    risk_score: int
    delta_pct: float


@dataclass(frozen=True)
class AcousticValuePolicy:
    """Human-readable assumptions used to convert risk into a value delta."""

    version: str
    policy_type: str
    note: str
    breakpoints: tuple[AcousticValueBreakpoint, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.version, str) or not self.version.strip():
            raise ValueError("Policy version must not be empty.")
        if not isinstance(self.policy_type, str) or not self.policy_type.strip():
            raise ValueError("Policy type must clearly identify a demo or prototype policy.")
        normalized_policy_type = self.policy_type.casefold()
        if not any(label in normalized_policy_type for label in ("demo", "prototype")):
            raise ValueError("Policy type must clearly identify a demo or prototype policy.")
        if any(label in normalized_policy_type for label in ("production", "certified", "validated")):
            raise ValueError("Policy type must not claim production, certification, or validation.")
        if not isinstance(self.note, str) or not self.note.strip():
            raise ValueError("Policy note must not be empty.")
        if len(self.breakpoints) < 2:
            raise ValueError("Policy must contain at least two breakpoints.")

        previous_score = -1
        previous_delta = math.inf
        for point in self.breakpoints:
            if not isinstance(point.risk_score, int) or isinstance(point.risk_score, bool):
                raise ValueError("Breakpoint risk scores must be integers.")
            if not 0 <= point.risk_score <= 100:
                raise ValueError("Breakpoint risk scores must be between 0 and 100.")
            if point.risk_score <= previous_score:
                raise ValueError("Breakpoint risk scores must be strictly increasing.")
            if (
                not isinstance(point.delta_pct, (int, float))
                or isinstance(point.delta_pct, bool)
                or not math.isfinite(point.delta_pct)
                or point.delta_pct < -100
            ):
                raise ValueError("Breakpoint adjustments must be finite and at least -100%.")
            if point.delta_pct > previous_delta:
                raise ValueError("Value adjustments must not increase as risk increases.")
            previous_score = point.risk_score
            previous_delta = point.delta_pct

        if self.breakpoints[0].risk_score != 0 or self.breakpoints[-1].risk_score != 100:
            raise ValueError("Policy breakpoints must cover the full 0–100 risk range.")


@dataclass(frozen=True)
class AcousticValueDeltaResult:
    base_wholesale_value: float
    acoustic_risk_score: int
    risk_band: str
    delta_pct: float
    delta_amount: float
    adjusted_wholesale_value: float
    policy_version: str
    policy_type: str
    policy_note: str
    rationale: str


def load_default_demo_policy() -> AcousticValuePolicy:
    """Load the bundled, explicitly illustrative demo policy from JSON."""
    policy_path = Path(__file__).with_name("demo_policy.json")
    policy_data = json.loads(policy_path.read_text(encoding="utf-8"))
    return _policy_from_data(policy_data)


def compute_acoustic_value_delta(
    base_wholesale_value: float,
    acoustic_risk_score: int,
    policy: AcousticValuePolicy | None = None,
) -> AcousticValueDeltaResult:
    """Apply a prototype policy to a baseline wholesale value.

    The returned delta is an illustrative economic adjustment, not a diagnosis
    or a representation of an ACV production pricing rule.
    """
    if not isinstance(base_wholesale_value, (int, float)) or isinstance(base_wholesale_value, bool):
        raise ValueError("Base wholesale value must be a finite number greater than zero.")
    if not math.isfinite(base_wholesale_value) or base_wholesale_value <= 0:
        raise ValueError("Base wholesale value must be a finite number greater than zero.")
    if not isinstance(acoustic_risk_score, int) or isinstance(acoustic_risk_score, bool):
        raise ValueError("Acoustic risk score must be an integer between 0 and 100.")
    if not 0 <= acoustic_risk_score <= 100:
        raise ValueError("Acoustic risk score must be between 0 and 100.")

    selected_policy = policy if policy is not None else load_default_demo_policy()
    if not isinstance(selected_policy, AcousticValuePolicy):
        raise ValueError("Policy must be an AcousticValuePolicy instance.")

    delta_pct = round(_interpolate_delta_pct(acoustic_risk_score, selected_policy), 4)
    delta_amount = round(float(base_wholesale_value) * delta_pct / 100, 2)
    adjusted_value = max(round(float(base_wholesale_value) + delta_amount, 2), 0.0)
    risk_band = risk_band_for_score(acoustic_risk_score)

    if delta_pct > 0:
        rationale = "Low acoustic risk supports a modest prototype value adjustment."
    elif delta_pct == 0:
        rationale = "Acoustic risk is neutral under the configured prototype policy."
    else:
        rationale = "Elevated acoustic risk increases the expected mechanical-risk discount under this prototype policy."

    return AcousticValueDeltaResult(
        base_wholesale_value=float(base_wholesale_value),
        acoustic_risk_score=acoustic_risk_score,
        risk_band=risk_band,
        delta_pct=delta_pct,
        delta_amount=delta_amount,
        adjusted_wholesale_value=adjusted_value,
        policy_version=selected_policy.version,
        policy_type=selected_policy.policy_type,
        policy_note=selected_policy.note,
        rationale=rationale,
    )


def _interpolate_delta_pct(score: int, policy: AcousticValuePolicy) -> float:
    for left, right in zip(policy.breakpoints, policy.breakpoints[1:]):
        if score <= right.risk_score:
            fraction = (score - left.risk_score) / (right.risk_score - left.risk_score)
            return left.delta_pct + fraction * (right.delta_pct - left.delta_pct)
    return policy.breakpoints[-1].delta_pct


def _policy_from_data(data: object) -> AcousticValuePolicy:
    if not isinstance(data, dict):
        raise ValueError("Demo policy JSON must contain an object.")
    try:
        raw_points = data["breakpoints"]
        if not isinstance(raw_points, list):
            raise ValueError("Policy breakpoints must be a list.")
        points = tuple(
            AcousticValueBreakpoint(
                risk_score=point["risk_score"],
                delta_pct=point["delta_pct"],
            )
            for point in raw_points
        )
        return AcousticValuePolicy(
            version=data["version"],
            policy_type=data["policy_type"],
            note=data["note"],
            breakpoints=points,
        )
    except (KeyError, TypeError) as exc:
        raise ValueError("Demo policy JSON is missing valid policy fields.") from exc
