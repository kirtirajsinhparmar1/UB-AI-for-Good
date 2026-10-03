import { AlertCircle, ArrowRight, CheckCircle, TrendingUp, Truck } from 'lucide-react';
import type { DecisionResponse, RecommendedChannel } from '../types/acoustic';

interface RoutingValuationProps {
  result: DecisionResponse | null;
}

const money = (value: number) => new Intl.NumberFormat('en-US', {
  style: 'currency', currency: 'USD', maximumFractionDigits: 0,
}).format(value);

function EconomicsCard({
  title,
  route,
  value,
  recommendedChannel,
}: {
  title: string;
  route: 'ACV' | 'COPART';
  value: number;
  recommendedChannel: RecommendedChannel;
}) {
  const highlighted = recommendedChannel === route;
  const accent = route === 'ACV'
    ? { label: 'text-emerald-400', pill: 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300', active: 'border-emerald-500/80 bg-slate-900/90 shadow-2xl ring-1 ring-emerald-500/50', value: 'text-emerald-400' }
    : { label: 'text-rose-400', pill: 'bg-rose-500/20 border-rose-500/50 text-rose-300', active: 'border-rose-500/80 bg-slate-900/90 shadow-2xl ring-1 ring-rose-500/50', value: 'text-rose-400' };

  return (
    <div className={`glass-panel rounded-2xl p-6 border transition-all duration-300 relative flex flex-col justify-between ${highlighted ? accent.active : 'border-slate-800 bg-slate-950/70 opacity-90'}`}>
      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <span className={`text-xs font-bold ${accent.label} uppercase tracking-wider block`}>{route} &bull; Expected Value</span>
            <h3 className="text-xl font-extrabold text-white">{title}</h3>
          </div>
          <div className={`p-2.5 rounded-xl border ${accent.pill}`}>
            {route === 'ACV' ? <TrendingUp className="w-6 h-6" /> : <Truck className="w-6 h-6" />}
          </div>
        </div>
        <div className="bg-slate-900/90 rounded-xl p-4 border border-slate-800 shadow-inner">
          <div className="flex items-center justify-between text-sm font-bold">
            <span className="text-slate-200">{title}</span>
            <span className={`font-mono text-lg ${accent.value}`}>{money(value)}</span>
          </div>
        </div>
      </div>
      <div className="mt-6 pt-4 border-t border-slate-800 flex items-center justify-between bg-slate-900 p-4 rounded-xl">
        <div>
          <span className="text-[10px] text-slate-400 uppercase font-bold block">{highlighted ? 'Recommended Channel' : 'Expected Value'}</span>
          <span className={`text-2xl font-black font-mono ${accent.value}`}>{money(value)}</span>
        </div>
        {highlighted && <span className={`px-3 py-2 rounded-lg text-xs font-bold ${route === 'ACV' ? 'bg-emerald-500/15 text-emerald-300' : 'bg-rose-500/15 text-rose-300'}`}>Recommended</span>}
      </div>
    </div>
  );
}

export const RoutingValuation: React.FC<RoutingValuationProps> = ({ result }) => {
  if (!result) {
    return (
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 text-center">
        <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-widest">STEP 3 &bull; VALUE & CHANNEL ROUTING</span>
        <h2 className="text-lg font-bold text-white mt-1">Adjusted ACV Value vs. Copart Expected Value</h2>
        <p className="text-sm text-slate-400 mt-2">Submit engine audio to calculate adjusted ACV value and the recommended channel.</p>
      </div>
    );
  }

  const { valuation, economics, decision } = result;
  const route = decision.recommended_channel;
  const deltaPct = valuation.acoustic_delta_pct * 100;

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-900/90 p-4 rounded-2xl border border-slate-800 shadow-md">
        <div>
          <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-widest px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30">STEP 3 &bull; ACV / COPART ECONOMICS</span>
          <h2 className="text-lg font-bold tracking-tight text-white mt-1">Adjusted ACV Value vs. Copart Expected Value</h2>
          <p className="text-xs text-slate-400 mt-0.5">Prototype acoustic value adjustment and caller-provided Copart estimate.</p>
        </div>
        <div className={`px-4 py-2 rounded-xl border text-xs font-extrabold flex items-center gap-2 shadow-lg ${route === 'ACV' ? 'bg-emerald-500/20 border-emerald-500/60 text-emerald-300' : route === 'COPART' ? 'bg-rose-500/20 border-rose-500/60 text-rose-300' : 'bg-amber-500/20 border-amber-500/60 text-amber-300'}`}>
          {route === 'REVIEW' ? <AlertCircle className="w-4 h-4" /> : <CheckCircle className="w-4 h-4" />}
          <span>RECOMMENDED CHANNEL: {route}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className={`glass-panel rounded-2xl p-6 border ${route === 'ACV' ? 'border-emerald-500/80 bg-slate-900/90 ring-1 ring-emerald-500/40' : 'border-slate-800 bg-slate-950/70'}`}>
          <div className="flex items-start justify-between mb-4">
            <div><span className="text-xs font-bold text-emerald-400 uppercase tracking-wider block">Acoustic Value Delta</span><h3 className="text-xl font-extrabold text-white">Adjusted ACV Value</h3></div>
            <TrendingUp className="w-6 h-6 text-emerald-400" />
          </div>
          <div className="bg-slate-900/90 rounded-xl p-4 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between text-xs"><span className="text-slate-400">Base wholesale value</span><span className="font-mono font-bold text-slate-200">{money(valuation.base_wholesale_value)}</span></div>
            <div className="flex items-center justify-between text-xs"><span className="text-slate-300">Acoustic value adjustment</span><span className={`font-mono font-bold ${valuation.acoustic_delta_amount < 0 ? 'text-rose-300' : 'text-emerald-300'}`}>{valuation.acoustic_delta_amount >= 0 ? '+' : '−'}{money(Math.abs(valuation.acoustic_delta_amount))} ({deltaPct >= 0 ? '+' : ''}{deltaPct.toFixed(2)}%)</span></div>
            <div className="flex items-center justify-between text-sm pt-2 border-t border-slate-800 font-bold"><span className="text-slate-200">Adjusted ACV Value</span><span className="font-mono text-lg text-emerald-400">{money(valuation.adjusted_wholesale_value)}</span></div>
          </div>
        </div>

        <EconomicsCard
          title="Copart Expected Value"
          route="COPART"
          value={economics.copart_expected_value}
          recommendedChannel={route}
        />
      </div>

      <div className={`p-4 rounded-2xl border text-sm flex items-start gap-3 shadow-xl ${route === 'ACV' ? 'bg-gradient-to-r from-emerald-950 via-slate-900 to-emerald-950 border-emerald-500 text-emerald-100' : route === 'COPART' ? 'bg-gradient-to-r from-rose-950 via-slate-900 to-rose-950 border-rose-500 text-rose-100' : 'bg-gradient-to-r from-amber-950 via-slate-900 to-amber-950 border-amber-500 text-amber-100'}`}>
        <div className="p-2.5 rounded-xl shrink-0 bg-slate-950/50"><ArrowRight className="w-5 h-5" /></div>
        <div className="space-y-1">
          <span className="text-[11px] uppercase tracking-widest font-mono text-cyan-300 block font-semibold">Decision rationale · {decision.decision_strength} margin</span>
          <p className="leading-snug text-white font-semibold">{decision.rationale}</p>
          <p className="text-xs text-slate-300">Value difference (Copart − ACV): {money(economics.value_difference)} · Switch advantage threshold: {money(decision.minimum_switch_advantage)}</p>
        </div>
      </div>

      <div className="rounded-xl border border-amber-500/30 bg-amber-950/25 px-4 py-3 text-xs text-amber-100/90">
        <span className="font-bold">Prototype economic policy for hackathon demonstration.</span>{' '}
        {valuation.policy_note || result.disclaimer}
      </div>
    </div>
  );
};
