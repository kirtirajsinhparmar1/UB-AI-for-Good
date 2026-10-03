"""Tests for direct ACV/Copart expected-value routing."""

import math

import pytest

from app.routing import ChannelRouteResult, route_vehicle


def test_clear_copart_win_uses_expected_values() -> None:
    result = route_vehicle(8_900, 10_600)

    assert result == ChannelRouteResult(
        acv_expected_value=8_900,
        copart_expected_value=10_600,
        value_difference=1_700,
        recommended_channel="COPART",
        decision_strength="strong",
        minimum_switch_advantage=500,
        rationale=(
            "Copart expected value exceeds adjusted ACV value by $1,700, "
            "meeting the $500 routing threshold."
        ),
    )


def test_clear_acv_win() -> None:
    result = route_vehicle(12_000, 11_000)

    assert result.value_difference == -1_000
    assert result.recommended_channel == "ACV"
    assert result.rationale == (
        "Adjusted ACV value exceeds Copart expected value by $1,000, meeting "
        "the $500 routing threshold."
    )


@pytest.mark.parametrize(
    ("acv_value", "copart_value", "expected_channel"),
    [
        (10_000, 10_500, "COPART"),
        (10_500, 10_000, "ACV"),
    ],
)
def test_exact_threshold_routes_to_stronger_channel(
    acv_value: float, copart_value: float, expected_channel: str
) -> None:
    result = route_vehicle(acv_value, copart_value)

    assert result.recommended_channel == expected_channel
    assert result.decision_strength == "strong"


def test_difference_inside_review_zone_recommends_manual_review() -> None:
    result = route_vehicle(10_400, 10_650)

    assert result.value_difference == 250
    assert result.recommended_channel == "REVIEW"
    assert result.decision_strength == "weak"
    assert result.rationale == (
        "Expected values differ by only $250, below the $500 routing "
        "threshold, so manual review is recommended."
    )


def test_equal_values_recommend_review() -> None:
    result = route_vehicle(10_000, 10_000)

    assert result.value_difference == 0
    assert result.recommended_channel == "REVIEW"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"acv_expected_value": -1},
        {"copart_expected_value": -1},
        {"minimum_switch_advantage": -1},
    ],
)
def test_negative_inputs_are_rejected(kwargs: dict[str, float]) -> None:
    values = {"acv_expected_value": 1_000, "copart_expected_value": 1_000}
    values.update(kwargs)

    with pytest.raises(ValueError):
        route_vehicle(**values)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"acv_expected_value": math.nan},
        {"copart_expected_value": math.inf},
        {"minimum_switch_advantage": math.inf},
    ],
)
def test_non_finite_inputs_are_rejected(kwargs: dict[str, float]) -> None:
    values = {"acv_expected_value": 1_000, "copart_expected_value": 1_000}
    values.update(kwargs)

    with pytest.raises(ValueError):
        route_vehicle(**values)


def test_zero_threshold_routes_equal_values_to_copart_by_rule_order() -> None:
    result = route_vehicle(1_000, 1_000, minimum_switch_advantage=0)

    assert result.recommended_channel == "COPART"
    assert result.decision_strength == "strong"
    assert result.rationale == (
        "Expected values are equal; the $0 routing threshold assigns ties to Copart."
    )


def test_output_is_deterministic() -> None:
    first = route_vehicle(8_900, 10_600)
    second = route_vehicle(8_900, 10_600)

    assert first == second
