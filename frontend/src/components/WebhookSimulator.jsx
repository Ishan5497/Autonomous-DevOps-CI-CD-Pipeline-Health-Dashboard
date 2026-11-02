import React, { useState } from 'react';
import {
  Radio,
  Send,
  GitCommit,
  GitPullRequest,
  CheckCircle2,
  XCircle,
  Terminal,
} from 'lucide-react';
import { api } from '../services/api';

export default function WebhookSimulator({ onEventSent }) {
  const [activeSim, setActiveSim] = useState('push');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [consoleOutput, setConsoleOutput] = useState({
    status: 'IDLE',
    data: { message: 'Ready to dispatch simulated GitHub / GitLab webhook payloads.' },
  });

  const handleSimulatePush = async (hasSecret = false) => {
    setIsSubmitting(true);
    const commitSha = Math.random().toString(16).substring(2, 10);
    const payload = {
      repository: 'Ishan5497/Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard',
      ref: 'refs/heads/main',
      commit_sha: commitSha,
      commit_message: hasSecret
        ? 'fix(auth): fast-patch with leaked token'
        : 'feat(core): optimize automated deployment worker',
      author: 'ishan-dev',
      diff: hasSecret
        ? '+++ b/keys.py\n+AWS_KEY = "AKIAIOSFODNN7EXAMPLE"'
        : '+++ b/worker.py\n+TIMEOUT = 30',
    };

    try {
      const res = await api.simulatePush(payload);
      setConsoleOutput({ status: '200 OK (PUSH)', data: res });
      if (onEventSent) onEventSent();
    } catch (err) {
      setConsoleOutput({ status: 'ERROR', data: { error: err.message } });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSimulatePR = async () => {
    setIsSubmitting(true);
    const prNum = Math.floor(Math.random() * 80) + 10;
    const payload = {
      repository: 'Ishan5497/Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard',
      pr_number: prNum,
      title: `feat: autonomous self-healing worker #${prNum}`,
      action: 'opened',
      author: 'ishan-dev',
      head_branch: `feature/healing-engine-${prNum}`,
      base_branch: 'main',
      head_sha: Math.random().toString(16).substring(2, 12),
      diff: null,
    };

    try {
      const res = await api.simulatePullRequest(payload);
      setConsoleOutput({ status: '200 OK (PULL_REQUEST)', data: res });
      if (onEventSent) onEventSent();
    } catch (err) {
      setConsoleOutput({ status: 'ERROR', data: { error: err.message } });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSimulateBuild = async (buildStatus) => {
    setIsSubmitting(true);
    const pipeId = `pipe-${Math.floor(Math.random() * 9000) + 1000}`;
    const payload = {
      repository: 'Ishan5497/Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard',
      pipeline_id: pipeId,
      branch: 'main',
      commit_sha: Math.random().toString(16).substring(2, 10),
      commit_message: 'Automated matrix build validation',
      author: 'github-actions[bot]',
      status: buildStatus,
      stage: buildStatus === 'failed' ? 'test' : 'deploy',
      duration_seconds: buildStatus === 'failed' ? 14.8 : 42.6,
      failure_reason:
        buildStatus === 'failed'
          ? 'Integration test failed: DB connection refused on 5432'
          : null,
    };

    try {
      const res = await api.simulateBuildStatus(payload);
      setConsoleOutput({ status: `200 OK (BUILD: ${buildStatus.toUpperCase()})`, data: res });
      if (onEventSent) onEventSent();
    } catch (err) {
      setConsoleOutput({ status: 'ERROR', data: { error: err.message } });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-6 space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <Radio className="w-4 h-4 text-cyan-400" />
            Interactive Webhook Simulation Center
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Test automated payload ingestion, pipeline transitions, and diff scanning gates
          </p>
        </div>
        <span className="text-[11px] font-mono text-cyan-400 bg-cyan-500/10 border border-cyan-500/20 px-2 py-0.5 rounded-full">
          POST /api/v1/webhooks/*
        </span>
      </div>

      {/* Simulator Action Buttons */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2.5">
        <button
          onClick={() => handleSimulatePush(false)}
          disabled={isSubmitting}
          className="flex items-center gap-2 p-3 rounded-xl bg-slate-900 border border-slate-700 hover:border-cyan-500/50 hover:bg-slate-800 text-left transition-all group disabled:opacity-50"
        >
          <span className="w-2 h-2 rounded-full bg-cyan-400 shadow-sm shadow-cyan-400 group-hover:scale-125 transition-transform" />
          <div className="truncate">
            <div className="text-xs font-semibold text-slate-200">Safe Push</div>
            <div className="text-[10px] text-slate-400 font-mono">Clean commit diff</div>
          </div>
        </button>

        <button
          onClick={() => handleSimulatePush(true)}
          disabled={isSubmitting}
          className="flex items-center gap-2 p-3 rounded-xl bg-slate-900 border border-slate-700 hover:border-rose-500/50 hover:bg-slate-800 text-left transition-all group disabled:opacity-50"
        >
          <span className="w-2 h-2 rounded-full bg-rose-400 shadow-sm shadow-rose-400 group-hover:scale-125 transition-transform" />
          <div className="truncate">
            <div className="text-xs font-semibold text-rose-300">Push (Secret Leak)</div>
            <div className="text-[10px] text-slate-400 font-mono">Contains AWS key</div>
          </div>
        </button>

        <button
          onClick={handleSimulatePR}
          disabled={isSubmitting}
          className="flex items-center gap-2 p-3 rounded-xl bg-slate-900 border border-slate-700 hover:border-purple-500/50 hover:bg-slate-800 text-left transition-all group disabled:opacity-50"
        >
          <span className="w-2 h-2 rounded-full bg-purple-400 shadow-sm shadow-purple-400 group-hover:scale-125 transition-transform" />
          <div className="truncate">
            <div className="text-xs font-semibold text-slate-200">Pull Request</div>
            <div className="text-[10px] text-slate-400 font-mono">PR opened event</div>
          </div>
        </button>

        <button
          onClick={() => handleSimulateBuild('success')}
          disabled={isSubmitting}
          className="flex items-center gap-2 p-3 rounded-xl bg-slate-900 border border-slate-700 hover:border-emerald-500/50 hover:bg-slate-800 text-left transition-all group disabled:opacity-50"
        >
          <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400 group-hover:scale-125 transition-transform" />
          <div className="truncate">
            <div className="text-xs font-semibold text-slate-200">Passing Build</div>
            <div className="text-[10px] text-slate-400 font-mono">Status: success</div>
          </div>
        </button>

        <button
          onClick={() => handleSimulateBuild('failed')}
          disabled={isSubmitting}
          className="flex items-center gap-2 p-3 rounded-xl bg-slate-900 border border-slate-700 hover:border-amber-500/50 hover:bg-slate-800 text-left transition-all group disabled:opacity-50"
        >
          <span className="w-2 h-2 rounded-full bg-amber-400 shadow-sm shadow-amber-400 group-hover:scale-125 transition-transform" />
          <div className="truncate">
            <div className="text-xs font-semibold text-slate-200">Failing Build</div>
            <div className="text-[10px] text-slate-400 font-mono">Status: failed</div>
          </div>
        </button>
      </div>

      {/* Real-time Response Output Console */}
      <div className="rounded-xl border border-slate-800 bg-[#060911] overflow-hidden">
        <div className="bg-slate-900/90 px-4 py-2 border-b border-slate-800 flex items-center justify-between text-[11px] font-mono text-slate-400">
          <span className="flex items-center gap-1.5">
            <Terminal className="w-3.5 h-3.5 text-cyan-400" />
            FastAPI Response Telemetry
          </span>
          <span
            className={`font-semibold ${
              consoleOutput.status.includes('OK')
                ? 'text-emerald-400'
                : consoleOutput.status === 'IDLE'
                ? 'text-slate-400'
                : 'text-rose-400'
            }`}
          >
            {consoleOutput.status}
          </span>
        </div>

        <pre className="p-4 text-xs font-mono text-cyan-300 overflow-x-auto max-h-48 leading-relaxed">
          {JSON.stringify(consoleOutput.data, null, 2)}
        </pre>
      </div>
    </div>
  );
}
