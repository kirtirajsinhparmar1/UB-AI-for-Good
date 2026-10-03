"""Compare ACV and Copart expected values and recommend a channel."""

from dataclasses import dataclass
import math
from typing import Literal


RecommendedChannel = Literal["ACV", "COPART", "REVIEW"]
DecisionStrength = Literal["weak", "strong"]


@dataclass(frozen=True)
class ChannelRouteResult:
    """Expected values and the resulting routing recommendation."""

    acv_expected_value: float
    copart_expected_value: float
    value_difference: float
    recommended_channel: RecommendedChannel
    decision_strength: DecisionStrength
    minimum_switch_advantage: float
    rationale: str


def _format_currency(amount: float) -> str:
    """Format whole-dollar values compactly and fractional dollars to cents."""
    if amount % 1 == 0:
        return f"${amount:,.0f}"
    return f"${amount:,.2f}"


def _validate_nonnegative_finite(name: str, value: float) -> None:
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be a finite, nonnegative value")


def route_vehicle(
    acv_expected_value: float,
    copart_expected_value: float,
    minimum_switch_advantage: float = 500,
) -> ChannelRouteResult:
    """Recommend a channel from the two supplied values and switch threshold."""
    inputs = (
        ("acv_expected_value", acv_expected_value),
        ("copart_expected_value", copart_expected_value),
        ("minimum_switch_advantage", minimum_switch_advantage),
    )
    for name, value in inputs:
        _validate_nonnegative_finite(name, value)

    value_difference = copart_expected_value - acv_expected_value
    if not math.isfinite(value_difference):
        raise ValueError("calculated value difference must be finite")

    threshold = _format_currency(minimum_switch_advantage)
    if value_difference >= minimum_switch_advantage:
        recommended_channel: RecommendedChannel = "COPART"
        decision_strength: DecisionStrength = "strong"
        if value_difference == 0:
            rationale = "Expected values are equal; the $0 routing threshold assigns ties to Copart."
        else:
            rationale = (
                f"Copart expected value exceeds adjusted ACV value by "
                f"{_format_currency(value_difference)}, meeting the {threshold} "
                "routing threshold."
            )
    elif value_difference <= -minimum_switch_advantage:
        recommended_channel = "ACV"
        decision_strength = "strong"
        rationale = (
            f"Adjusted ACV value exceeds Copart expected value by "
            f"{_format_currency(-value_difference)}, meeting the {threshold} "
            "routing threshold."
        )
    else:
        recommended_channel = "REVIEW"
        decision_strength = "weak"
        rationale = (
            f"Expected values differ by only "
            f"{_format_currency(abs(value_difference))}, below the {threshold} "
            "routing threshold, so manual review is recommended."
        )

    return ChannelRouteResult(
        acv_expected_value=acv_expected_value,
        copart_expected_value=copart_expected_value,
        value_difference=value_difference,
        recommended_channel=recommended_channel,
        decision_strength=decision_strength,
        minimum_switch_advantage=minimum_switch_advantage,
        rationale=rationale,
    )
