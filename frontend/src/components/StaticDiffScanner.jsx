import React, { useState } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  Play,
  FileCode,
  AlertTriangle,
  Flame,
  CheckCircle2,
  Copy,
  Check,
} from 'lucide-react';
import { api } from '../services/api';

const SAMPLE_LEAK_DIFF = `diff --git a/services/storage.py b/services/storage.py
--- a/services/storage.py
+++ b/services/storage.py
@@ -10,3 +10,4 @@
-def get_s3_client():
-    return boto3.client('s3')
+def get_s3_client():
+    # Hardcoded AWS credential leak
+    return boto3.client('s3', aws_access_key_id='AKIAIOSFODNN7EXAMPLE')
`;

const SAMPLE_BUG_DIFF = `diff --git a/database/query.py b/database/query.py
--- a/database/query.py
+++ b/database/query.py
@@ -15,4 +15,5 @@
 def execute_user_query(cursor, user_id, raw_code):
+    # Dangerous eval usage
+    payload = eval(raw_code)
+    # SQL Injection flaw
+    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
+    return payload
`;

export default function StaticDiffScanner({ onScanComplete }) {
  const [diffText, setDiffText] = useState(SAMPLE_LEAK_DIFF);
  const [filePath, setFilePath] = useState('services/storage.py');
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [copiedIndex, setCopiedIndex] = useState(null);

  const handleScan = async () => {
    if (!diffText.trim()) return;
    setIsScanning(true);
    try {
      const result = await api.scanDiff(diffText, filePath, true);
      setScanResult(result);
      if (onScanComplete) {
        onScanComplete();
      }
    } catch (err) {
      console.error('Scan error:', err);
    } finally {
      setIsScanning(false);
    }
  };

  const handleCopySnippet = (snippet, idx) => {
    navigator.clipboard.writeText(snippet);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className="glass-panel rounded-2xl p-6 space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            Static Analysis Diff Scanner & Secret Redaction Guard
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Intercepts hardcoded secrets, dangerous eval() calls, and SQL injection flaws before deployment
          </p>
        </div>

        {/* Preload Samples */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setDiffText(SAMPLE_LEAK_DIFF);
              setFilePath('services/storage.py');
              setScanResult(null);
            }}
            className="px-2.5 py-1 rounded-lg text-xs font-mono bg-slate-900 border border-slate-700/80 text-slate-300 hover:text-cyan-400 hover:border-cyan-500/40 transition-colors"
          >
            Load AWS Key Diff
          </button>
          <button
            onClick={() => {
              setDiffText(SAMPLE_BUG_DIFF);
              setFilePath('database/query.py');
              setScanResult(null);
            }}
            className="px-2.5 py-1 rounded-lg text-xs font-mono bg-slate-900 border border-slate-700/80 text-slate-300 hover:text-amber-400 hover:border-amber-500/40 transition-colors"
          >
            Load eval() & SQLi Diff
          </button>
        </div>
      </div>

      {/* Editor & Actions */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs font-mono text-slate-400 px-1">
          <span className="flex items-center gap-1.5">
            <FileCode className="w-3.5 h-3.5 text-cyan-400" />
            File: {filePath}
          </span>
          <span>Unified Git Diff Format</span>
        </div>

        <div className="relative rounded-xl border border-slate-800 bg-[#060911] overflow-hidden focus-within:border-cyan-500/40 transition-colors">
          <textarea
            value={diffText}
            onChange={(e) => setDiffText(e.target.value)}
            rows={8}
            className="w-full bg-transparent p-4 font-mono text-xs text-slate-200 focus:outline-none resize-y selection:bg-cyan-500/30"
            placeholder="Paste raw Git diff or patch code here..."
          />
        </div>

        <div className="flex justify-end gap-3 pt-1">
          <button
            onClick={handleScan}
            disabled={isScanning || !diffText.trim()}
            className="flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-cyan-500 to-blue-600 text-slate-950 hover:brightness-110 active:scale-95 transition-all shadow-md shadow-cyan-500/15 disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 fill-current ${isScanning ? 'animate-spin' : ''}`} />
            <span>{isScanning ? 'Analyzing Diff...' : 'Run Static Scan & Guardrail'}</span>
          </button>
        </div>
      </div>

      {/* Results Display */}
      {scanResult && (
        <div className="mt-4 pt-4 border-t border-slate-800/80 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {scanResult.is_safe ? (
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-rose-400" />
              )}
              <h4 className="text-sm font-semibold text-slate-100">
                {scanResult.is_safe ? 'Static Quality Gate Passed' : 'Security Flaws Detected'}
              </h4>
            </div>

            <div className="flex items-center gap-2 font-mono text-xs">
              <span className="px-2 py-0.5 rounded-full bg-slate-900 border border-slate-700 text-slate-300">
                {scanResult.scanned_lines} lines scanned
              </span>
              <span
                className={`px-2 py-0.5 rounded-full border font-semibold ${
                  scanResult.is_safe
                    ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                    : 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                }`}
              >
                {scanResult.findings_count} Finding(s) (
                {scanResult.critical_count} Critical, {scanResult.high_count} High)
              </span>
            </div>
          </div>

          {scanResult.findings.length === 0 ? (
            <div className="bg-emerald-950/20 border border-emerald-500/30 rounded-xl p-3 text-xs text-emerald-300 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>Clean commit diff. No hardcoded secrets or dangerous functions found.</span>
            </div>
          ) : (
            <div className="space-y-2.5">
              {scanResult.findings.map((f, idx) => (
                <div
                  key={idx}
                  className={`rounded-xl p-3.5 border transition-all text-xs space-y-2 ${
                    f.severity === 'CRITICAL'
                      ? 'bg-rose-950/20 border-rose-500/40'
                      : f.severity === 'HIGH'
                      ? 'bg-amber-950/20 border-amber-500/40'
                      : 'bg-purple-950/20 border-purple-500/40'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-0.5 rounded font-mono text-[10px] font-bold ${
                          f.severity === 'CRITICAL'
                            ? 'bg-rose-500 text-slate-950'
                            : 'bg-amber-500 text-slate-950'
                        }`}
                      >
                        {f.severity}
                      </span>
                      <span className="font-semibold text-slate-200">
                        {f.rule_name} ({f.rule_id})
                      </span>
                    </div>
                    <span className="font-mono text-[11px] text-slate-400">
                      Line {f.line_number || 1} in {f.file_path || filePath}
                    </span>
                  </div>

                  <p className="text-slate-300 text-xs">{f.description}</p>

                  {/* Redacted Snippet */}
                  <div className="relative bg-[#060911] p-2.5 rounded-lg border border-slate-800 font-mono text-xs text-rose-300 flex items-center justify-between">
                    <code>{f.snippet_redacted}</code>
                    <button
                      onClick={() => handleCopySnippet(f.snippet_redacted, idx)}
                      className="text-slate-400 hover:text-slate-200 transition-colors"
                      title="Copy redacted snippet"
                    >
                      {copiedIndex === idx ? (
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>

                  <div className="text-[11px] text-cyan-300/90 font-mono bg-cyan-950/30 p-2 rounded border border-cyan-500/20">
                    <strong>Autonomous Recommendation:</strong> {f.recommendation}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
