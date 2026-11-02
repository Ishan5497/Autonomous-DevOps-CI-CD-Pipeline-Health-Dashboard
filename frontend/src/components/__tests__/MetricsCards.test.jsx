import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MetricsCards from '../MetricsCards';

describe('MetricsCards Component', () => {
  it('renders correctly with default empty props', () => {
    render(<MetricsCards />);
    expect(screen.getByText(/Total Builds/i)).toBeInTheDocument();
    expect(screen.getByText(/Success Rate/i)).toBeInTheDocument();
    expect(screen.getByText(/Active PRs/i)).toBeInTheDocument();
    expect(screen.getByText(/Security Flags/i)).toBeInTheDocument();
    expect(screen.getByText(/MTTR/i)).toBeInTheDocument();
  });

  it('renders provided health metrics accurately', () => {
    const mockHealth = {
      total_runs: 42,
      successful_runs: 38,
      failed_runs: 4,
      running_runs: 0,
      success_rate_percent: 90.5,
      health_grade: 'A',
      risk_level: 'LOW',
      total_security_findings: 3,
      critical_vulnerabilities: 1,
      mttr_display: '2.5 min',
    };
    const mockPullRequests = [
      { id: 1, state: 'open' },
      { id: 2, state: 'closed' },
    ];

    render(<MetricsCards health={mockHealth} pullRequests={mockPullRequests} />);

    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('90.5%')).toBeInTheDocument();
    expect(screen.getByText('Grade A')).toBeInTheDocument();
    expect(screen.getByText('LOW RISK')).toBeInTheDocument();
    expect(screen.getByText('1 CRITICAL')).toBeInTheDocument();
    expect(screen.getByText('2.5 min')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument(); // 1 open PR
  });

  it('highlights critical vulnerabilities when present', () => {
    const mockHealth = {
      total_security_findings: 5,
      critical_vulnerabilities: 2,
    };
    render(<MetricsCards health={mockHealth} />);
    expect(screen.getByText('2 CRITICAL')).toBeInTheDocument();
  });
});

