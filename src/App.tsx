import { Code, Database } from 'lucide-react';
import { AudioVisualizer } from './components/AudioVisualizer';
import { DiagnosticPanel } from './components/DiagnosticPanel';
import { Header } from './components/Header';
import { IntakeSection } from './components/IntakeSection';
import { RoutingValuation } from './components/RoutingValuation';
import { Toast } from './components/Toast';
import { useAcousticEngine } from './hooks/useAcousticEngine';

export function App() {
  const { state, setVehicle, updateEconomicInput, selectPreset, handleFileUpload, toastMessage } = useAcousticEngine();
  const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/+$/, '');

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col selection:bg-cyan-500 selection:text-slate-950">
      <Header isAnalyzing={state.isAnalyzing} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 lg:px-8 py-6 space-y-6">
        <IntakeSection
          selectedVehicleId={state.selectedVehicleId}
          onVehicleChange={setVehicle}
          activePreset={state.activePreset}
          onSelectPreset={selectPreset}
          onFileUpload={handleFileUpload}
          isAnalyzing={state.isAnalyzing}
          audioFileName={state.audioFile?.name}
          economics={state.economics}
          onEconomicInputChange={updateEconomicInput}
          error={state.error}
        />

        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
          <div className="xl:col-span-6 space-y-6">
            <AudioVisualizer audioFile={state.audioFile} isAnalyzing={state.isAnalyzing} />
          </div>
          <div className="xl:col-span-6 space-y-6">
            <DiagnosticPanel result={state.result} isAnalyzing={state.isAnalyzing} />
          </div>
        </div>

        <RoutingValuation result={state.result} />

        <div className="glass-panel rounded-2xl p-4 md:p-5 border border-slate-800/80 bg-slate-950/60 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400"><Code className="w-5 h-5" /></div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-bold text-white">Live acoustic disposition analysis</span>
                <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-mono font-semibold">POST /v1/decision/analyze</span>
              </div>
              <p className="text-slate-400 mt-0.5">WAV audio and editable economics are sent to the local backend for scoring, valuation and routing.</p>
            </div>
          </div>
          <div className="flex items-center gap-2 self-stretch md:self-auto justify-end">
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 font-mono">
              <Database className="w-3.5 h-3.5 text-cyan-400" /><span>{apiBaseUrl}</span>
            </div>
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-800/80 py-4 px-4 text-center text-xs text-slate-400 bg-slate-950">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>ACV Pulse &copy; 2026 — Acoustic disposition decision support demo</span>
          <span className="font-mono">Local inference &bull; Prototype economics</span>
        </div>
      </footer>

      <Toast message={toastMessage} />
    </div>
  );
}

export default App;
