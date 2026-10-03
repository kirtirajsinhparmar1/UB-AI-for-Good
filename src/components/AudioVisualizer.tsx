import { useEffect, useRef, useState } from 'react';
import { Activity, AudioLines, Sliders } from 'lucide-react';

interface AudioVisualizerProps {
  audioFile?: File;
  isAnalyzing: boolean;
}

export const AudioVisualizer: React.FC<AudioVisualizerProps> = ({ audioFile, isAnalyzing }) => {
  const waveformRef = useRef<HTMLCanvasElement>(null);
  const amplitudeRef = useRef<HTMLCanvasElement>(null);
  const [previewInfo, setPreviewInfo] = useState<string | null>(null);

  useEffect(() => {
    const waveform = waveformRef.current;
    const amplitude = amplitudeRef.current;
    if (!waveform || !amplitude) return;

    const waveformContext = waveform.getContext('2d');
    const amplitudeContext = amplitude.getContext('2d');
    if (!waveformContext || !amplitudeContext) return;

    const drawGrid = (context: CanvasRenderingContext2D, canvas: HTMLCanvasElement) => {
      context.clearRect(0, 0, canvas.width, canvas.height);
      context.strokeStyle = 'rgba(30, 41, 59, 0.8)';
      context.lineWidth = 1;
      for (let y = canvas.height / 4; y < canvas.height; y += canvas.height / 4) {
        context.beginPath();
        context.moveTo(0, y);
        context.lineTo(canvas.width, y);
        context.stroke();
      }
    };

    drawGrid(waveformContext, waveform);
    drawGrid(amplitudeContext, amplitude);
    setPreviewInfo(null);
    if (!audioFile) return;

    let live = true;
    let audioContext: AudioContext | undefined;
    const render = async () => {
      try {
        audioContext = new AudioContext();
        const decoded = await audioContext.decodeAudioData(await audioFile.arrayBuffer());
        if (!live) return;
        const samples = decoded.getChannelData(0);
        const width = waveform.width;
        const height = waveform.height;
        const centerY = height / 2;
        const samplesPerColumn = Math.max(1, Math.floor(samples.length / width));

        waveformContext.strokeStyle = '#22d3ee';
        waveformContext.lineWidth = 1.5;
        waveformContext.beginPath();
        for (let x = 0; x < width; x += 1) {
          const start = x * samplesPerColumn;
          let min = 1;
          let max = -1;
          for (let index = start; index < Math.min(start + samplesPerColumn, samples.length); index += 1) {
            min = Math.min(min, samples[index]);
            max = Math.max(max, samples[index]);
          }
          waveformContext.moveTo(x, centerY - max * centerY * 0.9);
          waveformContext.lineTo(x, centerY - min * centerY * 0.9);
        }
        waveformContext.stroke();

        const columns = 60;
        const columnWidth = width / columns;
        amplitudeContext.fillStyle = '#0e7490';
        for (let column = 0; column < columns; column += 1) {
          const start = Math.floor((column / columns) * samples.length);
          const end = Math.max(start + 1, Math.floor(((column + 1) / columns) * samples.length));
          let sumSquares = 0;
          for (let index = start; index < Math.min(end, samples.length); index += 1) sumSquares += samples[index] ** 2;
          const rms = Math.sqrt(sumSquares / Math.max(1, end - start));
          const barHeight = Math.max(2, rms * (height - 8));
          amplitudeContext.fillRect(column * columnWidth + 1, height - barHeight - 4, columnWidth - 2, barHeight);
        }
        setPreviewInfo(`${decoded.duration.toFixed(1)} sec · ${decoded.sampleRate.toLocaleString()} Hz`);
      } catch {
        if (live) setPreviewInfo('WAV preview could not be decoded');
      } finally {
        await audioContext?.close().catch(() => undefined);
      }
    };

    void render();
    return () => {
      live = false;
      void audioContext?.close().catch(() => undefined);
    };
  }, [audioFile]);

  return (
    <div className="glass-panel rounded-2xl p-5 border border-slate-800 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 gap-2">
        <div className="flex items-center gap-2">
          <Sliders className="w-5 h-5 text-cyan-400" />
          <h2 className="text-sm font-bold tracking-tight text-white uppercase">Audio Signal Preview</h2>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
          <Activity className={`w-3.5 h-3.5 ${isAnalyzing ? 'text-cyan-400 animate-pulse' : 'text-slate-500'}`} />
          <span>{previewInfo ?? (audioFile ? 'Reading WAV…' : 'Awaiting WAV')}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2 font-mono">
            <span>Time-domain waveform</span><span className="text-cyan-400 font-semibold">Uploaded audio</span>
          </div>
          <canvas ref={waveformRef} width={420} height={130} className="w-full h-[130px] rounded border border-slate-900 bg-slate-950/80" />
        </div>
        <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2 font-mono">
            <span className="flex items-center gap-1.5 text-cyan-300 font-semibold"><AudioLines className="w-3.5 h-3.5" />Signal amplitude</span>
            <span>RMS by time</span>
          </div>
          <canvas ref={amplitudeRef} width={420} height={130} className="w-full h-[130px] rounded border border-slate-900 bg-slate-950/80" />
        </div>
      </div>
    </div>
  );
};
