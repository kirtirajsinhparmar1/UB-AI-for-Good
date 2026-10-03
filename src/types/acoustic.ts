export type InspectionMode = 'mobile' | 'pro';

export type PresetId = 'healthy' | 'rod_knock' | 'lifter_tick';

export interface Vehicle {
  id: string;
  name: string;
  mileage: string;
  vin: string;
  engine: string;
  baseBookValue: number;      // Wholesale baseline (Year/Make/Model/Mileage)
  copartSalvageFloor: number;  // Intact salvage part-out floor
}

export interface SeverityBreakdown {
  harmonicBalance: number;
  cyclicNoiseLevel: 'Low' | 'Moderate' | 'High' | 'Severe';
  percussiveSpikes: 'Normal Baseline' | 'Minor Chatter' | 'Critical Failure Detected';
}

export interface DiagnosticTag {
  id: string;
  type: 'critical' | 'warning' | 'info' | 'success';
  title: string;
  confidence: number;
}

export interface DiagnosticResult {
  mechanicalIntegrityScore: number;
  primaryStatus: 'HEALTHY' | 'WARNING' | 'CRITICAL';
  statusSummary: string;
  tags: DiagnosticTag[];
  breakdown: SeverityBreakdown;
  knockFrequencyPeakHz: number;
}

export interface AcvValuation {
  condition: string;
  baseBookValue: number;
  acousticStatus: string;
  acousticDelta: number; // +1200, -850, or -5800
  acousticDeltaLabel: string;
  adjustedAcvWholesale: number; // baseBookValue + acousticDelta
  sellerReserveGuidance: number; // Same as adjustedAcvWholesale
  arbitrationRiskPercent: string; // '< 0.8%', '4.5%', '92.4%'
  arbitrationRiskLevel: 'Low' | 'Moderate' | 'Extreme';
  isRecommended: boolean;
  recommendationNote: string;
}

export interface CopartValuation {
  condition: string;
  copartSalvageFloor: number;
  transmissionVal: number;
  bodyPanelsVal: number;
  catalyticScrapVal: number;
  isRecommended: boolean;
  recommendationNote: string;
}

export interface ValuationComparison {
  acv: AcvValuation;
  copart: CopartValuation;
  winningRoute: 'ACV' | 'COPART';
  netDifference: number; // Adjusted ACV - Copart Floor (or Copart Floor - Adjusted ACV)
  actionMessage: string;
}

export interface AnalysisState {
  isAnalyzing: boolean;
  mode: InspectionMode;
  selectedVehicle: Vehicle;
  activePreset: PresetId;
  diagnostic: DiagnosticResult;
  valuation: ValuationComparison;
  isRecording: boolean;
  recordingSeconds: number;
  audioSource: 'preset' | 'mic' | 'upload';
  audioFileName?: string;
}
