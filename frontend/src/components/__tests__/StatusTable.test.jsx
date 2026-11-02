import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import StatusTable from '../StatusTable';

describe('StatusTable Component', () => {
  const mockRuns = [
    {
      id: 1,
      pipeline_id: 'pipe-001',
      commit_sha: 'a1b2c3d4',
      commit_message: 'feat: add telemetry',
      branch: 'main',
      stage: 'deploy',
      status: 'success',
      duration_seconds: 42,
      author: 'alice',
      created_at: new Date().toISOString(),
    },
    {
      id: 2,
      pipeline_id: 'pipe-002',
      commit_sha: 'e5f6g7h8',
      commit_message: 'fix: broken tests',
      branch: 'fix/runner',
      stage: 'test',
      status: 'failed',
      duration_seconds: 15,
      failure_reason: 'Unit test timeout',
      author: 'bob',
      created_at: new Date().toISOString(),
    },
  ];

  it('renders runs and displays PASSED/FAILED badges', () => {
    render(<StatusTable runs={mockRuns} />);
    expect(screen.getByText('pipe-001')).toBeInTheDocument();
    expect(screen.getByText('pipe-002')).toBeInTheDocument();
    expect(screen.getByText('PASSED')).toBeInTheDocument();
    expect(screen.getAllByText('FAILED').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Unit test timeout/i)).toBeInTheDocument();
  });

  it('filters runs by status tabs', () => {
    render(<StatusTable runs={mockRuns} />);

    // Filter SUCCESS
    fireEvent.click(screen.getByRole('button', { name: 'SUCCESS' }));
    expect(screen.getByText('pipe-001')).toBeInTheDocument();
    expect(screen.queryByText('pipe-002')).not.toBeInTheDocument();

    // Filter FAILED
    fireEvent.click(screen.getByRole('button', { name: 'FAILED' }));
    expect(screen.queryByText('pipe-001')).not.toBeInTheDocument();
    expect(screen.getByText('pipe-002')).toBeInTheDocument();
  });

  it('searches by branch or commit query', () => {
    render(<StatusTable runs={mockRuns} />);
    const searchInput = screen.getByPlaceholderText(/Search branch, commit, or ID/i);

    fireEvent.change(searchInput, { target: { value: 'runner' } });
    expect(screen.queryByText('pipe-001')).not.toBeInTheDocument();
    expect(screen.getByText('pipe-002')).toBeInTheDocument();
  });

  it('renders empty placeholder when no runs match', () => {
    render(<StatusTable runs={[]} />);
    expect(screen.getByText(/No pipeline executions found/i)).toBeInTheDocument();
  });
});
