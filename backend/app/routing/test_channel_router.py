"""Tests for transparent ACV/Copart economic routing."""

import math

import pytest

from app.routing import ChannelRouteResult, route_vehicle


def test_clear_copart_win_uses_net_economics() -> None:
    result = route_vehicle(8_900, 10_600, acv_costs=500, copart_costs=900)

    assert result == ChannelRouteResult(
        acv_expected_gross=8_900,
        acv_costs=500,
        acv_expected_net=8_400,
        copart_expected_gross=10_600,
        copart_costs=900,
        copart_expected_net=9_700,
        net_difference=1_300,
        recommended_channel="COPART",
        decision_strength="strong",
        minimum_switch_advantage=500,
        rationale=(
            "Copart expected net exceeds ACV expected net by $1,300, meeting "
            "the $500 routing threshold."
        ),
    )


def test_clear_acv_win() -> None:
    result = route_vehicle(12_000, 11_000, acv_costs=400, copart_costs=800)

    assert result.acv_expected_net == 11_600
    assert result.copart_expected_net == 10_200
    assert result.net_difference == -1_400
    assert result.recommended_channel == "ACV"
    assert result.rationale == (
        "ACV expected net exceeds Copart expected net by $1,400, meeting the "
        "$500 routing threshold."
    )


@pytest.mark.parametrize(
    ("acv_gross", "copart_gross", "expected_channel"),
    [
        (10_000, 10_500, "COPART"),
        (10_500, 10_000, "ACV"),
    ],
)
def test_exact_threshold_routes_to_economically_stronger_channel(
    acv_gross: float, copart_gross: float, expected_channel: str
) -> None:
    result = route_vehicle(acv_gross, copart_gross)

    assert result.recommended_channel == expected_channel
    assert result.decision_strength == "strong"


def test_difference_inside_review_zone_recommends_manual_review() -> None:
    result = route_vehicle(10_400, 10_650)

    assert result.net_difference == 250
    assert result.recommended_channel == "REVIEW"
    assert result.decision_strength == "weak"
    assert result.rationale == (
        "Expected net values differ by only $250, below the $500 routing "
        "threshold, so manual review is recommended."
    )


def test_equal_economics_recommends_review() -> None:
    result = route_vehicle(10_000, 10_000)

    assert result.net_difference == 0
    assert result.recommended_channel == "REVIEW"


def test_zero_costs_are_allowed_and_preserved() -> None:
    result = route_vehicle(1_000, 1_600)

    assert result.acv_costs == 0
    assert result.copart_costs == 0
    assert result.acv_expected_net == 1_000
    assert result.copart_expected_net == 1_600
    assert result.recommended_channel == "COPART"


def test_costs_can_change_recommendation() -> None:
    no_costs = route_vehicle(10_000, 10_700)
    with_copart_costs = route_vehicle(10_000, 10_700, copart_costs=250)

    assert no_costs.recommended_channel == "COPART"
    assert with_copart_costs.copart_expected_net == 10_450
    assert with_copart_costs.net_difference == 450
    assert with_copart_costs.recommended_channel == "REVIEW"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"acv_expected_gross": -1},
        {"copart_expected_gross": -1},
        {"acv_costs": -1},
        {"copart_costs": -1},
        {"minimum_switch_advantage": -1},
    ],
)
def test_negative_inputs_are_rejected(kwargs: dict[str, float]) -> None:
    values = {"acv_expected_gross": 1_000, "copart_expected_gross": 1_000}
    values.update(kwargs)

    with pytest.raises(ValueError):
        route_vehicle(**values)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"acv_expected_gross": math.nan},
        {"copart_expected_gross": math.inf},
        {"acv_costs": math.inf},
        {"copart_costs": math.nan},
        {"minimum_switch_advantage": math.inf},
    ],
)
def test_non_finite_inputs_are_rejected(kwargs: dict[str, float]) -> None:
    values = {"acv_expected_gross": 1_000, "copart_expected_gross": 1_000}
    values.update(kwargs)

    with pytest.raises(ValueError):
        route_vehicle(**values)


def test_net_values_may_be_negative_when_costs_exceed_gross() -> None:
    result = route_vehicle(100, 500, acv_costs=200, copart_costs=700)

    assert result.acv_expected_net == -100
    assert result.copart_expected_net == -200
    assert result.net_difference == -100
    assert result.recommended_channel == "REVIEW"


def test_zero_threshold_routes_equal_economics_to_copart_by_rule_order() -> None:
    result = route_vehicle(1_000, 1_000, minimum_switch_advantage=0)

    assert result.recommended_channel == "COPART"
    assert result.decision_strength == "strong"
    assert result.rationale == (
        "Expected net values are equal; the $0 routing threshold assigns ties "
        "to Copart."
    )


def test_output_is_deterministic() -> None:
    first = route_vehicle(8_900, 10_600, acv_costs=500, copart_costs=900)
    second = route_vehicle(8_900, 10_600, acv_costs=500, copart_costs=900)

    assert first == second
