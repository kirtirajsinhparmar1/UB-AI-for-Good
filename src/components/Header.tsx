import { Smartphone, Radio, Zap, ShieldCheck, Activity } from 'lucide-react';
import type { InspectionMode } from '../types/acoustic';


interface HeaderProps {
  mode: InspectionMode;
  onModeChange: (mode: InspectionMode) => void;
  isAnalyzing: boolean;
}

export const Header: React.FC<HeaderProps> = ({ mode, onModeChange, isAnalyzing }) => {
  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 bg-slate-950/90 px-4 lg:px-8 py-3.5 backdrop-blur-md">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Branding */}
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-600 text-slate-950 shadow-lg shadow-emerald-500/20">
            <Activity className="w-6 h-6 stroke-[2.5]" />
            {isAnalyzing && (
              <span className="absolute -top-1 -right-1 flex h-3.5 w-3.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3.5 w-3.5 bg-cyan-500"></span>
              </span>
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                ACV Pulse
                <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono font-medium tracking-wide">
                  v2.4 AI Arbitrage
                </span>
              </h1>
            </div>
            <p className="text-xs text-slate-400 font-medium">
              Acoustic AI Arbitrage & Dynamic Reserve Engine
            </p>
          </div>
        </div>

        {/* Inspection Mode Switcher */}
        <div className="flex items-center bg-slate-900/90 p-1 rounded-xl border border-slate-800 shadow-inner">
          <button
            onClick={() => onModeChange('mobile')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 cursor-pointer ${
              mode === 'mobile'
                ? 'bg-slate-800 text-cyan-300 shadow border border-cyan-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Smartphone className="w-3.5 h-3.5" />
            <span>ClearCar Mobile Scan (Consumer / Phone Mic)</span>
          </button>

          <button
            onClick={() => onModeChange('pro')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 cursor-pointer ${
              mode === 'pro'
                ? 'bg-gradient-to-r from-emerald-950 to-slate-800 text-emerald-300 shadow border border-emerald-500/40'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Radio className="w-3.5 h-3.5 text-emerald-400" />
            <span>ACV Pro Telematics (APEX Contact Sensor + VIPER OBD-II)</span>
          </button>
        </div>

        {/* Dynamic Status Pill */}
        <div className="flex items-center">
          {mode === 'mobile' ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-medium">
              <Zap className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
              <span>Audio Signal Fidelity: Phone Mic (Confidence Cap: 85%)</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/40 text-emerald-300 text-xs font-medium glow-acv">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Acoustic Diagnostic: APEX Pro Sensor (Fidelity: 99.4%)</span>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
