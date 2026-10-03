import { Activity, ArrowRight, Database, Radio } from 'lucide-react';

interface HeaderProps {
  isAnalyzing: boolean;
}

export const Header: React.FC<HeaderProps> = ({ isAnalyzing }) => (
  <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 bg-slate-950/90 px-4 lg:px-8 py-3.5 backdrop-blur-md">
    <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-600 text-slate-950 shadow-lg shadow-emerald-500/20">
          <Activity className="w-6 h-6 stroke-[2.5]" />
          {isAnalyzing && <span className="absolute -top-1 -right-1 flex h-3.5 w-3.5"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" /><span className="relative inline-flex rounded-full h-3.5 w-3.5 bg-cyan-500" /></span>}
        </div>
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            ACV Pulse
            <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono font-medium tracking-wide">Acoustic Disposition</span>
          </h1>
          <p className="text-xs text-slate-400 font-medium">Engine audio analysis & channel economics</p>
        </div>
      </div>

      <div className="flex items-center bg-slate-900/90 p-1 rounded-xl border border-slate-800 shadow-inner text-xs font-semibold text-slate-300">
        <div className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-800 text-cyan-300 border border-cyan-500/30">
          <Radio className="w-3.5 h-3.5" /> WAV Audio
        </div>
        <ArrowRight className="w-3.5 h-3.5 mx-2 text-slate-500" />
        <div className="flex items-center gap-2 px-3.5 py-2">
          <Activity className="w-3.5 h-3.5 text-emerald-400" /> Value & Routing
        </div>
      </div>

      <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-200 text-xs font-medium">
        <Database className={`w-3.5 h-3.5 ${isAnalyzing ? 'animate-pulse' : 'text-cyan-400'}`} />
        <span>{isAnalyzing ? 'Backend analysis running' : 'Backend WAV analysis'}</span>
      </div>
    </div>
  </header>
);
