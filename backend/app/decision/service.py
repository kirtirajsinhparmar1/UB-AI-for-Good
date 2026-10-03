"""Compose local acoustic inference, prototype valuation, and channel routing."""

from pathlib import Path

from app.decision.models import (
    DecisionAcoustic,
    DecisionEconomics,
    DecisionRecommendation,
    DecisionResponse,
    DecisionValuation,
)
from app.model.knock_model import analyze_knock
from app.routing.channel_router import route_vehicle
from app.scoring.acoustic_score import score_acoustic_risk
from app.value.acoustic_value import compute_acoustic_value_delta


PROTOTYPE_DISCLAIMER = (
    "Prototype economic policy for hackathon demonstration; production values "
    "require empirical calibration."
)


def analyze_decision(
    *,
    audio_path: Path,
    vehicle_id: str,
    base_wholesale_value: float,
    copart_expected_gross: float,
    acv_costs: float = 0,
    copart_costs: float = 0,
    minimum_switch_advantage: float = 500,
) -> DecisionResponse:
    """Run one full decision from a validated local WAV and supplied estimates."""
    knock = analyze_knock(audio_path)
    score = score_acoustic_risk(knock.knock_probability)
    value_delta = compute_acoustic_value_delta(
        base_wholesale_value=base_wholesale_value,
        acoustic_risk_score=score.acoustic_risk_score,
    )
    route = route_vehicle(
        acv_expected_gross=value_delta.adjusted_wholesale_value,
        copart_expected_gross=copart_expected_gross,
        acv_costs=acv_costs,
        copart_costs=copart_costs,
        minimum_switch_advantage=minimum_switch_advantage,
    )

    return DecisionResponse(
        vehicle_id=vehicle_id,
        acoustic=DecisionAcoustic(
            acoustic_knock_score=score.acoustic_risk_score,
            risk_band=score.risk_band,
            model_name=knock.model_name,
        ),
        valuation=DecisionValuation(
            base_wholesale_value=value_delta.base_wholesale_value,
            acoustic_delta_pct=round(value_delta.delta_pct / 100, 8),
            acoustic_delta_amount=value_delta.delta_amount,
            adjusted_wholesale_value=value_delta.adjusted_wholesale_value,
            policy_type=value_delta.policy_type,
            policy_version=value_delta.policy_version,
            policy_note=value_delta.policy_note,
        ),
        economics=DecisionEconomics(
            acv_expected_gross=route.acv_expected_gross,
            acv_costs=route.acv_costs,
            acv_expected_net=route.acv_expected_net,
            copart_expected_gross=route.copart_expected_gross,
            copart_costs=route.copart_costs,
            copart_expected_net=route.copart_expected_net,
            net_difference=route.net_difference,
        ),
        decision=DecisionRecommendation(
            recommended_channel=route.recommended_channel,
            decision_strength=route.decision_strength,
            minimum_switch_advantage=route.minimum_switch_advantage,
            rationale=route.rationale,
        ),
        disclaimer=PROTOTYPE_DISCLAIMER,
    )
