import { useState } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Activity,
  Layers,
  Sparkles,
} from 'lucide-react';
import type { DiagnosticResult } from '../types/acoustic';

interface DiagnosticPanelProps {
  diagnostic: DiagnosticResult;
  isAnalyzing?: boolean;
}

export const DiagnosticPanel: React.FC<DiagnosticPanelProps> = ({ diagnostic }) => {
  const [showBreakdown, setShowBreakdown] = useState(true);

  const score = diagnostic.mechanicalIntegrityScore;

  // Determine color scheme based on score
  let strokeColor = '#10b981'; // Green
  let textColor = 'text-emerald-400';
  let bgBadge = 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300';
  let statusIcon = <ShieldCheck className="w-6 h-6 text-emerald-400" />;

  if (score < 40) {
    strokeColor = '#f43f5e'; // Red
    textColor = 'text-rose-400';
    bgBadge = 'bg-rose-500/10 border-rose-500/30 text-rose-300';
    statusIcon = <ShieldAlert className="w-6 h-6 text-rose-400" />;
  } else if (score < 75) {
    strokeColor = '#f59e0b'; // Amber
    textColor = 'text-amber-400';
    bgBadge = 'bg-amber-500/10 border-amber-500/30 text-amber-300';
    statusIcon = <AlertTriangle className="w-6 h-6 text-amber-400" />;
  }

  // Circular gauge math (radius 42, circumference 263.89)
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="glass-panel rounded-2xl p-5 md:p-6 border border-slate-800 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-widest px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30">
            STEP 2 &bull; AI DIAGNOSTIC PANEL
          </span>
          <h2 className="text-base font-extrabold text-white mt-1 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            Mechanical Integrity & Fault Detection
          </h2>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-bold border ${bgBadge}`}>
          {diagnostic.primaryStatus} STATUS
        </span>
      </div>

      {/* Main Gauge & Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
        {/* Circular Metric Gauge */}
        <div className="flex flex-col items-center justify-center p-4 bg-slate-900/90 rounded-2xl border border-slate-800 relative shadow-inner">
          <div className="relative w-32 h-32 flex items-center justify-center">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r={radius}
                className="stroke-slate-800"
                strokeWidth="10"
                fill="transparent"
              />
              <circle
                cx="50"
                cy="50"
                r={radius}
                stroke={strokeColor}
                strokeWidth="10"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                fill="transparent"
                className="transition-all duration-1000 ease-out"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
              <span className={`text-3xl font-black font-mono tracking-tighter ${textColor}`}>
                {score}
              </span>
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                Integrity Score
              </span>
            </div>
          </div>
          <span className="text-xs text-slate-400 mt-2 font-medium">Out of 100 Mechanical Health</span>
        </div>

        {/* Status Summary & Detected Tags */}
        <div className="md:col-span-2 space-y-4">
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex items-start gap-3">
            <div className="p-2 rounded-lg bg-slate-800 shrink-0">{statusIcon}</div>
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Acoustic Neural Model Summary
              </span>
              <h3 className="text-base font-bold text-white mt-0.5">{diagnostic.statusSummary}</h3>
              <p className="text-xs text-slate-400 mt-1">
                APEX acoustic neural model analyzed spectral knock energy features across 5 seconds of
                idle telemetry.
              </p>
            </div>
          </div>

          {/* Detected Diagnostic Tags */}
          <div className="space-y-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5" />
              Detected Diagnostic Tags & Fault Logs
            </span>
            <div className="space-y-1.5">
              {diagnostic.tags.map((tag) => (
                <div
                  key={tag.id}
                  className={`flex items-center justify-between px-3.5 py-2 rounded-lg border text-xs font-medium ${
                    tag.type === 'critical'
                      ? 'bg-rose-950/40 border-rose-500/40 text-rose-200'
                      : tag.type === 'warning'
                      ? 'bg-amber-950/40 border-amber-500/40 text-amber-200'
                      : tag.type === 'success'
                      ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-200'
                      : 'bg-cyan-950/40 border-cyan-500/40 text-cyan-200'
                  }`}
                >
                  <span className="font-semibold">{tag.title}</span>
                  <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-slate-900/80 border border-slate-700 text-slate-300 font-bold">
                    Confidence: {tag.confidence}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Accordion Severity Breakdown */}
      <div className="border-t border-slate-800/80 pt-4">
        <button
          onClick={() => setShowBreakdown(!showBreakdown)}
          className="flex items-center justify-between w-full text-xs font-bold uppercase tracking-wider text-slate-300 hover:text-white transition-colors cursor-pointer py-1"
        >
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <span>Diagnostic Severity Breakdown (Click to {showBreakdown ? 'Collapse' : 'Expand'})</span>
          </div>
          {showBreakdown ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showBreakdown && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-3 pt-3 border-t border-slate-800/50">
            {/* Harmonic Balance */}
            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5">
              <span className="text-xs text-slate-400 font-semibold block">Harmonic Balance</span>
              <div className="flex items-baseline justify-between">
                <span className="text-lg font-bold font-mono text-white">
                  {diagnostic.breakdown.harmonicBalance}%
                </span>
                <span className="text-[10px] text-slate-400">Resonance Ratio</span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-cyan-400 h-full rounded-full transition-all duration-500"
                  style={{ width: `${diagnostic.breakdown.harmonicBalance}%` }}
                ></div>
              </div>
            </div>

            {/* High-Frequency Cyclic Noise */}
            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5">
              <span className="text-xs text-slate-400 font-semibold block">High-Frequency Cyclic Noise</span>
              <div className="flex items-baseline justify-between">
                <span className="text-base font-bold text-white">
                  {diagnostic.breakdown.cyclicNoiseLevel}
                </span>
                <span className="text-[10px] text-slate-400">Valve Train Chatter</span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    diagnostic.breakdown.cyclicNoiseLevel === 'High' ||
                    diagnostic.breakdown.cyclicNoiseLevel === 'Severe'
                      ? 'bg-rose-500'
                      : diagnostic.breakdown.cyclicNoiseLevel === 'Moderate'
                      ? 'bg-amber-400'
                      : 'bg-emerald-400'
                  }`}
                  style={{
                    width:
                      diagnostic.breakdown.cyclicNoiseLevel === 'High'
                        ? '85%'
                        : diagnostic.breakdown.cyclicNoiseLevel === 'Moderate'
                        ? '55%'
                        : '25%',
                  }}
                ></div>
              </div>
            </div>

            {/* Percussive Energy Spikes */}
            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5">
              <span className="text-xs text-slate-400 font-semibold block">Percussive Energy Spikes</span>
              <div className="flex items-baseline justify-between">
                <span className="text-xs font-bold text-white truncate">
                  {diagnostic.breakdown.percussiveSpikes}
                </span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    diagnostic.breakdown.percussiveSpikes.includes('Critical')
                      ? 'bg-rose-500'
                      : diagnostic.breakdown.percussiveSpikes.includes('Chatter')
                      ? 'bg-amber-400'
                      : 'bg-emerald-400'
                  }`}
                  style={{
                    width: diagnostic.breakdown.percussiveSpikes.includes('Critical')
                      ? '95%'
                      : diagnostic.breakdown.percussiveSpikes.includes('Chatter')
                      ? '50%'
                      : '15%',
                  }}
                ></div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
