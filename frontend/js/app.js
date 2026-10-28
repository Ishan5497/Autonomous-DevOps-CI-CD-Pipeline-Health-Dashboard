/**
 * Autonomous DevOps & CI/CD Pipeline Health Dashboard
 * Frontend Client Controller
 */

const API_BASE = window.location.origin.includes('8000') 
  ? window.location.origin 
  : 'http://127.0.0.1:8000';

const SAMPLE_LEAK_DIFF = `diff --git a/config/aws.py b/config/aws.py
--- a/config/aws.py
+++ b/config/aws.py
@@ -5,3 +5,3 @@
-AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
+AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
+DATABASE_URL = "postgres://root:SuperSecretP@ssw0rd@db.internal:5432/prod"
`;

const SAMPLE_EVAL_SQLI_DIFF = `diff --git a/server/handler.py b/server/handler.py
--- a/server/handler.py
+++ b/server/handler.py
@@ -14,4 +14,5 @@
 def execute_query(cursor, user_id, raw_cmd):
+    # Dangerous eval usage
+    result = eval(raw_cmd)
+    # SQL injection vulnerability
+    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
+    return result
`;

// DOM elements
const kpiGradeBadge = document.getElementById('kpi-grade-badge');
const kpiGradeText = document.getElementById('kpi-grade-text');
const kpiRiskBadge = document.getElementById('kpi-risk-badge');
const kpiGradeCaption = document.getElementById('kpi-grade-caption');
const kpiSuccessRate = document.getElementById('kpi-success-rate');
const kpiSuccessFill = document.getElementById('kpi-success-fill');
const kpiRunsSummary = document.getElementById('kpi-runs-summary');
const kpiMttr = document.getElementById('kpi-mttr');
const kpiFindingsCount = document.getElementById('kpi-findings-count');
const kpiCriticalBadge = document.getElementById('kpi-critical-badge');
const recsContainer = document.getElementById('recommendations-container');
const recsCount = document.getElementById('recs-count');
const simResponseOutput = document.getElementById('sim-response-output');
const consoleStatus = document.getElementById('console-status');
const diffTextarea = document.getElementById('diff-textarea');
const scanResultsDisplay = document.getElementById('scan-results-display');
const scanStatusTitle = document.getElementById('scan-status-title');
const scanMetaPill = document.getElementById('scan-meta-pill');
const scanFindingsList = document.getElementById('scan-findings-list');
const runsTableBody = document.getElementById('runs-table-body');
const runsCountBadge = document.getElementById('runs-count-badge');
const findingsFeedBody = document.getElementById('findings-feed-body');
const findingsCountBadge = document.getElementById('findings-count-badge');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  fetchDashboardSummary();
  // Auto-refresh every 12 seconds
  setInterval(fetchDashboardSummary, 12000);
});

function setupEventListeners() {
  document.getElementById('btn-refresh-all').addEventListener('click', fetchDashboardSummary);
  document.getElementById('btn-seed-data').addEventListener('click', seedDemoData);

  // Simulator buttons
  document.getElementById('sim-btn-push').addEventListener('click', () => simulatePush(false));
  document.getElementById('sim-btn-push-vuln').addEventListener('click', () => simulatePush(true));
  document.getElementById('sim-btn-pr').addEventListener('click', simulatePullRequest);
  document.getElementById('sim-btn-build').addEventListener('click', () => simulateBuild('success'));
  document.getElementById('sim-btn-build-fail').addEventListener('click', () => simulateBuild('failed'));

  // Scanner buttons
  document.getElementById('btn-load-vulnerable-sample').addEventListener('click', () => {
    diffTextarea.value = SAMPLE_LEAK_DIFF;
  });
  document.getElementById('btn-load-eval-sample').addEventListener('click', () => {
    diffTextarea.value = SAMPLE_EVAL_SQLI_DIFF;
  });
  document.getElementById('btn-run-scan').addEventListener('click', runStaticScan);
}

async function fetchDashboardSummary() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/dashboard/summary`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const data = await res.json();
    renderDashboard(data);
  } catch (err) {
    console.warn('Dashboard fetch error:', err);
  }
}

function renderDashboard(data) {
  const { health, recent_runs, recent_findings } = data;

  // Grade Card
  kpiGradeText.textContent = health.health_grade;
  kpiGradeBadge.textContent = health.health_grade;
  kpiRiskBadge.textContent = `${health.risk_level} RISK`;
  kpiRiskBadge.className = `kpi-sub-badge badge-${health.risk_level === 'CRITICAL' ? 'danger' : health.risk_level === 'HIGH' ? 'warning' : 'success'}`;

  // Success Rate Card
  kpiSuccessRate.textContent = `${health.success_rate_percent}%`;
  kpiSuccessFill.style.width = `${health.success_rate_percent}%`;
  kpiRunsSummary.textContent = `${health.successful_runs} passed / ${health.total_runs} total runs`;

  // MTTR
  kpiMttr.textContent = health.mttr_display;

  // Security Findings
  kpiFindingsCount.textContent = health.total_security_findings;
  kpiCriticalBadge.textContent = `${health.critical_vulnerabilities} Critical`;
  kpiCriticalBadge.className = `kpi-sub-badge ${health.critical_vulnerabilities > 0 ? 'badge-danger' : 'badge-success'}`;

  // Recommendations
  renderRecommendations(health.recommendations);

  // Runs Table
  renderRunsTable(recent_runs);

  // Findings Feed
  renderFindingsFeed(recent_findings);
}

function renderRecommendations(recommendations) {
  recsCount.textContent = `${recommendations.length} Active`;
  if (!recommendations || recommendations.length === 0) {
    recsContainer.innerHTML = '<div class="rec-card glass-panel"><p class="text-muted">No active recommendations.</p></div>';
    return;
  }

  recsContainer.innerHTML = recommendations.map(rec => `
    <div class="rec-card glass-panel priority-${rec.priority}">
      <div class="rec-header">
        <span class="badge badge-${rec.priority === 'HIGH' ? 'danger' : rec.priority === 'MEDIUM' ? 'warning' : 'info'}">${rec.type}</span>
        <h4>${escapeHtml(rec.title)}</h4>
      </div>
      <p class="text-muted" style="font-size: 0.85rem;">${escapeHtml(rec.message)}</p>
      <div class="rec-action">
        <strong>Suggested Action:</strong> ${escapeHtml(rec.suggested_action)}
      </div>
    </div>
  `).join('');
}

function renderRunsTable(runs) {
  runsCountBadge.textContent = `${runs.length} Runs`;
  if (!runs || runs.length === 0) {
    runsTableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No pipeline runs recorded yet. Click "Seed Demo Data" above.</td></tr>`;
    return;
  }

  runsTableBody.innerHTML = runs.map(run => {
    const isSuccess = run.status.toLowerCase() === 'success';
    const isFailed = run.status.toLowerCase() === 'failed';
    const statusBadge = isSuccess 
      ? '<span class="badge badge-success">PASSED</span>'
      : isFailed
      ? '<span class="badge badge-danger">FAILED</span>'
      : '<span class="badge badge-info">RUNNING</span>';

    return `
      <tr>
        <td>${statusBadge}</td>
        <td>
          <strong>${escapeHtml(run.pipeline_id || 'manual')}</strong>
          <div class="text-dim" style="font-size: 0.75rem;">${escapeHtml((run.commit_sha || '').substring(0, 8))} • ${escapeHtml(run.commit_message || 'No message')}</div>
        </td>
        <td><span class="badge badge-purple">${escapeHtml(run.branch)}</span></td>
        <td>${escapeHtml(run.stage)}</td>
        <td>${run.duration_seconds}s</td>
        <td>${escapeHtml(run.author || 'system')}</td>
      </tr>
    `;
  }).join('');
}

function renderFindingsFeed(findings) {
  findingsCountBadge.textContent = `${findings.length} Findings`;
  if (!findings || findings.length === 0) {
    findingsFeedBody.innerHTML = '<div class="text-center text-muted empty-feed">No security findings recorded yet. Safe diffs!</div>';
    return;
  }

  findingsFeedBody.innerHTML = findings.map(f => `
    <div class="finding-item sev-${f.severity}">
      <div class="finding-title-row">
        <span class="finding-title">${escapeHtml(f.rule_name)}</span>
        <span class="badge badge-${f.severity === 'CRITICAL' ? 'danger' : f.severity === 'HIGH' ? 'warning' : 'info'}">${f.severity}</span>
      </div>
      <div class="text-muted" style="font-size: 0.78rem;">${escapeHtml(f.file_path || 'diff')} : Line ${f.line_number || 1}</div>
      <code class="finding-code">${escapeHtml(f.snippet_redacted)}</code>
      <div class="text-dim" style="font-size: 0.75rem; margin-top: 0.25rem;">${escapeHtml(f.recommendation || f.description)}</div>
    </div>
  `).join('');
}

// Simulator Actions
async function simulatePush(hasVulnerability) {
  const commitSha = Math.random().toString(16).substring(2, 10);
  const payload = {
    repository: "Ishan5497/Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard",
    ref: "refs/heads/main",
    commit_sha: commitSha,
    commit_message: hasVulnerability ? "fix: urgent patch with hardcoded token" : "feat: optimize pipeline health metrics",
    author: "ishan-dev",
    diff: hasVulnerability ? SAMPLE_LEAK_DIFF : null
  };

  await sendSimulatorRequest('/api/v1/webhooks/simulate/push', payload);
}

async function simulatePullRequest() {
  const prNum = Math.floor(Math.random() * 80) + 10;
  const payload = {
    repository: "Ishan5497/Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard",
    pr_number: prNum,
    title: `feat: autonomous pipeline self-healing worker #${prNum}`,
    action: "opened",
    author: "ishan-dev",
    head_branch: `feature/patch-${prNum}`,
    base_branch: "main",
    head_sha: Math.random().toString(16).substring(2, 12),
    diff: null
  };

  await sendSimulatorRequest('/api/v1/webhooks/simulate/pull-request', payload);
}

async function simulateBuild(status) {
  const pipeId = `pipe-${Math.floor(Math.random() * 9000) + 1000}`;
  const payload = {
    repository: "Ishan5497/Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard",
    pipeline_id: pipeId,
    branch: "main",
    commit_sha: Math.random().toString(16).substring(2, 10),
    commit_message: "Automated verification build",
    author: "github-actions[bot]",
    status: status,
    stage: status === 'failed' ? 'test' : 'deploy',
    duration_seconds: status === 'failed' ? 14.2 : 46.8,
    failure_reason: status === 'failed' ? 'AssertionError in test_regression_suite.py: timeout after 10000ms' : null
  };

  await sendSimulatorRequest('/api/v1/webhooks/simulate/build-status', payload);
}

async function seedDemoData() {
  await sendSimulatorRequest('/api/v1/dashboard/seed-demo-data', {});
}

async function sendSimulatorRequest(endpoint, body) {
  consoleStatus.textContent = 'DISPATCHING...';
  consoleStatus.style.color = '#f59e0b';

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    simResponseOutput.textContent = JSON.stringify(data, null, 2);
    consoleStatus.textContent = '200 OK';
    consoleStatus.style.color = '#10b981';
    fetchDashboardSummary();
  } catch (err) {
    simResponseOutput.textContent = `Error: ${err.message}`;
    consoleStatus.textContent = 'FAILED';
    consoleStatus.style.color = '#f43f5e';
  }
}

// Live Static Diff Scanner
async function runStaticScan() {
  const diff = diffTextarea.value.trim();
  if (!diff) {
    alert('Please enter or load a Git diff first.');
    return;
  }

  scanResultsDisplay.style.display = 'block';
  scanStatusTitle.textContent = 'Scanning diff...';

  try {
    const res = await fetch(`${API_BASE}/api/v1/security/scan-diff?persist=true`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        diff: diff,
        file_path: "patch.diff",
        commit_sha: Math.random().toString(16).substring(2, 10),
        repository: "Ishan5497/Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard"
      })
    });
    const result = await res.json();

    if (result.is_safe) {
      scanStatusTitle.textContent = '✓ Diff Clean & Safe';
      scanStatusTitle.style.color = '#10b981';
      scanMetaPill.className = 'badge badge-success';
      scanMetaPill.textContent = '0 Findings';
      scanFindingsList.innerHTML = '<p class="text-muted" style="font-size: 0.85rem;">No hardcoded secrets or dangerous patterns detected.</p>';
    } else {
      scanStatusTitle.textContent = `⚠ ${result.findings_count} Security Finding(s) Detected`;
      scanStatusTitle.style.color = '#f43f5e';
      scanMetaPill.className = 'badge badge-danger';
      scanMetaPill.textContent = `${result.critical_count} Critical, ${result.high_count} High`;

      scanFindingsList.innerHTML = result.findings.map(f => `
        <div class="finding-item sev-${f.severity}">
          <div class="finding-title-row">
            <span class="finding-title">${escapeHtml(f.rule_name)}</span>
            <span class="badge badge-${f.severity === 'CRITICAL' ? 'danger' : 'warning'}">${f.severity}</span>
          </div>
          <p style="font-size: 0.8rem; color: #cbd5e1;">${escapeHtml(f.description)}</p>
          <code class="finding-code">${escapeHtml(f.snippet_redacted)}</code>
          <div class="text-dim" style="font-size: 0.75rem; margin-top: 0.3rem;">
            <strong>Recommendation:</strong> ${escapeHtml(f.recommendation || 'Remediate immediately')}
          </div>
        </div>
      `).join('');
    }

    // Refresh dashboard to show persisted findings and updated grade
    fetchDashboardSummary();
  } catch (err) {
    scanStatusTitle.textContent = `Error: ${err.message}`;
    scanStatusTitle.style.color = '#f43f5e';
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
