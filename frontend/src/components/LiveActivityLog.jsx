import React, { useState } from 'react';
import {
  Radio,
  Trash2,
  CheckCircle2,
  XCircle,
  ShieldAlert,
  Zap,
  GitCommit,
  Wifi,
  WifiOff,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

const SEVERITY_CONFIG = {
  critical: {
    icon: ShieldAlert,
    badge: 'bg-rose-500/20 text-rose-400 border-rose-500/40',
    dot: 'bg-rose-500 animate-pulse',
    row: 'border-l-rose-500',
  },
  error: {
    icon: XCircle,
    badge: 'bg-amber-500/20 text-amber-400 border-amber-500/40',
    dot: 'bg-amber-500',
    row: 'border-l-amber-500',
  },
  success: {
    icon: CheckCircle2,
    badge: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    dot: 'bg-emerald-400',
    row: 'border-l-emerald-500',
  },
  info: {
    icon: Zap,
    badge: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
    dot: 'bg-cyan-400',
    row: 'border-l-cyan-500',
  },
};

function LogEntry({ entry }) {
  const [expanded, setExpanded] = useState(false);
  const config = SEVERITY_CONFIG[entry.severity] || SEVERITY_CONFIG.info;
  const Icon = config.icon;

  const timeStr = (() => {
    try {
      return new Date(entry.timestamp).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return 'now';
    }
  })();

  return (
    <div
      className={`border-l-2 ${config.row} bg-slate-900/40 rounded-r-lg px-3 py-2 transition-all duration-300 hover:bg-slate-900/70 animate-slide-in`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-start gap-2 min-w-0 flex-1">
          <span className={`w-2 h-2 rounded-full ${config.dot} mt-1.5 shrink-0`} />
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span
                className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold border ${config.badge}`}
              >
                <Icon className="w-3 h-3" />
                {entry.type.replace('_', ' ')}
              </span>
              <span className="text-xs font-medium text-slate-200 truncate">
                {entry.title}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed truncate">
              {entry.message}
            </p>
            {entry.author && (
              <span className="text-[10px] text-slate-500 font-mono">
                by {entry.author}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          <span className="text-[10px] font-mono text-slate-500 whitespace-nowrap">
            {timeStr}
          </span>
          {entry.data && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="p-0.5 text-slate-500 hover:text-slate-300 transition-colors"
            >
              {expanded ? (
                <ChevronUp className="w-3 h-3" />
              ) : (
                <ChevronDown className="w-3 h-3" />
              )}
            </button>
          )}
        </div>
      </div>

      {expanded && entry.data && (
        <pre className="mt-2 text-[11px] font-mono text-cyan-300/80 bg-[#060911] p-2 rounded-lg border border-slate-800 overflow-x-auto max-h-32">
          {JSON.stringify(entry.data, null, 2)}
        </pre>
      )}
    </div>
  );
}

export default function LiveActivityLog({
  activityLog = [],
  isConnected = false,
  onClearLog,
}) {
  const [filter, setFilter] = useState('ALL');

  const filteredLog =
    filter === 'ALL'
      ? activityLog
      : activityLog.filter((e) => {
          switch (filter) {
            case 'PIPELINE':
              return e.type === 'PIPELINE_UPDATE';
            case 'FAILURES':
              return e.type === 'BUILD_FAILURE';
            case 'SECURITY':
              return e.type === 'SECURITY_ALERT';
            default:
              return true;
          }
        });

  return (
    <div className="glass-panel rounded-2xl p-5 space-y-3">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <Radio className="w-4 h-4 text-cyan-400" />
            Live Activity Stream
            <span
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium border ${
                isConnected
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
              }`}
            >
              {isConnected ? (
                <>
                  <Wifi className="w-3 h-3" />
                  LIVE
                </>
              ) : (
                <>
                  <WifiOff className="w-3 h-3" />
                  RECONNECTING
                </>
              )}
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time pipeline events, build status, and security alerts via WebSocket
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Filter Tabs */}
          <div className="flex items-center bg-slate-900/90 p-0.5 rounded-xl border border-slate-700/80 text-xs">
            {['ALL', 'PIPELINE', 'FAILURES', 'SECURITY'].map((tab) => (
              <button
                key={tab}
                onClick={() => setFilter(tab)}
                className={`px-2 py-1 rounded-lg font-mono text-[11px] transition-colors ${
                  filter === tab
                    ? 'bg-cyan-500/20 text-cyan-300 font-semibold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {onClearLog && (
            <button
              onClick={onClearLog}
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
              title="Clear log"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Log Stream */}
      <div className="space-y-1.5 max-h-[420px] overflow-y-auto pr-1">
        {filteredLog.length === 0 ? (
          <div className="text-center py-10 text-slate-500 text-xs font-mono">
            <Radio className="w-5 h-5 mx-auto mb-2 text-slate-600" />
            <p>Waiting for real-time events...</p>
            <p className="text-[11px] mt-1 text-slate-600">
              Events will appear here as webhooks are processed
            </p>
          </div>
        ) : (
          filteredLog.map((entry) => <LogEntry key={entry.id} entry={entry} />)
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono px-1 pt-1 border-t border-slate-800/60">
        <span>
          {filteredLog.length} event{filteredLog.length !== 1 ? 's' : ''} in stream
        </span>
        <span className="flex items-center gap-1">
          <GitCommit className="w-3 h-3 text-cyan-500" />
          WebSocket /api/v1/ws
        </span>
      </div>
    </div>
  );
}

