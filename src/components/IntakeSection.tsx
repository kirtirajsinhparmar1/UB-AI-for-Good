import { useRef } from 'react';
import {
  Car,
  Mic,
  Upload,
  CheckCircle2,
  AlertTriangle,
  Flame,
  Volume2,
  Loader2,
} from 'lucide-react';

import type { PresetId, Vehicle } from '../types/acoustic';
import { SAMPLE_VEHICLES } from '../hooks/useAcousticEngine';

interface IntakeSectionProps {
  selectedVehicle: Vehicle;
  onVehicleChange: (vehicleId: string) => void;
  activePreset: PresetId;
  onSelectPreset: (presetId: PresetId) => void;
  isRecording: boolean;
  recordingSeconds: number;
  onStartRecording: () => void;
  onFileUpload: (fileName: string) => void;
  isAnalyzing: boolean;
  audioSource: 'preset' | 'mic' | 'upload';
  audioFileName?: string;
}

export const IntakeSection: React.FC<IntakeSectionProps> = ({
  selectedVehicle,
  onVehicleChange,
  activePreset,
  onSelectPreset,
  isRecording,
  recordingSeconds,
  onStartRecording,
  onFileUpload,
  isAnalyzing,
  audioSource,
  audioFileName,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      onFileUpload(file.name);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileUpload(e.target.files[0].name);
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-5 md:p-6 shadow-2xl border border-slate-800 space-y-6">
      {/* Step Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-widest px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30">
            STEP 1 &bull; VEHICLE & ENGINE SOUND INTAKE
          </span>
          <h2 className="text-lg font-extrabold text-white mt-1">Select Inspection Vehicle & Capture Audio</h2>
        </div>

        {/* Vehicle Selection Dropdown */}
        <div className="flex items-center gap-3 bg-slate-900 p-2 rounded-xl border border-slate-800">
          <div className="p-2 rounded-lg bg-slate-800 text-cyan-400">
            <Car className="w-5 h-5" />
          </div>
          <div>
            <label htmlFor="vehicle-select" className="sr-only">
              Select Vehicle
            </label>
            <select
              id="vehicle-select"
              value={selectedVehicle.id}
              onChange={(e) => onVehicleChange(e.target.value)}
              className="bg-slate-950 text-white font-bold text-xs md:text-sm border border-slate-700 rounded-lg px-3 py-1.5 focus:outline-none focus:border-cyan-500 cursor-pointer shadow-sm"
            >
              {SAMPLE_VEHICLES.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name} (Base: ${v.baseBookValue.toLocaleString()} | Salvage: ${v.copartSalvageFloor.toLocaleString()})
                </option>
              ))}
            </select>
          </div>
          <div className="hidden lg:flex items-center gap-2 text-xs font-mono text-slate-300 border-l border-slate-800 pl-3">
            <span className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 font-bold">
              Base: ${selectedVehicle.baseBookValue.toLocaleString()}
            </span>
            <span className="px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/30 text-rose-300 font-bold">
              Salvage Floor: ${selectedVehicle.copartSalvageFloor.toLocaleString()}
            </span>
          </div>
        </div>
      </div>


      {/* Quick-Demo Preset Buttons Section */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
            <Volume2 className="w-4 h-4 text-cyan-400" />
            Live Demo Audio Presets (Click to Test AI Engine)
          </span>
          <span className="text-[11px] text-cyan-400 font-mono">Select a preset to test live routing</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Healthy Preset */}
          <button
            onClick={() => onSelectPreset('healthy')}
            disabled={isAnalyzing || isRecording}
            className={`flex items-center justify-between p-4 rounded-xl border transition-all cursor-pointer ${
              activePreset === 'healthy' && audioSource === 'preset'
                ? 'bg-emerald-950/70 border-emerald-500 text-emerald-300 shadow-lg shadow-emerald-950/60 ring-1 ring-emerald-500/50 scale-[1.01]'
                : 'bg-slate-900/80 border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-850'
            }`}
          >
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
              <div className="text-left">
                <span className="block font-bold text-white text-sm">Healthy Engine Idle</span>
                <span className="text-xs text-emerald-400 font-medium">Pass &bull; ACV Auctions Win</span>
              </div>
            </div>
            <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-300">
              94 Health
            </span>
          </button>

          {/* Rod Knock Preset */}
          <button
            onClick={() => onSelectPreset('rod_knock')}
            disabled={isAnalyzing || isRecording}
            className={`flex items-center justify-between p-4 rounded-xl border transition-all cursor-pointer ${
              activePreset === 'rod_knock' && audioSource === 'preset'
                ? 'bg-rose-950/70 border-rose-500 text-rose-300 shadow-lg shadow-rose-950/60 ring-1 ring-rose-500/50 scale-[1.01]'
                : 'bg-slate-900/80 border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-850'
            }`}
          >
            <div className="flex items-center gap-3">
              <Flame className="w-5 h-5 text-rose-400 shrink-0" />
              <div className="text-left">
                <span className="block font-bold text-white text-sm">Severe Rod Knock</span>
                <span className="text-xs text-rose-400 font-medium">Fail &bull; Copart Salvage Win</span>
              </div>
            </div>
            <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-rose-500/20 text-rose-300">
              28 Health
            </span>
          </button>

          {/* Lifter Tick Preset */}
          <button
            onClick={() => onSelectPreset('lifter_tick')}
            disabled={isAnalyzing || isRecording}
            className={`flex items-center justify-between p-4 rounded-xl border transition-all cursor-pointer ${
              activePreset === 'lifter_tick' && audioSource === 'preset'
                ? 'bg-amber-950/70 border-amber-500 text-amber-300 shadow-lg shadow-amber-950/60 ring-1 ring-amber-500/50 scale-[1.01]'
                : 'bg-slate-900/80 border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-850'
            }`}
          >
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
              <div className="text-left">
                <span className="block font-bold text-white text-sm">Hydraulic Lifter Tick</span>
                <span className="text-xs text-amber-400 font-medium">Warning &bull; ACV Auctions Win</span>
              </div>
            </div>
            <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-amber-500/20 text-amber-300">
              62 Health
            </span>
          </button>
        </div>
      </div>

      {/* Audio Capture Options (Mic Record vs File Upload) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
        {/* Record 5s Engine Idle */}
        <div className="bg-slate-900/90 rounded-xl p-5 border border-slate-800 flex flex-col items-center justify-center text-center relative overflow-hidden">
          <div className="relative mb-3">
            {isRecording && (
              <span className="absolute -inset-4 rounded-full bg-cyan-500/30 animate-ping"></span>
            )}
            <button
              onClick={onStartRecording}
              disabled={isRecording || isAnalyzing}
              className={`relative z-10 w-16 h-16 rounded-full flex items-center justify-center transition-all duration-300 shadow-xl cursor-pointer ${
                isRecording
                  ? 'bg-rose-600 text-white shadow-rose-600/50 scale-105'
                  : 'bg-gradient-to-tr from-cyan-500 to-emerald-500 text-slate-950 hover:scale-105 shadow-cyan-500/30'
              }`}
            >
              {isRecording ? (
                <span className="font-mono text-xl font-bold">{recordingSeconds}s</span>
              ) : (
                <Mic className="w-7 h-7 stroke-[2.5]" />
              )}
            </button>
          </div>

          <span className="font-bold text-sm text-white">
            {isRecording ? `Listening to Engine Idle...` : 'Click to Record 5s Live Engine Idle'}
          </span>
          <p className="text-xs text-slate-400 mt-1 max-w-xs">
            Captures real-time phone/APEX microphone acoustic frequencies for FFT analysis.
          </p>
        </div>

        {/* File Dropzone */}
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleFileDrop}
          onClick={() => fileInputRef.current?.click()}
          className="bg-slate-900/60 hover:bg-slate-900/90 border-2 border-dashed border-slate-700 hover:border-cyan-500/80 rounded-xl p-5 flex flex-col items-center justify-center text-center cursor-pointer transition-all"
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            accept=".wav,.mp3,.m4a"
            className="hidden"
          />

          <div className="p-3 rounded-full bg-slate-800 text-cyan-400 mb-2">
            <Upload className="w-5 h-5" />
          </div>
          <span className="font-bold text-sm text-slate-200">
            {audioFileName ? `File: ${audioFileName}` : 'Upload Engine .wav File'}
          </span>
          <p className="text-xs text-slate-400 mt-1">
            Drag & drop uncompressed .wav audio file or click to browse
          </p>
        </div>
      </div>

      {/* Analysis Status Progress Spinner */}
      {isAnalyzing && (
        <div className="flex items-center justify-center gap-3 p-3 bg-cyan-950/60 border border-cyan-500/40 rounded-xl text-cyan-300 text-xs font-semibold animate-pulse">
          <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
          <span>Analyzing FFT Spectrogram (1-3 kHz Knock Band Peak Analysis)...</span>
        </div>
      )}
    </div>
  );
};
