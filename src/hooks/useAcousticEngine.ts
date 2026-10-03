import { useCallback, useRef, useState } from 'react';
import { analyzeDecision } from '../api/acvPulse';
import type { AnalysisState, EconomicInputs, PresetId, Vehicle } from '../types/acoustic';

export const SAMPLE_VEHICLES: Vehicle[] = [
  { id: 'VEHICLE-A', name: 'Vehicle A · Clean audio' },
  { id: 'VEHICLE-B', name: 'Vehicle B · Knocking audio' },
];

const DEFAULT_ECONOMICS: EconomicInputs = {
  baseWholesaleValue: 15000,
  copartExpectedGross: 14200,
  minimumSwitchAdvantage: 500,
};

const SAMPLE_FILES: Record<PresetId, string> = {
  clean: 'car_clean_0006.wav',
  knocking: 'car_knocking_0003.wav',
};

export function useAcousticEngine() {
  const [state, setState] = useState<AnalysisState>({
    isAnalyzing: false,
    selectedVehicleId: SAMPLE_VEHICLES[0].id,
    result: null,
    error: null,
    economics: DEFAULT_ECONOMICS,
  });
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const requestInProgress = useRef(false);

  const showToast = useCallback((message: string) => {
    setToastMessage(message);
    window.setTimeout(() => setToastMessage(null), 4000);
  }, []);

  const setVehicle = useCallback((selectedVehicleId: string) => {
    setState((current) => ({ ...current, selectedVehicleId }));
  }, []);

  const updateEconomicInput = useCallback((key: keyof EconomicInputs, value: number) => {
    setState((current) => ({
      ...current,
      economics: { ...current.economics, [key]: value },
    }));
  }, []);

  const runAnalysis = useCallback(async (audioFile: File, activePreset?: PresetId, vehicleId = state.selectedVehicleId) => {
    if (requestInProgress.current) return;
    requestInProgress.current = true;
    setState((current) => ({
      ...current,
      isAnalyzing: true,
      error: null,
      result: null,
      audioFile,
      activePreset,
    }));

    try {
      const result = await analyzeDecision(vehicleId, audioFile, state.economics);
      setState((current) => ({ ...current, isAnalyzing: false, result }));
      showToast(`${result.decision.recommended_channel} recommended for ${result.vehicle_id}`);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Analysis failed. Please try again.';
      setState((current) => ({ ...current, isAnalyzing: false, error: message }));
      showToast(message);
    } finally {
      requestInProgress.current = false;
    }
  }, [showToast, state.economics, state.selectedVehicleId]);

  const selectPreset = useCallback(async (presetId: PresetId) => {
    const filename = SAMPLE_FILES[presetId];
    const vehicleId = presetId === 'clean' ? SAMPLE_VEHICLES[0].id : SAMPLE_VEHICLES[1].id;
    setState((current) => ({ ...current, selectedVehicleId: vehicleId }));
    try {
      const response = await fetch(`${import.meta.env.BASE_URL}demo/${filename}`);
      if (!response.ok) throw new Error('The selected demo WAV could not be loaded.');
      const audioFile = new File([await response.blob()], filename, { type: 'audio/wav' });
      await runAnalysis(audioFile, presetId, vehicleId);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'The selected demo WAV could not be loaded.';
      setState((current) => ({ ...current, error: message }));
      showToast(message);
    }
  }, [runAnalysis, showToast]);

  const handleFileUpload = useCallback((audioFile: File) => {
    if (!audioFile.name.toLowerCase().endsWith('.wav')) {
      const message = 'Please choose a WAV audio file.';
      setState((current) => ({ ...current, error: message }));
      showToast(message);
      return;
    }
    void runAnalysis(audioFile);
  }, [runAnalysis, showToast]);

  return { state, setVehicle, updateEconomicInput, selectPreset, handleFileUpload, toastMessage };
}
