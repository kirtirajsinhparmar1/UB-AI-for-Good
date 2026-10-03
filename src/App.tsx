import { Header } from './components/Header';
import { IntakeSection } from './components/IntakeSection';
import { AudioVisualizer } from './components/AudioVisualizer';
import { DiagnosticPanel } from './components/DiagnosticPanel';
import { RoutingValuation } from './components/RoutingValuation';
import { Toast } from './components/Toast';
import { useAcousticEngine } from './hooks/useAcousticEngine';
import { Cpu, Code, Database } from 'lucide-react';


export function App() {
  const {
    state,
    setInspectionMode,
    setVehicle,
    selectPreset,
    startRecording,
    handleFileUpload,
    toastMessage,
  } = useAcousticEngine();

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col selection:bg-cyan-500 selection:text-slate-950">
      {/* Top Header & Mode Toggle */}
      <Header
        mode={state.mode}
        onModeChange={setInspectionMode}
        isAnalyzing={state.isAnalyzing}
      />

      {/* Main Content Dashboard Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 lg:px-8 py-6 space-y-6">
        {/* Section 1: Intake & Audio Capture */}
        <IntakeSection
          selectedVehicle={state.selectedVehicle}
          onVehicleChange={setVehicle}
          activePreset={state.activePreset}
          onSelectPreset={selectPreset}
          isRecording={state.isRecording}
          recordingSeconds={state.recordingSeconds}
          onStartRecording={startRecording}
          onFileUpload={handleFileUpload}
          isAnalyzing={state.isAnalyzing}
          audioSource={state.audioSource}
          audioFileName={state.audioFileName}
        />

        {/* Section 2 & 3: Audio Visualizer + Diagnostic Panel */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
          <div className="xl:col-span-6 space-y-6">
            <AudioVisualizer
              activePreset={state.activePreset}
              isAnalyzing={state.isAnalyzing}
              knockPeakHz={state.diagnostic.knockFrequencyPeakHz}
            />
          </div>

          <div className="xl:col-span-6 space-y-6">
            <DiagnosticPanel
              diagnostic={state.diagnostic}
              isAnalyzing={state.isAnalyzing}
            />
          </div>
        </div>

        {/* Section 4: Dynamic Routing & Valuation Comparison Cards */}
        <RoutingValuation valuation={state.valuation} />

        {/* Section 5: Hackathon Backend Integration & API Hook Details Banner */}
        <div className="glass-panel rounded-2xl p-4 md:p-5 border border-slate-800/80 bg-slate-950/60 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <Code className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-white">Backend Integration Hook (`useAcousticEngine.ts`)</span>
                <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-mono font-semibold">
                  `POST /api/analyze-audio` Ready
                </span>
              </div>
              <p className="text-slate-400 mt-0.5">
                Frontend encapsulates mock analysis state & delay. Ready to swap out with Python/Flask backend endpoint (`POST /api/analyze-audio`).
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-stretch md:self-auto justify-end">
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 font-mono">
              <Database className="w-3.5 h-3.5 text-cyan-400" />
              <span>APEX Neural Model: Online</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 font-mono">
              <Cpu className="w-3.5 h-3.5 text-emerald-400" />
              <span>Latency: 1.2s (Simulated)</span>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-4 px-4 text-center text-xs text-slate-400 bg-slate-950">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>
            ACV Pulse &copy; 2026 — Autonomous Acoustic Arbitrage Engine (ACV Auctions & Copart Hackathon Demo)
          </span>
          <div className="flex items-center gap-3 text-slate-400 font-mono">
            <span>ClearCar Mobile AI</span>
            <span>&bull;</span>
            <span>APEX Pro Telematics</span>
          </div>
        </div>
      </footer>

      {/* Toast Notification Container */}
      <Toast message={toastMessage} />
    </div>
  );
}

export default App;
