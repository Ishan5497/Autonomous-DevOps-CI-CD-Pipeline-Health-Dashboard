import React, { useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  Clock,
  RotateCw,
  GitCommit,
  GitBranch,
  Search,
  Filter,
  ExternalLink,
  ChevronRight,
  Terminal,
} from 'lucide-react';

export default function StatusTable({ runs = [], onTriggerSimulatedRun }) {
  const [filter, setFilter] = useState('ALL');
  const [search, setSearch] = useState('');

  const filteredRuns = runs.filter((run) => {
    const matchesFilter =
      filter === 'ALL' ||
      (filter === 'SUCCESS' && run.status?.toLowerCase() === 'success') ||
      (filter === 'FAILED' && ['failed', 'failure', 'error'].includes(run.status?.toLowerCase())) ||
      (filter === 'RUNNING' && ['running', 'pending'].includes(run.status?.toLowerCase()));

    const matchesSearch =
      !search ||
      run.pipeline_id?.toLowerCase().includes(search.toLowerCase()) ||
      run.commit_sha?.toLowerCase().includes(search.toLowerCase()) ||
      run.commit_message?.toLowerCase().includes(search.toLowerCase()) ||
      run.branch?.toLowerCase().includes(search.toLowerCase()) ||
      run.author?.toLowerCase().includes(search.toLowerCase());

    return matchesFilter && matchesSearch;
  });

  const getStatusBadge = (status) => {
    switch (status?.toLowerCase()) {
      case 'success':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold font-mono bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            PASSED
          </span>
        );
      case 'failed':
      case 'failure':
      case 'error':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold font-mono bg-rose-500/15 text-rose-400 border border-rose-500/30">
            <XCircle className="w-3.5 h-3.5 text-rose-400" />
            FAILED
          </span>
        );
      case 'running':
      case 'pending':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold font-mono bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 animate-pulse">
            <RotateCw className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
            RUNNING
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold font-mono bg-slate-800 text-slate-400 border border-slate-700">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            {status?.toUpperCase() || 'UNKNOWN'}
          </span>
        );
    }
  };

  const getStageIcon = (stage) => {
    switch (stage?.toLowerCase()) {
      case 'lint':
      case 'lint_and_build':
        return '🔍';
      case 'test':
        return '🧪';
      case 'deploy':
        return '🚀';
      case 'security_scan':
        return '🛡️';
      default:
        return '⚙️';
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-5 space-y-4">
      {/* Table Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <Terminal className="w-4 h-4 text-cyan-400" />
            Real-Time Pipeline Executions & Status Telemetry
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Monitoring active runners, automated gate verifications, and execution durations
          </p>
        </div>

        {/* Search & Filter Bar */}
        <div className="flex items-center gap-2 flex-wrap">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search branch, commit, or ID..."
              className="bg-slate-900/90 border border-slate-700/80 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500/50 w-48 sm:w-56"
            />
          </div>

          <div className="flex items-center bg-slate-900/90 p-0.5 rounded-xl border border-slate-700/80 text-xs">
            {['ALL', 'SUCCESS', 'FAILED', 'RUNNING'].map((tab) => (
              <button
                key={tab}
                onClick={() => setFilter(tab)}
                className={`px-2.5 py-1 rounded-lg font-mono text-[11px] transition-colors ${
                  filter === tab
                    ? 'bg-cyan-500/20 text-cyan-300 font-semibold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto rounded-xl border border-slate-800/80 bg-slate-950/40">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800/80 uppercase font-mono text-[10px] tracking-wider">
            <tr>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Pipeline ID / Commit</th>
              <th className="px-4 py-3">Branch</th>
              <th className="px-4 py-3">Stage</th>
              <th className="px-4 py-3">Duration</th>
              <th className="px-4 py-3">Author</th>
              <th className="px-4 py-3 text-right">Time</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-sans">
            {filteredRuns.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-12 text-center text-slate-500 text-xs">
                  <div className="max-w-xs mx-auto space-y-2">
                    <p className="font-mono text-slate-400">No pipeline executions found.</p>
                    <p className="text-[11px] text-slate-500">
                      Click "Seed Demo Data" or use the Webhook Simulator to dispatch events.
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              filteredRuns.map((run) => (
                <tr
                  key={run.id || run.pipeline_id}
                  className="hover:bg-slate-900/40 transition-colors group"
                >
                  <td className="px-4 py-3 whitespace-nowrap">
                    {getStatusBadge(run.status)}
                  </td>

                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex items-center gap-1.5 font-mono font-medium text-slate-200">
                      <span>{run.pipeline_id || 'manual-run'}</span>
                    </div>
                    <div className="text-[11px] text-slate-400 flex items-center gap-1 font-mono truncate max-w-xs mt-0.5">
                      <GitCommit className="w-3 h-3 text-cyan-400 shrink-0" />
                      <span className="text-cyan-400">
                        {(run.commit_sha || '').substring(0, 7)}
                      </span>
                      <span className="text-slate-500">•</span>
                      <span className="truncate text-slate-300">
                        {run.commit_message || 'Pipeline trigger'}
                      </span>
                    </div>
                    {run.failure_reason && (
                      <div className="mt-1 text-[11px] font-mono text-rose-400/90 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20 max-w-sm truncate">
                        ⚠ {run.failure_reason}
                      </div>
                    )}
                  </td>

                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md font-mono text-[11px] bg-purple-500/10 text-purple-300 border border-purple-500/20">
                      <GitBranch className="w-3 h-3" />
                      {run.branch || 'main'}
                    </span>
                  </td>

                  <td className="px-4 py-3 whitespace-nowrap font-mono text-slate-300">
                    <span className="mr-1.5">{getStageIcon(run.stage)}</span>
                    {run.stage || 'build'}
                  </td>

                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="font-mono text-slate-200">
                      {run.duration_seconds || 0}s
                    </div>
                    <div className="w-16 h-1 bg-slate-800 rounded-full mt-1 overflow-hidden">
                      <div
                        style={{
                          width: `${Math.min(100, ((run.duration_seconds || 10) / 90) * 100)}%`,
                        }}
                        className="h-full bg-cyan-400/80"
                      />
                    </div>
                  </td>

                  <td className="px-4 py-3 whitespace-nowrap text-slate-300 font-mono text-[11px]">
                    {run.author || 'system'}
                  </td>

                  <td className="px-4 py-3 whitespace-nowrap text-right font-mono text-[11px] text-slate-500">
                    {run.created_at
                      ? new Date(run.created_at).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                          second: '2-digit',
                        })
                      : 'Just now'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between text-xs text-slate-500 px-1 font-mono">
        <span>Showing {filteredRuns.length} of {runs.length} recorded executions</span>
        <span>Auto-refreshed via FastAPI WebSocket / Polling</span>
      </div>
    </div>
  );
}
