import React from 'react';
import {
  LayoutDashboard,
  GitBranch,
  ShieldAlert,
  Radio,
  Sparkles,
  ExternalLink,
  Cpu,
  Layers,
  ChevronRight,
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, systemStatus }) {
  const navItems = [
    { id: 'dashboard', label: 'Operations Center', icon: LayoutDashboard, badge: null },
    { id: 'pipelines', label: 'Pipeline Executions', icon: GitBranch, badge: 'Live' },
    { id: 'scanner', label: 'Static Diff Scanner', icon: ShieldAlert, badge: 'Sec' },
    { id: 'simulator', label: 'Webhook Simulator', icon: Radio, badge: null },
    { id: 'recommendations', label: 'AI Guardrails', icon: Sparkles, badge: 'Autonomous' },
  ];

  return (
    <aside className="w-64 bg-[#0a0f1d] border-r border-slate-800/80 flex flex-col shrink-0 h-screen sticky top-0">
      {/* Brand & Logo */}
      <div className="p-5 border-b border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 shadow-lg shadow-cyan-500/20 text-slate-950 font-bold">
            <Layers className="w-5 h-5 text-slate-950" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-emerald-400 ring-2 ring-[#0a0f1d] animate-ping" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-emerald-400 ring-2 ring-[#0a0f1d]" />
          </div>
          <div>
            <h1 className="font-semibold text-base text-slate-100 tracking-tight flex items-center gap-1.5">
              AUTO-DEVOPS
            </h1>
            <p className="text-[11px] font-mono text-cyan-400/80 uppercase tracking-wider">
              Health Monitor v1.0
            </p>
          </div>
        </div>
      </div>

      {/* Nav List */}
      <div className="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto">
        <p className="px-3 pb-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
          Telemetry & Control
        </p>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all duration-200 group ${
                isActive
                  ? 'bg-gradient-to-r from-cyan-500/15 to-blue-500/10 text-cyan-300 border border-cyan-500/30 shadow-sm shadow-cyan-500/10'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={`w-4 h-4 transition-colors ${
                    isActive ? 'text-cyan-400' : 'text-slate-400 group-hover:text-slate-200'
                  }`}
                />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-mono uppercase font-semibold ${
                    isActive
                      ? 'bg-cyan-500/20 text-cyan-300'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}

        <div className="pt-6">
          <p className="px-3 pb-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
            Quick Links
          </p>
          <a
            href="http://127.0.0.1:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="w-full flex items-center justify-between px-3.5 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <ExternalLink className="w-4 h-4 text-slate-400" />
              <span>Swagger API Docs</span>
            </div>
            <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
          </a>
        </div>
      </div>

      {/* System Status Footer */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-900/40">
        <div className="bg-slate-900/80 rounded-xl p-3 border border-slate-800/80 text-[11px] space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-slate-400 flex items-center gap-1.5 font-medium">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" />
              FastAPI Engine
            </span>
            <span className="flex items-center gap-1 text-emerald-400 font-mono text-[10px]">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              ONLINE
            </span>
          </div>
          <div className="flex items-center justify-between text-slate-400 font-mono text-[10px]">
            <span>DB ENGINE:</span>
            <span className="text-slate-300">SQLite ORM</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
