import React from 'react';
import { RefreshCw, Play, Shield, Activity, Menu } from 'lucide-react';

export default function Header({
  onRefresh,
  onSeedData,
  isRefreshing,
  isSeeding,
  lastUpdated,
  onToggleMobileSidebar,
}) {
  return (
    <header className="h-16 px-6 border-b border-slate-800/80 bg-[#070b14]/80 backdrop-blur-md sticky top-0 z-30 flex items-center justify-between">
      {/* Left: Title & Live indicator */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleMobileSidebar}
          className="lg:hidden p-2 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded-lg"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold text-slate-100">
              DevOps Operations Center
            </h2>
            <span className="hidden sm:inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              LIVE TELEMETRY
            </span>
          </div>
          <p className="text-[11px] text-slate-400 hidden md:block">
            Autonomous Pipeline Health, MTTR Diagnostics & Real-Time Diff Protection
          </p>
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2.5">
        {lastUpdated && (
          <span className="hidden xl:inline text-[11px] font-mono text-slate-500">
            Updated {lastUpdated.toLocaleTimeString()}
          </span>
        )}

        <button
          onClick={onSeedData}
          disabled={isSeeding}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-cyan-500 to-blue-600 text-slate-950 hover:brightness-110 active:scale-95 transition-all shadow-md shadow-cyan-500/10 disabled:opacity-50"
        >
          <Play className={`w-3.5 h-3.5 fill-current ${isSeeding ? 'animate-spin' : ''}`} />
          <span>{isSeeding ? 'Seeding...' : 'Seed Demo Data'}</span>
        </button>

        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900 border border-slate-700/80 text-slate-300 hover:text-white hover:bg-slate-800 active:scale-95 transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-cyan-400' : ''}`} />
          <span className="hidden sm:inline">Refresh</span>
        </button>
      </div>
    </header>
  );
}
