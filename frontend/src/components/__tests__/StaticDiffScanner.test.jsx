import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import StaticDiffScanner from '../StaticDiffScanner';
import { api } from '../../services/api';

vi.mock('../../services/api', () => ({
  api: {
    scanDiff: vi.fn(),
  },
}));

describe('StaticDiffScanner Component', () => {
  it('renders default diff editor and preloaded action buttons', () => {
    render(<StaticDiffScanner />);
    expect(screen.getByText(/Static Analysis Diff Scanner/i)).toBeInTheDocument();
    expect(screen.getByText('Load AWS Key Diff')).toBeInTheDocument();
    expect(screen.getByText('Load eval() & SQLi Diff')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Run Static Scan/i })).toBeInTheDocument();
  });

  it('switches sample diffs when buttons clicked', () => {
    render(<StaticDiffScanner />);
    const evalBtn = screen.getByText('Load eval() & SQLi Diff');
    fireEvent.click(evalBtn);

    const textarea = screen.getByPlaceholderText(/Paste raw Git diff/i);
    expect(textarea.value).toContain('Dangerous eval usage');
  });

  it('runs static scan and renders security findings', async () => {
    api.scanDiff.mockResolvedValueOnce({
      is_safe: false,
      findings_count: 1,
      critical_count: 1,
      high_count: 0,
      scanned_lines: 10,
      findings: [
        {
          rule_id: 'SEC-001',
          rule_name: 'AWS Access Key ID',
          severity: 'CRITICAL',
          description: 'Hardcoded key detected',
          snippet_redacted: 'AKIA****************LE',
          recommendation: 'Rotate key',
        },
      ],
    });

    render(<StaticDiffScanner />);
    const scanBtn = screen.getByRole('button', { name: /Run Static Scan/i });
    fireEvent.click(scanBtn);

    await waitFor(() => {
      expect(screen.getByText('Security Flaws Detected')).toBeInTheDocument();
      expect(screen.getByText(/Hardcoded key detected/i)).toBeInTheDocument();
      expect(screen.getByText('AKIA****************LE')).toBeInTheDocument();
    });
  });
});

