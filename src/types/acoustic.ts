export type PresetId = 'clean' | 'knocking';
export type RiskBand = 'low' | 'medium' | 'high';
export type RecommendedChannel = 'ACV' | 'COPART' | 'REVIEW';

export interface Vehicle {
  id: string;
  name: string;
}

export interface EconomicInputs {
  baseWholesaleValue: number;
  copartExpectedGross: number;
  minimumSwitchAdvantage: number;
}

export interface DecisionResponse {
  vehicle_id: string;
  acoustic: {
    acoustic_knock_score: number;
    risk_band: RiskBand;
    model_name: string;
  };
  valuation: {
    base_wholesale_value: number;
    acoustic_delta_pct: number;
    acoustic_delta_amount: number;
    adjusted_wholesale_value: number;
    policy_type: string;
    policy_version: string;
    policy_note: string;
  };
  economics: {
    acv_expected_value: number;
    copart_expected_value: number;
    value_difference: number;
  };
  decision: {
    recommended_channel: RecommendedChannel;
    decision_strength: 'weak' | 'strong';
    minimum_switch_advantage: number;
    rationale: string;
  };
  disclaimer: string;
}

export interface AnalysisState {
  isAnalyzing: boolean;
  selectedVehicleId: string;
  activePreset?: PresetId;
  audioFile?: File;
  result: DecisionResponse | null;
  error: string | null;
  economics: EconomicInputs;
}
