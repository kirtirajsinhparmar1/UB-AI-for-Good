import {
  TrendingUp,
  Award,
  AlertCircle,
  Truck,
  CheckCircle,
  ArrowRight,
  ShieldAlert,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import type { ValuationComparison } from '../types/acoustic';

interface RoutingValuationProps {
  valuation: ValuationComparison;
}

export const RoutingValuation: React.FC<RoutingValuationProps> = ({ valuation }) => {
  const { acv, copart, winningRoute, actionMessage } = valuation;


  return (
    <div className="space-y-5">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-900/90 p-4 rounded-2xl border border-slate-800 shadow-md">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-widest px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30">
              STEP 3 &bull; WATERFALL VALUATION & ARBITRAGE
            </span>
          </div>
          <h2 className="text-lg font-bold tracking-tight text-white mt-1 flex items-center gap-2">
            ACV Wholesale Waterfall vs. Copart Salvage Floor
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Baseline market value is dynamically calibrated by APEX acoustic delta (+$1,200 to -$5,800) to dictate optimal channel routing.
          </p>
        </div>

        {/* Winning Route Summary Pill */}
        <div className="flex items-center gap-3">
          <div
            className={`px-4 py-2 rounded-xl border text-xs font-extrabold flex items-center gap-2 shadow-lg transition-all ${
              winningRoute === 'ACV'
                ? 'bg-emerald-500/20 border-emerald-500/60 text-emerald-300 glow-acv'
                : 'bg-rose-500/20 border-rose-500/60 text-rose-300 glow-copart'
            }`}
          >
            {winningRoute === 'ACV' ? (
              <TrendingUp className="w-4 h-4 text-emerald-400" />
            ) : (
              <Truck className="w-4 h-4 text-rose-400" />
            )}
            <span>
              WINNING ROUTE: {winningRoute === 'ACV' ? 'ACV Dealer Wholesale' : 'Copart Salvage Harvest'}
            </span>
          </div>
        </div>
      </div>

      {/* Side-by-Side Comparison Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* COLUMN 1: ACV WHOLESALE ROUTE (WATERFALL VALUATION) */}
        <div
          className={`glass-panel rounded-2xl p-6 border transition-all duration-300 relative flex flex-col justify-between ${
            winningRoute === 'ACV'
              ? 'glow-acv border-emerald-500/80 bg-slate-900/90 shadow-2xl ring-1 ring-emerald-500/50'
              : 'border-slate-800 bg-slate-950/70 opacity-90 hover:opacity-100'
          }`}
        >
          {/* Header */}
          <div className="space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider block">
                  Column 1 &bull; Whole-Car Wholesale
                </span>
                <h3 className="text-xl font-extrabold text-white flex items-center gap-2">
                  ACV Dealer Wholesale Auction
                </h3>
              </div>
              <div
                className={`p-2.5 rounded-xl border ${
                  winningRoute === 'ACV'
                    ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300'
                    : 'bg-slate-900 border-slate-800 text-slate-400'
                }`}
              >
                <TrendingUp className="w-6 h-6" />
              </div>
            </div>

            {/* Recommendation Note */}
            <div
              className={`p-3.5 rounded-xl border text-xs font-semibold ${
                acv.isRecommended
                  ? 'bg-emerald-950/60 border-emerald-500/50 text-emerald-200'
                  : 'bg-rose-950/60 border-rose-500/50 text-rose-200'
              }`}
            >
              <div className="flex items-start gap-2.5">
                {acv.isRecommended ? (
                  <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                )}
                <span>{acv.recommendationNote}</span>
              </div>
            </div>

            {/* Waterfall Valuation Breakdown List */}
            <div className="bg-slate-900/90 rounded-xl p-4 border border-slate-800 space-y-3 shadow-inner">
              <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 block border-b border-slate-800 pb-2">
                Waterfall Valuation Model
              </span>

              {/* Line 1: Baseline Market Book Value */}
              <div className="flex items-center justify-between text-xs font-medium">
                <span className="text-slate-400">Baseline Market Book Value (ACV MAX):</span>
                <span className="font-mono font-bold text-slate-200 text-sm">
                  ${acv.baseBookValue.toLocaleString()}
                </span>
              </div>

              {/* Line 2: Acoustic Health Delta */}
              <div className="flex items-center justify-between text-xs font-medium py-1">
                <span className="text-slate-300 flex items-center gap-1.5 font-semibold">
                  <Zap className="w-3.5 h-3.5 text-cyan-400" /> Acoustic Health Delta (ClearCar AI):
                </span>
                <span
                  className={`font-mono text-xs font-bold px-2.5 py-1 rounded-full border ${
                    acv.acousticDelta > 0
                      ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300'
                      : 'bg-rose-500/20 border-rose-500/40 text-rose-300'
                  }`}
                >
                  {acv.acousticDeltaLabel}
                </span>
              </div>

              {/* Line 3: Recommended Seller Reserve */}
              <div className="flex items-center justify-between text-sm pt-2 border-t border-slate-800 font-bold">
                <span className="text-slate-200">Recommended Seller Reserve:</span>
                <span className="font-mono text-lg text-emerald-400">
                  ${acv.adjustedAcvWholesale.toLocaleString()}
                </span>
              </div>
            </div>

            {/* Engine Arbitration Risk Badge */}
            <div
              className={`p-3 rounded-xl border flex items-center justify-between text-xs font-semibold ${
                acv.arbitrationRiskLevel === 'Low'
                  ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-300'
                  : acv.arbitrationRiskLevel === 'Moderate'
                  ? 'bg-amber-950/40 border-amber-500/30 text-amber-300'
                  : 'bg-rose-950/40 border-rose-500/30 text-rose-300'
              }`}
            >
              <div className="flex items-center gap-2">
                {acv.arbitrationRiskLevel === 'Low' ? (
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                ) : (
                  <ShieldAlert className="w-4 h-4 text-rose-400" />
                )}
                <span>Engine Arbitration Risk Level:</span>
              </div>
              <span className="font-mono font-bold text-sm px-2.5 py-0.5 rounded bg-slate-950 border border-slate-700">
                {acv.arbitrationRiskLevel.toUpperCase()} ({acv.arbitrationRiskPercent})
              </span>
            </div>
          </div>

          {/* Action Footer */}
          <div className="mt-6 pt-4 border-t border-slate-800 flex items-center justify-between bg-slate-900 p-4 rounded-xl border border-slate-800">
            <div>
              <span className="text-[10px] text-slate-400 uppercase font-bold block">
                Adjusted Wholesale Value
              </span>
              <span className="text-2xl font-black font-mono text-emerald-400">
                ${acv.adjustedAcvWholesale.toLocaleString()}
              </span>
            </div>

            <button
              className={`px-4 py-2.5 rounded-xl font-bold text-xs flex items-center gap-2 transition-all cursor-pointer ${
                winningRoute === 'ACV'
                  ? 'bg-gradient-to-r from-emerald-500 to-cyan-500 text-slate-950 hover:brightness-110 shadow-lg shadow-emerald-500/20'
                  : 'bg-slate-800 text-slate-400 cursor-not-allowed opacity-60'
              }`}
            >
              <span>List on ACV Wholesale</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* COLUMN 2: COPART MARKETPLACE (SALVAGE / PARTS FLOOR) */}
        <div
          className={`glass-panel rounded-2xl p-6 border transition-all duration-300 relative flex flex-col justify-between ${
            winningRoute === 'COPART'
              ? 'glow-copart border-rose-500/80 bg-slate-900/90 shadow-2xl ring-1 ring-rose-500/50'
              : 'border-slate-800 bg-slate-950/70 opacity-90 hover:opacity-100'
          }`}
        >
          {/* Header */}
          <div className="space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-xs font-bold text-rose-400 uppercase tracking-wider block">
                  Column 2 &bull; Salvage & Dismantle Yield
                </span>
                <h3 className="text-xl font-extrabold text-white flex items-center gap-2">
                  Copart Salvage Marketplace
                </h3>
              </div>
              <div
                className={`p-2.5 rounded-xl border ${
                  winningRoute === 'COPART'
                    ? 'bg-rose-500/20 border-rose-500/50 text-rose-300'
                    : 'bg-slate-900 border-slate-800 text-slate-400'
                }`}
              >
                <Truck className="w-6 h-6" />
              </div>
            </div>

            {/* Recommendation Note */}
            <div
              className={`p-3.5 rounded-xl border text-xs font-semibold ${
                copart.isRecommended
                  ? 'bg-rose-950/60 border-rose-500/50 text-rose-200'
                  : 'bg-slate-900 border-slate-800 text-slate-400'
              }`}
            >
              <div className="flex items-start gap-2.5">
                {copart.isRecommended ? (
                  <Award className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                )}
                <span>{copart.recommendationNote}</span>
              </div>
            </div>

            {/* Guaranteed Salvage Recovery Breakdown */}
            <div className="bg-slate-900/90 rounded-xl p-4 border border-slate-800 space-y-3 shadow-inner">
              <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 block border-b border-slate-800 pb-2">
                Guaranteed Salvage Recovery Floor
              </span>

              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between p-2 rounded-lg bg-slate-950 border border-slate-800 font-medium">
                  <span className="text-slate-300">Intact Transmission & Drivetrain:</span>
                  <span className="font-mono font-bold text-slate-100">
                    ${copart.transmissionVal.toLocaleString()}
                  </span>
                </div>

                <div className="flex items-center justify-between p-2 rounded-lg bg-slate-950 border border-slate-800 font-medium">
                  <span className="text-slate-300">Core Body Panels & Structural Shell:</span>
                  <span className="font-mono font-bold text-slate-100">
                    ${copart.bodyPanelsVal.toLocaleString()}
                  </span>
                </div>

                <div className="flex items-center justify-between p-2 rounded-lg bg-slate-950 border border-slate-800 font-medium">
                  <span className="text-slate-300">Catalytic Converter & Scrap Metal:</span>
                  <span className="font-mono font-bold text-slate-100">
                    ${copart.catalyticScrapVal.toLocaleString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Net Salvage Floor Banner */}
            <div className="p-3 rounded-xl border border-slate-800 bg-slate-900/80 flex items-center justify-between text-xs font-semibold">
              <span className="text-slate-300">Guaranteed Yard Net Salvage Floor:</span>
              <span className="font-mono font-bold text-sm text-cyan-300">
                ${copart.copartSalvageFloor.toLocaleString()}
              </span>
            </div>
          </div>

          {/* Action Footer */}
          <div className="mt-6 pt-4 border-t border-slate-800 flex items-center justify-between bg-slate-900 p-4 rounded-xl border border-slate-800">
            <div>
              <span className="text-[10px] text-slate-400 uppercase font-bold block">
                Net Salvage Floor Yield
              </span>
              <span className="text-2xl font-black font-mono text-rose-400">
                ${copart.copartSalvageFloor.toLocaleString()}
              </span>
            </div>

            <button
              className={`px-4 py-2.5 rounded-xl font-bold text-xs flex items-center gap-2 transition-all cursor-pointer ${
                winningRoute === 'COPART'
                  ? 'bg-gradient-to-r from-rose-500 to-amber-500 text-slate-950 hover:brightness-110 shadow-lg shadow-rose-500/20'
                  : 'bg-slate-800 text-slate-400 cursor-not-allowed opacity-60'
              }`}
            >
              <span>Divert to Copart Salvage</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* ARBITRAGE DECISION BANNER (BOTTOM OF THE CARDS) */}
      <div
        className={`p-4 rounded-2xl border text-sm font-bold flex items-center gap-3 shadow-xl transition-all duration-300 ${
          winningRoute === 'ACV'
            ? 'bg-gradient-to-r from-emerald-950 via-slate-900 to-emerald-950 border-emerald-500 text-emerald-200'
            : 'bg-gradient-to-r from-rose-950 via-slate-900 to-amber-950 border-rose-500 text-rose-200'
        }`}
      >
        <div
          className={`p-2.5 rounded-xl shrink-0 ${
            winningRoute === 'ACV'
              ? 'bg-emerald-500/20 text-emerald-400'
              : 'bg-rose-500/20 text-rose-400'
          }`}
        >
          {winningRoute === 'ACV' ? (
            <TrendingUp className="w-6 h-6" />
          ) : (
            <Truck className="w-6 h-6" />
          )}
        </div>
        <div className="space-y-0.5">
          <span className="text-[11px] uppercase tracking-widest font-mono text-cyan-400 block font-semibold">
            Arbitrage Recommendation Decision Engine
          </span>
          <p className="leading-snug text-white font-extrabold text-sm sm:text-base">
            {actionMessage}
          </p>
        </div>
      </div>
    </div>
  );
};
