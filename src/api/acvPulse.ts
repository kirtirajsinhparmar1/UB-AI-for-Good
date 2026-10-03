import type { DecisionResponse, EconomicInputs } from '../types/acoustic';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/+$/, '');

export class AnalysisApiError extends Error {
  readonly status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = 'AnalysisApiError';
    this.status = status;
  }
}

export async function analyzeDecision(
  vehicleId: string,
  audioFile: File,
  economics: EconomicInputs,
): Promise<DecisionResponse> {
  const form = new FormData();
  form.append('vehicle_id', vehicleId);
  form.append('audio_file', audioFile, audioFile.name);
  form.append('base_wholesale_value', String(economics.baseWholesaleValue));
  form.append('copart_expected_gross', String(economics.copartExpectedGross));
  form.append('minimum_switch_advantage', String(economics.minimumSwitchAdvantage));

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/v1/decision/analyze`, {
      method: 'POST',
      body: form,
    });
  } catch {
    throw new AnalysisApiError(`Cannot reach the analysis service at ${API_BASE_URL}. Start the backend and try again.`);
  }

  if (!response.ok) {
    const messages: Record<number, string> = {
      400: 'Invalid vehicle, audio, or economic input. Check the WAV file and values.',
      413: 'This audio file is too large. Choose a smaller WAV file.',
      422: 'A required analysis input is missing or malformed.',
      500: 'The backend could not complete the analysis. Please try again.',
      503: 'The local acoustic model is unavailable. Check the backend model setup.',
    };
    throw new AnalysisApiError(messages[response.status] || `Analysis failed (HTTP ${response.status}).`, response.status);
  }

  return (await response.json()) as DecisionResponse;
}
