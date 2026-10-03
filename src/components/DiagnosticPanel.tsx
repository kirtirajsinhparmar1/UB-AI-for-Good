import { AlertTriangle, Activity, ShieldCheck, Sparkles } from 'lucide-react';
import type { DecisionResponse } from '../types/acoustic';

interface DiagnosticPanelProps {
  result: DecisionResponse | null;
  isAnalyzing: boolean;
}

export const DiagnosticPanel: React.FC<DiagnosticPanelProps> = ({ result, isAnalyzing }) => {
  const score = result?.acoustic.acoustic_knock_score ?? 0;
  const risk = result?.acoustic.risk_band;
  const palette = risk === 'high'
    ? { stroke: '#f43f5e', text: 'text-rose-400', badge: 'bg-rose-500/10 border-rose-500/30 text-rose-300' }
    : risk === 'medium'
      ? { stroke: '#f59e0b', text: 'text-amber-400', badge: 'bg-amber-500/10 border-amber-500/30 text-amber-300' }
      : { stroke: '#10b981', text: 'text-emerald-400', badge: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' };
  const radius = 42;
  const circumference = 2 * Math.PI * radius;

  return (
    <div className="glass-panel rounded-2xl p-5 md:p-6 border border-slate-800 space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-widest px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30">STEP 2 &bull; ACOUSTIC ANALYSIS</span>
          <h2 className="text-base font-extrabold text-white mt-1 flex items-center gap-2"><Sparkles className="w-4 h-4 text-cyan-400" /> Engine Sound Assessment</h2>
        </div>
        {risk && (
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-bold uppercase tracking-wider ${palette.badge}`}>
            {risk === 'low' ? <ShieldCheck className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
            Acoustic Risk: {risk}
          </div>
        )}
      </div>

      <div className="flex flex-col sm:flex-row items-center gap-6">
        <div className="relative w-36 h-36 shrink-0">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100" aria-label={result ? `Acoustic Knock Score ${score} out of 100` : 'Waiting for WAV audio'}>
            <circle cx="50" cy="50" r={radius} fill="none" stroke="#1e293b" strokeWidth="8" />
            {result && <circle cx="50" cy="50" r={radius} fill="none" stroke={palette.stroke} strokeWidth="8" strokeDasharray={circumference} strokeDashoffset={circumference - (score / 100) * circumference} strokeLinecap="round" className="transition-all duration-700" />}
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-4xl font-black font-mono ${result ? palette.text : 'text-slate-600'}`}>{result ? score : '—'}</span>
            <span className="text-[10px] text-slate-400 uppercase tracking-widest mt-1">of 100</span>
          </div>
        </div>
        <div className="flex-1 space-y-4 w-full">
          <div>
            <span className="text-xs text-slate-400 font-semibold block">Acoustic Knock Score</span>
            <p className="text-sm text-slate-300 mt-1">A model score derived from the uploaded engine audio. It is not a calibrated probability or a mechanical diagnosis.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-xs text-slate-400 font-semibold block">Acoustic Risk</span>
              <span className={`text-lg font-bold uppercase ${result ? palette.text : 'text-slate-600'}`}>{risk ?? 'Waiting'}</span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-xs text-slate-400 font-semibold block">Inference Model</span>
              <span className="text-sm font-bold text-white break-words">{result?.acoustic.model_name ?? (isAnalyzing ? 'Running…' : '—')}</span>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Activity className="w-3.5 h-3.5 text-cyan-500" />
            {result ? `Vehicle ${result.vehicle_id} · backend result` : 'Select a real WAV sample or upload an engine recording to begin.'}
          </div>
        </div>
      </div>
    </div>
  );
};
