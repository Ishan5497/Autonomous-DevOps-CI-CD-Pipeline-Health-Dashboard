import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../App';
import { api } from '../services/api';

vi.mock('../services/api', () => ({
  api: {
    getDashboardSummary: vi.fn(),
    getPipelineHealth: vi.fn(),
    seedDemoData: vi.fn(),
    simulatePush: vi.fn(),
    simulatePullRequest: vi.fn(),
    simulateBuildStatus: vi.fn(),
    scanDiff: vi.fn(),
  },
}));

describe('App Integration Test', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.getDashboardSummary.mockResolvedValue({
      health: {
        total_runs: 10,
        successful_runs: 8,
        failed_runs: 2,
        running_runs: 0,
        success_rate_percent: 80.0,
        health_grade: 'B',
        risk_level: 'LOW',
        total_security_findings: 0,
        critical_vulnerabilities: 0,
        mttr_display: '1.2 min',
      },
      recent_runs: [
        {
          id: 1,
          pipeline_id: 'pipe-app-1',
          branch: 'main',
          status: 'success',
          stage: 'deploy',
          duration_seconds: 30,
          author: 'ci-bot',
          commit_sha: 'sha111',
          commit_message: 'initial release',
          created_at: new Date().toISOString(),
        },
      ],
      recent_pull_requests: [
        {
          id: 1,
          pr_number: 10,
          title: 'test pr',
          state: 'open',
          action: 'opened',
        },
      ],
      recent_findings: [],
      system_status: { status: 'OPERATIONAL' },
    });

    api.getPipelineHealth.mockResolvedValue({
      recommendations: [
        {
          id: 'REC-01',
          priority: 'HIGH',
          title: 'Flaky test detected',
          message: 'Review retry settings',
          suggested_action: 'Enable test retries in GitHub Actions',
        },
      ],
    });
  });

  it('renders application brand, navigation, and summary data', async () => {
    render(<App />);

    expect(screen.getByText('AUTO-DEVOPS')).toBeInTheDocument();
    expect(screen.getByText('DevOps Operations Center')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getAllByText(/80%/)[0]).toBeInTheDocument();
      expect(screen.getByText('Grade B')).toBeInTheDocument();
      expect(screen.getByText('pipe-app-1')).toBeInTheDocument();
    });
  });

  it('navigates through navigation tabs smoothly', async () => {
    render(<App />);

    // Switch to Pipelines tab
    fireEvent.click(screen.getByRole('button', { name: /Pipeline Executions/i }));
    expect(screen.getByText(/Real-Time Pipeline Executions/i)).toBeInTheDocument();

    // Switch to Static Diff Scanner tab
    fireEvent.click(screen.getByRole('button', { name: /Static Diff Scanner/i }));
    expect(screen.getByText(/Static Analysis Diff Scanner/i)).toBeInTheDocument();

    // Switch to Webhook Simulator tab
    fireEvent.click(screen.getByRole('button', { name: /Webhook Simulator/i }));
    expect(screen.getByText(/Interactive Webhook Simulation Center/i)).toBeInTheDocument();

    // Switch to AI Guardrails tab
    fireEvent.click(screen.getByRole('button', { name: /AI Guardrails/i }));
    await waitFor(() => {
      expect(screen.getByText(/Autonomous AI Guardrails/i)).toBeInTheDocument();
      expect(screen.getByText('Flaky test detected')).toBeInTheDocument();
    });
  });
});
