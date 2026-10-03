"""Compare supplied ACV and Copart economics and recommend a channel.

This module is intentionally independent of pricing, vehicle condition, and
market data. Callers provide gross expected values and costs that have already
been estimated upstream.
"""

from dataclasses import dataclass
import math
from typing import Literal


RecommendedChannel = Literal["ACV", "COPART", "REVIEW"]
DecisionStrength = Literal["weak", "strong"]


@dataclass(frozen=True)
class ChannelRouteResult:
    """Transparent net economics and the resulting routing recommendation."""

    acv_expected_gross: float
    acv_costs: float
    acv_expected_net: float
    copart_expected_gross: float
    copart_costs: float
    copart_expected_net: float
    net_difference: float
    recommended_channel: RecommendedChannel
    decision_strength: DecisionStrength
    minimum_switch_advantage: float
    rationale: str


def _format_currency(amount: float) -> str:
    """Format whole-dollar economics compactly and fractional dollars to cents."""
    if amount % 1 == 0:
        return f"${amount:,.0f}"
    return f"${amount:,.2f}"


def _validate_nonnegative_finite(name: str, value: float) -> None:
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be a finite, nonnegative value")


def route_vehicle(
    acv_expected_gross: float,
    copart_expected_gross: float,
    acv_costs: float = 0,
    copart_costs: float = 0,
    minimum_switch_advantage: float = 500,
) -> ChannelRouteResult:
    """Recommend ACV, COPART, or REVIEW from caller-supplied economics.

    ``decision_strength`` is ``"strong"`` only when the net difference meets
    the configured routing threshold. It describes this deterministic margin
    rule, not statistical confidence in the upstream estimates.
    """
    inputs = (
        ("acv_expected_gross", acv_expected_gross),
        ("copart_expected_gross", copart_expected_gross),
        ("acv_costs", acv_costs),
        ("copart_costs", copart_costs),
        ("minimum_switch_advantage", minimum_switch_advantage),
    )
    for name, value in inputs:
        _validate_nonnegative_finite(name, value)

    acv_expected_net = acv_expected_gross - acv_costs
    copart_expected_net = copart_expected_gross - copart_costs
    net_difference = copart_expected_net - acv_expected_net
    if not all(
        math.isfinite(value)
        for value in (acv_expected_net, copart_expected_net, net_difference)
    ):
        raise ValueError("calculated net values and difference must be finite")

    threshold = _format_currency(minimum_switch_advantage)
    if net_difference >= minimum_switch_advantage:
        recommended_channel: RecommendedChannel = "COPART"
        decision_strength: DecisionStrength = "strong"
        if net_difference == 0:
            rationale = (
                "Expected net values are equal; the $0 routing threshold assigns "
                "ties to Copart."
            )
        else:
            rationale = (
                f"Copart expected net exceeds ACV expected net by "
                f"{_format_currency(net_difference)}, meeting the {threshold} "
                "routing threshold."
            )
    elif net_difference <= -minimum_switch_advantage:
        recommended_channel = "ACV"
        decision_strength = "strong"
        rationale = (
            f"ACV expected net exceeds Copart expected net by "
            f"{_format_currency(-net_difference)}, meeting the {threshold} "
            "routing threshold."
        )
    else:
        recommended_channel = "REVIEW"
        decision_strength = "weak"
        rationale = (
            f"Expected net values differ by only "
            f"{_format_currency(abs(net_difference))}, below the {threshold} "
            "routing threshold, so manual review is recommended."
        )

    return ChannelRouteResult(
        acv_expected_gross=acv_expected_gross,
        acv_costs=acv_costs,
        acv_expected_net=acv_expected_net,
        copart_expected_gross=copart_expected_gross,
        copart_costs=copart_costs,
        copart_expected_net=copart_expected_net,
        net_difference=net_difference,
        recommended_channel=recommended_channel,
        decision_strength=decision_strength,
        minimum_switch_advantage=minimum_switch_advantage,
        rationale=rationale,
    )
