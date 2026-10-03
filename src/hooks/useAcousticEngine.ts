import { useState, useCallback } from 'react';
import type {
  InspectionMode,
  PresetId,
  Vehicle,
  AnalysisState,
  DiagnosticResult,
  ValuationComparison,
} from '../types/acoustic';

export const SAMPLE_VEHICLES: Vehicle[] = [
  {
    id: 'f150',
    name: '2019 Ford F-150 SuperCrew',
    mileage: '84k mi',
    vin: '1FTFW1E84KFA12093',
    engine: '3.5L EcoBoost V6',
    baseBookValue: 21500,
    copartSalvageFloor: 9800,
  },
  {
    id: 'civic',
    name: '2020 Honda Civic EX',
    mileage: '52k mi',
    vin: '2HGFC2F74LH549102',
    engine: '1.5L Turbo I4',
    baseBookValue: 14200,
    copartSalvageFloor: 6100,
  },
  {
    id: 'bmw',
    name: '2017 BMW 330i xDrive',
    mileage: '98k mi',
    vin: 'WBA8B9C54HNT83109',
    engine: '2.0L TwinPower I4',
    baseBookValue: 11000,
    copartSalvageFloor: 5400,
  },
];

const PRESET_DIAGNOSTICS: Record<PresetId, DiagnosticResult> = {
  healthy: {
    mechanicalIntegrityScore: 94,
    primaryStatus: 'HEALTHY',
    statusSummary: 'Normal Combustion Resonance & Mechanical Harmony',
    knockFrequencyPeakHz: 1420,
    tags: [
      {
        id: 't1',
        type: 'success',
        title: 'APEX Certified: Zero Rod Knock Detected (Confidence: 97%)',
        confidence: 97,
      },
      {
        id: 't2',
        type: 'info',
        title: 'OBD-II Telematics: Clean ECU Fault Log (No Active DTC)',
        confidence: 99,
      },
      {
        id: 't3',
        type: 'info',
        title: 'Harmonic Balance Optimal (Resonance Index: 0.96)',
        confidence: 94,
      },
    ],
    breakdown: {
      harmonicBalance: 96,
      cyclicNoiseLevel: 'Low',
      percussiveSpikes: 'Normal Baseline',
    },
  },

  rod_knock: {
    mechanicalIntegrityScore: 28,
    primaryStatus: 'CRITICAL',
    statusSummary: 'Catastrophic Bottom-End Bearing Fatigue & Rod Knock Detected',
    knockFrequencyPeakHz: 2480,
    tags: [
      {
        id: 't1',
        type: 'critical',
        title: 'Critical: Bottom-End Bearing Fatigue / Rod Knock Detected (Confidence: 89%)',
        confidence: 89,
      },
      {
        id: 't2',
        type: 'warning',
        title: 'Secondary: OBD-II P0300 Random/Multiple Cylinder Misfire Detected',
        confidence: 91,
      },
      {
        id: 't3',
        type: 'critical',
        title: 'Percussive Energy Spike: 4.8x Baseline (2.48 kHz Peak)',
        confidence: 95,
      },
    ],
    breakdown: {
      harmonicBalance: 42,
      cyclicNoiseLevel: 'High',
      percussiveSpikes: 'Critical Failure Detected',
    },
  },

  lifter_tick: {
    mechanicalIntegrityScore: 62,
    primaryStatus: 'WARNING',
    statusSummary: 'Top-End Valve Train Friction & Hydraulic Lifter Bleed-off',
    knockFrequencyPeakHz: 3850,
    tags: [
      {
        id: 't1',
        type: 'warning',
        title: 'Warning: Hydraulic Lifter Tick / Valve Train Noise (Confidence: 82%)',
        confidence: 82,
      },
      {
        id: 't2',
        type: 'info',
        title: 'OBD-II: P0302 Cylinder 2 Balance Contribution Warning',
        confidence: 86,
      },
      {
        id: 't3',
        type: 'success',
        title: 'Rod Bearing Integrity: Intact (Zero 1-3 kHz Knock Impulse)',
        confidence: 93,
      },
    ],
    breakdown: {
      harmonicBalance: 74,
      cyclicNoiseLevel: 'Moderate',
      percussiveSpikes: 'Minor Chatter',
    },
  },
};

export function calculateWaterfallValuation(
  vehicle: Vehicle,
  presetId: PresetId
): ValuationComparison {
  const basePrice = vehicle.baseBookValue;
  const floorPrice = vehicle.copartSalvageFloor;

  // Compute component floor breakdown proportional to floor
  const transVal = Math.round(floorPrice * 0.35);
  const bodyVal = Math.round(floorPrice * 0.42);
  const scrapVal = floorPrice - transVal - bodyVal;

  if (presetId === 'healthy') {
    const delta = 1200;
    const adjustedAcv = basePrice + delta;
    const netDiff = adjustedAcv - floorPrice;

    return {
      winningRoute: 'ACV',
      netDifference: netDiff,
      actionMessage: `RECOMMENDED ACTION: LIST ON ACV WHOLESALE. Vehicle captures +$${netDiff.toLocaleString()} higher margin as a running wholesale unit.`,
      acv: {
        condition: 'Clean Wholesale Run (Verified Powertrain)',
        baseBookValue: basePrice,
        acousticStatus: 'Verified Powertrain Integrity',
        acousticDelta: delta,
        acousticDeltaLabel: '+$1,200 (Certified Sound Premium)',
        adjustedAcvWholesale: adjustedAcv,
        sellerReserveGuidance: adjustedAcv,
        arbitrationRiskPercent: '< 0.8%',
        arbitrationRiskLevel: 'Low',
        isRecommended: true,
        recommendationNote: `RECOMMENDED: List on ACV Auctions at $${adjustedAcv.toLocaleString()} Reserve (+$1,200 APEX Verified Premium).`,
      },
      copart: {
        condition: 'Functional Vehicle (Component Harvest)',
        copartSalvageFloor: floorPrice,
        transmissionVal: transVal,
        bodyPanelsVal: bodyVal,
        catalyticScrapVal: scrapVal,
        isRecommended: false,
        recommendationNote: `Sub-Optimal Route: Whole-car wholesale on ACV yields +$${netDiff.toLocaleString()} higher net return.`,
      },
    };
  } else if (presetId === 'lifter_tick') {
    const delta = -850;
    const adjustedAcv = basePrice + delta;
    const netDiff = adjustedAcv - floorPrice;

    return {
      winningRoute: 'ACV',
      netDifference: netDiff,
      actionMessage: `RECOMMENDED ACTION: LIST ON ACV WHOLESALE. Vehicle captures +$${netDiff.toLocaleString()} higher margin with disclosed top-end valve tick.`,
      acv: {
        condition: 'Minor Mechanical Wear / Top-End Service',
        baseBookValue: basePrice,
        acousticStatus: 'Top-End Valvetrain Noise',
        acousticDelta: delta,
        acousticDeltaLabel: '-$850 (Valvetrain Wear Deduction)',
        adjustedAcvWholesale: adjustedAcv,
        sellerReserveGuidance: adjustedAcv,
        arbitrationRiskPercent: '4.5%',
        arbitrationRiskLevel: 'Moderate',
        isRecommended: true,
        recommendationNote: `RECOMMENDED: List on ACV Auctions at $${adjustedAcv.toLocaleString()} Reserve with Disclosed Valve Tick.`,
      },
      copart: {
        condition: 'Component Salvage Option',
        copartSalvageFloor: floorPrice,
        transmissionVal: transVal,
        bodyPanelsVal: bodyVal,
        catalyticScrapVal: scrapVal,
        isRecommended: false,
        recommendationNote: `Unnecessary Salvage Loss: Vehicle retains strong dealer market demand on ACV.`,
      },
    };
  } else {
    // Severe Rod Knock
    const delta = -5800;
    const adjustedAcv = basePrice + delta;

    if (adjustedAcv > floorPrice) {
      const netDiff = adjustedAcv - floorPrice;
      return {
        winningRoute: 'ACV',
        netDifference: netDiff,
        actionMessage: `RECOMMENDED ACTION: LIST ON ACV WHOLESALE. Vehicle captures +$${netDiff.toLocaleString()} higher margin despite engine replacement deduction.`,
        acv: {
          condition: 'Rebuildable / Major Engine Replacement Needed',
          baseBookValue: basePrice,
          acousticStatus: 'Catastrophic Bottom-End Knock Detected',
          acousticDelta: delta,
          acousticDeltaLabel: '-$5,800 (Powertrain Defect Deduction)',
          adjustedAcvWholesale: adjustedAcv,
          sellerReserveGuidance: adjustedAcv,
          arbitrationRiskPercent: '92.4%',
          arbitrationRiskLevel: 'Extreme',
          isRecommended: true,
          recommendationNote: `RECOMMENDED: List on ACV Wholesale at $${adjustedAcv.toLocaleString()} Reserve with Disclosed Blown Engine.`,
        },
        copart: {
          condition: 'Mechanical Total Loss (Component Harvest)',
          copartSalvageFloor: floorPrice,
          transmissionVal: transVal,
          bodyPanelsVal: bodyVal,
          catalyticScrapVal: scrapVal,
          isRecommended: false,
          recommendationNote: `Sub-Optimal: Whole-car wholesale yields +$${netDiff.toLocaleString()} higher return.`,
        },
      };
    } else {
      // Adjusted ACV <= Copart Salvage Floor (e.g. BMW 330i: $11,000 - $5,800 = $5,200 <= $5,400 Copart Floor)
      const netDiff = floorPrice - adjustedAcv;
      return {
        winningRoute: 'COPART',
        netDifference: netDiff,
        actionMessage: `RECOMMENDED ACTION: DIVERT TO COPART SALVAGE. Selling as salvage yields +$${netDiff.toLocaleString()} more net return than reconditioning a blown motor.`,
        acv: {
          condition: 'Rebuildable / Major Engine Replacement Needed',
          baseBookValue: basePrice,
          acousticStatus: 'Catastrophic Bottom-End Knock Detected',
          acousticDelta: delta,
          acousticDeltaLabel: '-$5,800 (Powertrain Defect Deduction)',
          adjustedAcvWholesale: adjustedAcv,
          sellerReserveGuidance: adjustedAcv,
          arbitrationRiskPercent: '92.4%',
          arbitrationRiskLevel: 'Extreme',
          isRecommended: false,
          recommendationNote: `UNFAVORABLE WHOLESALE YIELD: Adjusted ACV value ($${adjustedAcv.toLocaleString()}) falls below Copart salvage floor ($${floorPrice.toLocaleString()}).`,
        },
        copart: {
          condition: 'Mechanical Total Loss (Component Harvest)',
          copartSalvageFloor: floorPrice,
          transmissionVal: transVal,
          bodyPanelsVal: bodyVal,
          catalyticScrapVal: scrapVal,
          isRecommended: true,
          recommendationNote: `RECOMMENDED: Divert to Copart Salvage Yard — Yields +$${netDiff.toLocaleString()} more net return than reconditioning a blown motor.`,
        },
      };
    }
  }
}

export function useAcousticEngine() {
  const initialVehicle = SAMPLE_VEHICLES[2]; // Default to BMW 330i to showcase Copart diversion on Rod Knock
  const initialPreset: PresetId = 'rod_knock';

  const [state, setState] = useState<AnalysisState>({
    isAnalyzing: false,
    mode: 'mobile',
    selectedVehicle: initialVehicle,
    activePreset: initialPreset,
    diagnostic: PRESET_DIAGNOSTICS.rod_knock,
    valuation: calculateWaterfallValuation(initialVehicle, initialPreset),
    isRecording: false,
    recordingSeconds: 0,
    audioSource: 'preset',
  });

  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = useCallback((msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 4000);
  }, []);

  // Switch inspection mode (Mobile vs Pro Telematics)
  const setInspectionMode = useCallback(
    (mode: InspectionMode) => {
      setState((prev) => {
        const isPro = mode === 'pro';
        const updatedTags = prev.diagnostic.tags.map((tag) => ({
          ...tag,
          confidence: isPro ? Math.min(99, tag.confidence + 8) : Math.min(85, tag.confidence),
        }));

        return {
          ...prev,
          mode,
          diagnostic: {
            ...prev.diagnostic,
            tags: updatedTags,
          },
        };
      });

      showToast(
        mode === 'pro'
          ? 'Switched to APEX Pro Telematics (Fidelity: 99.4%)'
          : 'Switched to ClearCar Mobile Scan (Confidence Cap: 85%)'
      );
    },
    [showToast]
  );

  // Switch vehicle
  const setVehicle = useCallback(
    (vehicleId: string) => {
      const v = SAMPLE_VEHICLES.find((item) => item.id === vehicleId) || SAMPLE_VEHICLES[0];
      setState((prev) => {
        const newValuation = calculateWaterfallValuation(v, prev.activePreset);
        return {
          ...prev,
          selectedVehicle: v,
          valuation: newValuation,
        };
      });
      showToast(`Selected ${v.name} (Base Wholesale: $${v.baseBookValue.toLocaleString()})`);
    },
    [showToast]
  );

  // Load preset with simulated AI delay
  const selectPreset = useCallback(
    (presetId: PresetId) => {
      setState((prev) => ({ ...prev, isAnalyzing: true, activePreset: presetId }));

      setTimeout(() => {
        setState((prev) => {
          const diag = PRESET_DIAGNOSTICS[presetId];
          const val = calculateWaterfallValuation(prev.selectedVehicle, presetId);
          return {
            ...prev,
            isAnalyzing: false,
            audioSource: 'preset',
            audioFileName: undefined,
            diagnostic: diag,
            valuation: val,
          };
        });

        const titles: Record<PresetId, string> = {
          healthy: 'Healthy Engine Idle Analyzed - Waterfall Delta: +$1,200',
          rod_knock: 'Severe Rod Knock Detected - Waterfall Delta: -$5,800',
          lifter_tick: 'Hydraulic Lifter Tick Detected - Waterfall Delta: -$850',
        };

        showToast(titles[presetId]);
      }, 800);
    },
    [showToast]
  );

  // Trigger simulated 5s recording
  const startRecording = useCallback(() => {
    if (state.isRecording || state.isAnalyzing) return;

    setState((prev) => ({
      ...prev,
      isRecording: true,
      recordingSeconds: 5,
    }));

    showToast('Recording 5s Engine Idle via Microphone...');

    let timer = 5;
    const interval = setInterval(() => {
      timer -= 1;
      if (timer <= 0) {
        clearInterval(interval);
        setState((prev) => ({
          ...prev,
          isRecording: false,
          recordingSeconds: 0,
          isAnalyzing: true,
          audioSource: 'mic',
        }));

        setTimeout(() => {
          setState((prev) => {
            const diag = PRESET_DIAGNOSTICS.rod_knock;
            const val = calculateWaterfallValuation(prev.selectedVehicle, 'rod_knock');
            return {
              ...prev,
              isAnalyzing: false,
              diagnostic: diag,
              valuation: val,
            };
          });
          showToast('Live Audio Stream Processed — Waterfall Delta & Arbitrage Recalibrated!');
        }, 800);
      } else {
        setState((prev) => ({ ...prev, recordingSeconds: timer }));
      }
    }, 1000);
  }, [state.isRecording, state.isAnalyzing, showToast]);

  // Simulated file upload dropzone handler
  const handleFileUpload = useCallback(
    (fileName: string) => {
      setState((prev) => ({
        ...prev,
        isAnalyzing: true,
        audioSource: 'upload',
        audioFileName: fileName,
      }));

      showToast(`Uploaded audio: ${fileName} - Analyzing spectral knock signatures...`);

      setTimeout(() => {
        setState((prev) => {
          const diag = PRESET_DIAGNOSTICS.healthy;
          const val = calculateWaterfallValuation(prev.selectedVehicle, 'healthy');
          return {
            ...prev,
            isAnalyzing: false,
            diagnostic: diag,
            valuation: val,
          };
        });
        showToast(`Analysis Complete for ${fileName}: Verified Powertrain (+ $1,200 Delta).`);
      }, 800);
    },
    [showToast]
  );

  return {
    state,
    setInspectionMode,
    setVehicle,
    selectPreset,
    startRecording,
    handleFileUpload,
    toastMessage,
  };
}
