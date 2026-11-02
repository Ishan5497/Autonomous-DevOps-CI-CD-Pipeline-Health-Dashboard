import axios from 'axios';

// Detect whether running under custom VITE_API_URL, Vite dev proxy, or directly against backend
const getApiBaseUrl = () => {
  if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  if (typeof window !== 'undefined') {
    if (window.location.port === '5173') {
      return ''; // Uses Vite proxy to http://127.0.0.1:8000
    }
    if (window.location.origin && window.location.origin.includes('8000')) {
      return window.location.origin;
    }
  }
  return 'http://127.0.0.1:8000';
};

const API_BASE_URL = getApiBaseUrl();

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Response interceptor for consistent error handling across all API calls
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'Network communication error';
    return Promise.reject(new Error(detail));
  }
);

export const api = {
  // Summary & Health
  async getDashboardSummary() {
    const res = await client.get('/api/v1/dashboard/summary');
    return res.data;
  },

  async getPipelineHealth() {
    const res = await client.get('/api/v1/pipeline/health');
    return res.data;
  },

  async seedDemoData() {
    const res = await client.post('/api/v1/dashboard/seed-demo-data');
    return res.data;
  },

  // Pipeline Runs & Pull Requests
  async getPipelineRuns(params = {}) {
    const res = await client.get('/api/v1/pipeline/runs', { params });
    return res.data;
  },

  async getPullRequests(params = {}) {
    const res = await client.get('/api/v1/pipeline/pull-requests', { params });
    return res.data;
  },

  // Security Findings & Diff Scanning
  async getSecurityFindings(params = {}) {
    const res = await client.get('/api/v1/security/findings', { params });
    return res.data;
  },

  async scanDiff(diffText, filePath = 'patch.diff', persist = true) {
    const res = await client.post(`/api/v1/security/scan-diff?persist=${persist}`, {
      diff: diffText,
      file_path: filePath,
      commit_sha: Math.random().toString(16).substring(2, 10),
      repository: 'Ishan5497/Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard',
    });
    return res.data;
  },

  async resolveFinding(findingId) {
    const res = await client.delete(`/api/v1/security/findings/${findingId}`);
    return res.data;
  },

  // Webhook Simulations
  async simulatePush(payload) {
    const res = await client.post('/api/v1/webhooks/simulate/push', payload);
    return res.data;
  },

  async simulatePullRequest(payload) {
    const res = await client.post('/api/v1/webhooks/simulate/pull-request', payload);
    return res.data;
  },

  async simulateBuildStatus(payload) {
    const res = await client.post('/api/v1/webhooks/simulate/build-status', payload);
    return res.data;
  },

  async getWebhookEvents(params = {}) {
    const res = await client.get('/api/v1/webhooks/events', { params });
    return res.data;
  },
};

export default api;
