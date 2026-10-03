import { useEffect, useRef } from 'react';
import { Sliders, Activity, Flame } from 'lucide-react';
import type { PresetId } from '../types/acoustic';


interface AudioVisualizerProps {
  activePreset: PresetId;
  isAnalyzing: boolean;
  knockPeakHz: number;
}

export const AudioVisualizer: React.FC<AudioVisualizerProps> = ({
  activePreset,
  isAnalyzing,
  knockPeakHz,
}) => {
  const waveformRef = useRef<HTMLCanvasElement>(null);
  const spectrogramRef = useRef<HTMLCanvasElement>(null);

  // Render Oscilloscope Waveform Animation
  useEffect(() => {
    const canvas = waveformRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let phase = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Background grid lines
      ctx.strokeStyle = 'rgba(30, 41, 59, 0.5)';
      ctx.lineWidth = 1;
      const stepY = canvas.height / 4;
      for (let y = stepY; y < canvas.height; y += stepY) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
      }

      ctx.beginPath();
      ctx.lineWidth = 2;

      // Color scheme based on active preset
      if (activePreset === 'healthy') {
        ctx.strokeStyle = '#10b981'; // Emerald
      } else if (activePreset === 'rod_knock') {
        ctx.strokeStyle = '#f43f5e'; // Rose/Red
      } else {
        ctx.strokeStyle = '#f59e0b'; // Amber
      }

      const centerY = canvas.height / 2;
      phase += 0.08;

      for (let x = 0; x < canvas.width; x++) {
        let amp = 15;
        if (activePreset === 'rod_knock') {
          // Rod knock has sharp periodic percussive spikes
          amp = (x % 40 < 6 ? 45 : 12) * (isAnalyzing ? 1.5 : 1);
        } else if (activePreset === 'lifter_tick') {
          amp = (x % 20 < 4 ? 28 : 10) * (isAnalyzing ? 1.5 : 1);
        } else {
          amp = (Math.sin(x * 0.05 + phase) * 8 + 8) * (isAnalyzing ? 1.4 : 1);
        }

        const y = centerY + Math.sin(x * 0.08 + phase) * amp;
        if (x === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [activePreset, isAnalyzing]);

  // Render Mel-Spectrogram Heatmap
  useEffect(() => {
    const canvas = spectrogramRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    // Generate heat map gradient slices
    const cols = 60;
    const rows = 30;
    const colWidth = width / cols;
    const rowHeight = height / rows;

    for (let c = 0; c < cols; c++) {
      for (let r = 0; r < rows; r++) {
        // Frequency maps from 8kHz (top, r=0) down to 100Hz (bottom, r=rows)
        const freqRatio = (rows - r) / rows;
        const currentFreqHz = freqRatio * 8000;

        let intensity = Math.random() * 0.2;

        // Highlight 1–3 kHz knock band (approx rows 10 to 20)
        const isKnockBand = currentFreqHz >= 1000 && currentFreqHz <= 3000;

        if (activePreset === 'rod_knock' && isKnockBand) {
          // High intensity in knock band
          intensity = 0.7 + Math.sin(c * 0.5) * 0.3;
        } else if (activePreset === 'lifter_tick' && currentFreqHz >= 3500 && currentFreqHz <= 4500) {
          intensity = 0.6 + Math.cos(c * 0.4) * 0.3;
        } else if (activePreset === 'healthy') {
          intensity = (1 - freqRatio) * 0.4 + Math.random() * 0.15;
        }

        // Color mapping: Purple -> Blue -> Cyan -> Yellow -> Red
        let rCol = 15,
          gCol = 23,
          bCol = 42;

        if (intensity > 0.65) {
          // Critical Knock Spike: Bright Red/Orange
          rCol = 244;
          gCol = 63;
          bCol = 94;
        } else if (intensity > 0.4) {
          // Moderate: Amber/Yellow
          rCol = 245;
          gCol = 158;
          bCol = 11;
        } else if (intensity > 0.2) {
          // Low: Cyan/Blue
          rCol = 6;
          gCol = 182;
          bCol = 212;
        }

        ctx.fillStyle = `rgba(${rCol}, ${gCol}, ${bCol}, ${intensity + 0.1})`;
        ctx.fillRect(c * colWidth, r * rowHeight, colWidth - 0.5, rowHeight - 0.5);
      }
    }
  }, [activePreset, isAnalyzing]);

  return (
    <div className="glass-panel rounded-2xl p-5 border border-slate-800 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Sliders className="w-5 h-5 text-cyan-400" />
          <h2 className="text-sm font-bold tracking-tight text-white uppercase">
            Live Audio Signal & Mel-Spectrogram Heatmap
          </h2>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
          <Activity className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
          <span>Real-Time FFT Sampling (44.1 kHz)</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Canvas #1: Oscilloscope Waveform */}
        <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 relative">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2 font-mono">
            <span>Time-Domain Oscilloscope</span>
            <span className="text-cyan-400 font-semibold">Amplitude Waveform</span>
          </div>
          <canvas
            ref={waveformRef}
            width={420}
            height={130}
            className="w-full h-[130px] rounded border border-slate-900 bg-slate-950/80"
          />
        </div>

        {/* Canvas #2: Mel-Spectrogram Frequency Heatmap */}
        <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 relative">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2 font-mono">
            <span className="flex items-center gap-1.5 text-rose-400 font-semibold">
              <Flame className="w-3.5 h-3.5" />
              1–3 kHz Engine Knock Band
            </span>
            <span>Peak: {knockPeakHz} Hz</span>
          </div>

          <div className="relative">
            <canvas
              ref={spectrogramRef}
              width={420}
              height={130}
              className="w-full h-[130px] rounded border border-slate-900 bg-slate-950/80"
            />

            {/* Overlay Knock Band Box (1-3 kHz Region) */}
            <div className="absolute top-[35%] bottom-[40%] left-0 right-0 border-y border-dashed border-rose-500/60 bg-rose-500/10 pointer-events-none flex items-center justify-end pr-2">
              <span className="text-[10px] font-mono text-rose-300 bg-slate-950/90 px-1.5 py-0.5 rounded border border-rose-500/40">
                1–3 kHz Knock Filter Window
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
