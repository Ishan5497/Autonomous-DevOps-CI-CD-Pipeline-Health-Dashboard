import React from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Zap,
  Gauge,
  Flame,
  Check,
} from 'lucide-react';

export default function HealthVisualizer({ health, runs = [] }) {
  const {
    success_rate_percent = 100,
    average_duration_seconds = 0,
    health_grade = 'A+',
    risk_level = 'LOW',
    critical_vulnerabilities = 0,
  } = health || {};

  // Stage metrics breakdown
  const stages = [
    { name: 'Static Lint', status: 'optimal', latency: '4.2s', rate: 99.4, color: 'bg-cyan-500' },
    { name: 'Test Matrix', status: success_rate_percent < 80 ? 'degraded' : 'optimal', latency: '34.8s', rate: Math.max(75, success_rate_percent), color: 'bg-emerald-500' },
    { name: 'Diff SecScan', status: critical_vulnerabilities > 0 ? 'critical' : 'optimal', latency: '6.1s', rate: critical_vulnerabilities > 0 ? 60.0 : 100, color: critical_vulnerabilities > 0 ? 'bg-rose-500' : 'bg-purple-500' },
    { name: 'Docker Build', status: 'optimal', latency: '48.2s', rate: 96.2, color: 'bg-blue-500' },
    { name: 'Canary Deploy', status: 'optimal', latency: '19.5s', rate: 98.0, color: 'bg-teal-500' },
  ];

  // Test coverage simulation derived from pipeline health
  const simulatedTestCoverage = Math.min(98.5, Math.max(82.0, (success_rate_percent * 0.95).toFixed(1)));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      {/* 1. Pipeline Health & Quality Gate Visualizer */}
      <div className="glass-panel rounded-2xl p-5 lg:col-span-2 flex flex-col justify-between">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Gauge className="w-4 h-4 text-cyan-400" />
            <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
              Autonomous Pipeline Reliability & Health Gates
            </h3>
          </div>
          <span className="text-[11px] font-mono text-cyan-400 bg-cyan-500/10 border border-cyan-500/30 px-2 py-0.5 rounded-full">
            Grade {health_grade} / {risk_level} Risk
          </span>
        </div>

        {/* Segmented Visual Progress Bar */}
        <div className="space-y-2 my-2">
          <div className="flex justify-between items-center text-xs font-mono">
            <span className="text-slate-400 flex items-center gap-1.5">
              <span>Overall Pipeline Reliability</span>
              <span className="text-white font-bold">{success_rate_percent}%</span>
            </span>
            <span className="text-slate-500 text-[11px]">SLA Threshold: 90.0%</span>
          </div>

          <div className="relative h-3 w-full bg-slate-800/80 rounded-full overflow-hidden p-0.5 border border-slate-700/50">
            {/* Target marker at 90% */}
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-yellow-400/80 z-10"
              style={{ left: '90%' }}
              title="90% Target SLA"
            />
            <div
              style={{ width: `${success_rate_percent}%` }}
              className={`h-full rounded-full transition-all duration-700 ${
                success_rate_percent >= 90
                  ? 'bg-gradient-to-r from-emerald-500 to-cyan-400 shadow-sm shadow-cyan-400/30'
                  : success_rate_percent >= 75
                  ? 'bg-gradient-to-r from-amber-500 to-yellow-400'
                  : 'bg-gradient-to-r from-rose-600 to-rose-400 shadow-sm shadow-rose-500/30'
              }`}
            />
          </div>

          <div className="flex justify-between text-[10px] font-mono text-slate-500 px-0.5">
            <span>0% (Degraded)</span>
            <span className="text-yellow-400">90% (SLA Target)</span>
            <span>100% (Zero Faults)</span>
          </div>
        </div>

        {/* Stage-by-Stage Latency & Success Breakdown */}
        <div className="mt-4 pt-3 border-t border-slate-800/80">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2.5">
            Stage Latency & Gate Stability
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
            {stages.map((stg) => (
              <div
                key={stg.name}
                className="bg-slate-900/60 rounded-xl p-2.5 border border-slate-800/80 flex flex-col justify-between"
              >
                <div className="flex items-center justify-between text-[11px] mb-1">
                  <span className="font-medium text-slate-300 truncate">{stg.name}</span>
                  <span
                    className={`w-2 h-2 rounded-full ${
                      stg.status === 'critical'
                        ? 'bg-rose-500 animate-pulse'
                        : stg.status === 'degraded'
                        ? 'bg-amber-400'
                        : 'bg-emerald-400'
                    }`}
                  />
                </div>
                <div className="flex items-baseline justify-between font-mono text-xs">
                  <span className="text-cyan-400">{stg.latency}</span>
                  <span className="text-slate-500 text-[10px]">{stg.rate}%</span>
                </div>
                <div className="w-full h-1 bg-slate-800 rounded-full mt-1.5 overflow-hidden">
                  <div
                    style={{ width: `${stg.rate}%` }}
                    className={`h-full ${stg.color}`}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 2. Test Coverage & Quality Gate Metrics */}
      <div className="glass-panel rounded-2xl p-5 flex flex-col justify-between">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
              Test Coverage & Quality
            </h3>
          </div>
          <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded-full">
            PASSING
          </span>
        </div>

        {/* Circular / Radial visual representation */}
        <div className="flex items-center justify-center my-3">
          <div className="relative flex items-center justify-center">
            {/* Outer Ring */}
            <svg className="w-28 h-28 transform -rotate-90">
              <circle
                cx="56"
                cy="56"
                r="46"
                stroke="currentColor"
                strokeWidth="7"
                className="text-slate-800/90"
                fill="transparent"
              />
              <circle
                cx="56"
                cy="56"
                r="46"
                stroke="currentColor"
                strokeWidth="7"
                strokeDasharray={289}
                strokeDashoffset={289 - (289 * simulatedTestCoverage) / 100}
                strokeLinecap="round"
                className="text-emerald-400 transition-all duration-1000 ease-out"
                fill="transparent"
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center text-center">
              <span className="text-2xl font-bold font-mono text-white tracking-tight">
                {simulatedTestCoverage}%
              </span>
              <span className="text-[10px] text-slate-400 uppercase tracking-widest font-mono">
                Coverage
              </span>
            </div>
          </div>
        </div>

        {/* Quality Gates Checklist */}
        <div className="space-y-1.5 pt-2 border-t border-slate-800/80 text-xs">
          <div className="flex items-center justify-between text-slate-300">
            <span className="flex items-center gap-1.5 text-slate-400 text-[11px]">
              <Check className="w-3.5 h-3.5 text-emerald-400" /> Zero Leaked Secret Gate
            </span>
            <span
              className={`font-mono text-[10px] ${
                critical_vulnerabilities === 0 ? 'text-emerald-400' : 'text-rose-400'
              }`}
            >
              {critical_vulnerabilities === 0 ? 'PASSED' : `${critical_vulnerabilities} BLOCKED`}
            </span>
          </div>

          <div className="flex items-center justify-between text-slate-300">
            <span className="flex items-center gap-1.5 text-slate-400 text-[11px]">
              <Check className="w-3.5 h-3.5 text-emerald-400" /> Static Analysis Gate
            </span>
            <span className="font-mono text-[10px] text-cyan-400">ACTIVE (15 RULES)</span>
          </div>

          <div className="flex items-center justify-between text-slate-300">
            <span className="flex items-center gap-1.5 text-slate-400 text-[11px]">
              <Check className="w-3.5 h-3.5 text-emerald-400" /> Mean Build Duration
            </span>
            <span className="font-mono text-[10px] text-slate-300">
              {average_duration_seconds}s
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
