import React from 'react';
import {
  Activity,
  CheckCircle2,
  GitPullRequest,
  ShieldAlert,
  Clock,
  TrendingUp,
  AlertOctagon,
  Cpu,
} from 'lucide-react';

export default function MetricsCards({ health, runs = [], pullRequests = [] }) {
  const {
    total_runs = 0,
    successful_runs = 0,
    failed_runs = 0,
    running_runs = 0,
    success_rate_percent = 100,
    failure_rate_percent = 0,
    mttr_display = 'Optimal',
    health_grade = 'A+',
    risk_level = 'LOW',
    total_security_findings = 0,
    critical_vulnerabilities = 0,
  } = health || {};

  const openPRs = pullRequests.filter((pr) => pr.state === 'open').length;

  const getGradeColor = (grade) => {
    switch (grade) {
      case 'A+':
      case 'A':
        return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
      case 'B':
        return 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30';
      case 'C':
        return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
      default:
        return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
    }
  };

  const getRiskBadgeColor = (risk) => {
    switch (risk?.toUpperCase()) {
      case 'MINIMAL':
      case 'LOW':
        return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
      case 'MODERATE':
        return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
      default:
        return 'bg-rose-500/15 text-rose-400 border-rose-500/30';
    }
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-4">
      {/* 1. Total Builds Card */}
      <div className="glass-panel rounded-2xl p-4 flex flex-col justify-between hover:border-cyan-500/40 transition-all duration-300 group">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
            Total Builds
          </span>
          <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-400 group-hover:scale-110 transition-transform">
            <Activity className="w-4 h-4" />
          </div>
        </div>

        <div className="my-2.5">
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-white">
              {total_runs}
            </span>
            <span className="text-xs text-slate-400 font-mono">runs</span>
          </div>
          <div className="flex items-center gap-2 mt-1 text-[11px] font-mono text-slate-400">
            <span className="text-emerald-400 flex items-center gap-0.5">
              ● {successful_runs} passed
            </span>
            <span className="text-rose-400 flex items-center gap-0.5">
              ● {failed_runs} failed
            </span>
            {running_runs > 0 && (
              <span className="text-cyan-400 flex items-center gap-0.5">
                ● {running_runs} active
              </span>
            )}
          </div>
        </div>

        {/* Micro progress split */}
        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden flex">
          <div
            style={{ width: `${total_runs ? (successful_runs / total_runs) * 100 : 100}%` }}
            className="bg-emerald-500 h-full transition-all duration-500"
          />
          <div
            style={{ width: `${total_runs ? (failed_runs / total_runs) * 100 : 0}%` }}
            className="bg-rose-500 h-full transition-all duration-500"
          />
        </div>
      </div>

      {/* 2. Success Rate & Grade Card */}
      <div className="glass-panel rounded-2xl p-4 flex flex-col justify-between hover:border-emerald-500/40 transition-all duration-300 group">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
            Success Rate
          </span>
          <span
            className={`px-2 py-0.5 rounded-lg text-xs font-bold border font-mono ${getGradeColor(
              health_grade
            )}`}
          >
            Grade {health_grade}
          </span>
        </div>

        <div className="my-2.5">
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-emerald-400">
              {success_rate_percent}%
            </span>
            <span
              className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-medium border ${getRiskBadgeColor(
                risk_level
              )}`}
            >
              {risk_level} RISK
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            {success_rate_percent >= 90
              ? 'Reliability meeting SLA target'
              : 'Reliability below threshold'}
          </p>
        </div>

        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
          <div
            style={{ width: `${success_rate_percent}%` }}
            className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all duration-500"
          />
        </div>
      </div>

      {/* 3. Active Pull Requests Card */}
      <div className="glass-panel rounded-2xl p-4 flex flex-col justify-between hover:border-purple-500/40 transition-all duration-300 group">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
            Active PRs
          </span>
          <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-400 group-hover:scale-110 transition-transform">
            <GitPullRequest className="w-4 h-4" />
          </div>
        </div>

        <div className="my-2.5">
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-white">
              {openPRs}
            </span>
            <span className="text-xs text-slate-400 font-mono">
              of {pullRequests.length} total
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-purple-400 inline-block" />
            Automatic diff verification active
          </p>
        </div>

        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
          <div
            style={{
              width: `${pullRequests.length ? (openPRs / pullRequests.length) * 100 : 0}%`,
            }}
            className="h-full bg-gradient-to-r from-purple-500 to-indigo-400 transition-all duration-500"
          />
        </div>
      </div>

      {/* 4. Security Flags Card */}
      <div className="glass-panel rounded-2xl p-4 flex flex-col justify-between hover:border-rose-500/40 transition-all duration-300 group">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
            Security Flags
          </span>
          <div className="w-8 h-8 rounded-lg bg-rose-500/10 flex items-center justify-center text-rose-400 group-hover:scale-110 transition-transform">
            <ShieldAlert className="w-4 h-4" />
          </div>
        </div>

        <div className="my-2.5">
          <div className="flex items-baseline gap-2">
            <span
              className={`text-3xl font-bold tracking-tight ${
                critical_vulnerabilities > 0 ? 'text-rose-400' : 'text-slate-200'
              }`}
            >
              {total_security_findings}
            </span>
            <span
              className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-medium border ${
                critical_vulnerabilities > 0
                  ? 'bg-rose-500/20 text-rose-400 border-rose-500/40 animate-pulse'
                  : 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
              }`}
            >
              {critical_vulnerabilities} CRITICAL
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            {critical_vulnerabilities > 0
              ? 'Secret leak / RCE flaw detected'
              : 'Zero active critical leaks'}
          </p>
        </div>

        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
          <div
            style={{
              width: `${total_security_findings > 0 ? 100 : 0}%`,
            }}
            className={`h-full transition-all duration-500 ${
              critical_vulnerabilities > 0 ? 'bg-rose-500' : 'bg-emerald-500'
            }`}
          />
        </div>
      </div>

      {/* 5. MTTR Metric Card */}
      <div className="glass-panel rounded-2xl p-4 flex flex-col justify-between hover:border-cyan-500/40 transition-all duration-300 group col-span-1 sm:col-span-2 lg:col-span-4 xl:col-span-1">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
            MTTR
          </span>
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center text-cyan-400 group-hover:scale-110 transition-transform">
            <Clock className="w-4 h-4" />
          </div>
        </div>

        <div className="my-2.5">
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold tracking-tight text-cyan-400 font-mono">
              {mttr_display}
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            Mean recovery time from failure
          </p>
        </div>

        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
          <div
            style={{ width: '85%' }}
            className="h-full bg-gradient-to-r from-cyan-500 to-blue-500"
          />
        </div>
      </div>
    </div>
  );
}
