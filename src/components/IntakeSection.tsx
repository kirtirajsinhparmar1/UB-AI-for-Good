import { useRef } from 'react';
import { AlertTriangle, CheckCircle2, Car, Loader2, Mic, Upload, Volume2 } from 'lucide-react';
import type { EconomicInputs, PresetId } from '../types/acoustic';
import { SAMPLE_VEHICLES } from '../hooks/useAcousticEngine';

interface IntakeSectionProps {
  selectedVehicleId: string;
  onVehicleChange: (vehicleId: string) => void;
  activePreset?: PresetId;
  onSelectPreset: (presetId: PresetId) => void;
  onFileUpload: (file: File) => void;
  isAnalyzing: boolean;
  audioFileName?: string;
  economics: EconomicInputs;
  onEconomicInputChange: (key: keyof EconomicInputs, value: number) => void;
  error: string | null;
}

const economicFields: { key: keyof EconomicInputs; label: string; min: number }[] = [
  { key: 'baseWholesaleValue', label: 'Base wholesale value', min: 0.01 },
  { key: 'copartExpectedGross', label: 'Copart expected gross', min: 0 },
  { key: 'minimumSwitchAdvantage', label: 'Switch advantage', min: 0 },
];

export const IntakeSection: React.FC<IntakeSectionProps> = ({
  selectedVehicleId,
  onVehicleChange,
  activePreset,
  onSelectPreset,
  onFileUpload,
  isAnalyzing,
  audioFileName,
  economics,
  onEconomicInputChange,
  error,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const submitFile = (file?: File) => {
    if (file && !isAnalyzing) onFileUpload(file);
  };

  const handleFileDrop = (event: React.DragEvent) => {
    event.preventDefault();
    submitFile(event.dataTransfer.files[0]);
  };

  return (
    <div className="glass-panel rounded-2xl p-5 md:p-6 shadow-2xl border border-slate-800 space-y-6">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-widest px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30">
            STEP 1 &bull; VEHICLE & ENGINE SOUND INTAKE
          </span>
          <h2 className="text-lg font-extrabold text-white mt-1">Select Vehicle & Engine Audio</h2>
        </div>

        <div className="flex items-center gap-3 bg-slate-900 p-2 rounded-xl border border-slate-800">
          <div className="p-2 rounded-lg bg-slate-800 text-cyan-400"><Car className="w-5 h-5" /></div>
          <div>
            <label htmlFor="vehicle-select" className="sr-only">Select Vehicle</label>
            <select
              id="vehicle-select"
              value={selectedVehicleId}
              onChange={(event) => onVehicleChange(event.target.value)}
              disabled={isAnalyzing}
              className="bg-slate-950 text-white font-bold text-xs md:text-sm border border-slate-700 rounded-lg px-3 py-1.5 focus:outline-none focus:border-cyan-500 cursor-pointer shadow-sm"
            >
              {SAMPLE_VEHICLES.map((vehicle) => (
                <option key={vehicle.id} value={vehicle.id}>{vehicle.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
            <Volume2 className="w-4 h-4 text-cyan-400" /> Real Demo Audio Samples
          </span>
          <span className="text-[11px] text-cyan-400 font-mono">Each sample is analyzed by the backend</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <button
            type="button"
            onClick={() => onSelectPreset('clean')}
            disabled={isAnalyzing}
            className={`flex items-center justify-between p-4 rounded-xl border transition-all cursor-pointer disabled:cursor-wait disabled:opacity-60 ${
              activePreset === 'clean'
                ? 'bg-emerald-950/70 border-emerald-500 text-emerald-300 shadow-lg shadow-emerald-950/60 ring-1 ring-emerald-500/50'
                : 'bg-slate-900/80 border-slate-800 text-slate-300 hover:border-slate-700'
            }`}
          >
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
              <div className="text-left">
                <span className="block font-bold text-white text-sm">Clean Engine Sample</span>
                <span className="text-xs text-emerald-400 font-medium">Vehicle A &bull; same demo economics</span>
              </div>
            </div>
            <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-300">WAV</span>
          </button>

          <button
            type="button"
            onClick={() => onSelectPreset('knocking')}
            disabled={isAnalyzing}
            className={`flex items-center justify-between p-4 rounded-xl border transition-all cursor-pointer disabled:cursor-wait disabled:opacity-60 ${
              activePreset === 'knocking'
                ? 'bg-rose-950/70 border-rose-500 text-rose-300 shadow-lg shadow-rose-950/60 ring-1 ring-rose-500/50'
                : 'bg-slate-900/80 border-slate-800 text-slate-300 hover:border-slate-700'
            }`}
          >
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
              <div className="text-left">
                <span className="block font-bold text-white text-sm">Knocking Engine Sample</span>
                <span className="text-xs text-rose-400 font-medium">Vehicle B &bull; same demo economics</span>
              </div>
            </div>
            <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-rose-500/20 text-rose-300">WAV</span>
          </button>
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-300">Disposition Economics</span>
          <span className="text-[11px] text-slate-400 font-mono">Same defaults for both demo samples</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {economicFields.map(({ key, label, min }) => (
            <label key={key} className="text-[11px] text-slate-400 font-semibold space-y-1">
              <span className="block">{label}</span>
              <div className="flex items-center rounded-lg bg-slate-950 border border-slate-800 focus-within:border-cyan-500 px-2.5">
                <span className="text-slate-500">$</span>
                <input
                  type="number"
                  min={min}
                  step="100"
                  value={economics[key]}
                  onChange={(event) => onEconomicInputChange(key, Number(event.target.value))}
                  disabled={isAnalyzing}
                  className="w-full min-w-0 bg-transparent text-white font-mono text-sm px-1.5 py-2 outline-none disabled:opacity-60"
                  aria-label={label}
                />
              </div>
            </label>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
        <div className="bg-slate-900/70 rounded-xl p-5 border border-slate-800 flex flex-col items-center justify-center text-center">
          <div className="p-3 rounded-full bg-slate-800 text-slate-500 mb-2"><Mic className="w-6 h-6" /></div>
          <span className="font-bold text-sm text-white">Live Microphone Capture</span>
          <p className="text-xs text-slate-400 mt-1 max-w-xs">Not enabled in this demo. Upload or select one of the WAV samples.</p>
        </div>

        <div
          onDragOver={(event) => event.preventDefault()}
          onDrop={handleFileDrop}
          onClick={() => !isAnalyzing && fileInputRef.current?.click()}
          className="bg-slate-900/60 hover:bg-slate-900/90 border-2 border-dashed border-slate-700 hover:border-cyan-500/80 rounded-xl p-5 flex flex-col items-center justify-center text-center cursor-pointer transition-all"
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={(event) => {
              submitFile(event.target.files?.[0]);
              event.target.value = '';
            }}
            accept=".wav,audio/wav,audio/x-wav"
            className="hidden"
            disabled={isAnalyzing}
          />
          <div className="p-3 rounded-full bg-slate-800 text-cyan-400 mb-2"><Upload className="w-5 h-5" /></div>
          <span className="font-bold text-sm text-slate-200">{audioFileName ? `File: ${audioFileName}` : 'Upload Engine .wav File'}</span>
          <p className="text-xs text-slate-400 mt-1">Drag & drop a WAV file or click to browse</p>
        </div>
      </div>

      {isAnalyzing && (
        <div role="status" className="flex items-center justify-center gap-3 p-3 bg-cyan-950/60 border border-cyan-500/40 rounded-xl text-cyan-300 text-xs font-semibold animate-pulse">
          <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
          <span>Analyzing engine acoustics & calculating disposition economics…</span>
        </div>
      )}
      {error && (
        <div role="alert" className="flex items-center gap-2 p-3 bg-rose-950/50 border border-rose-500/40 rounded-xl text-rose-200 text-xs font-semibold">
          <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};
