import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import LiveActivityLog from '../LiveActivityLog';

describe('LiveActivityLog Component', () => {
  it('renders waiting state when activity log is empty', () => {
    render(<LiveActivityLog activityLog={[]} isConnected={true} />);
    expect(screen.getByText(/Waiting for real-time events/i)).toBeInTheDocument();
    expect(screen.getByText('LIVE')).toBeInTheDocument();
  });

  it('renders reconnecting state when disconnected', () => {
    render(<LiveActivityLog activityLog={[]} isConnected={false} />);
    expect(screen.getByText('RECONNECTING')).toBeInTheDocument();
  });

  it('renders entries and applies category filters', () => {
    const mockLogs = [
      {
        id: '1',
        type: 'PIPELINE_UPDATE',
        severity: 'success',
        title: 'Pipeline pipe-100',
        message: 'Build passed on main',
        timestamp: new Date().toISOString(),
      },
      {
        id: '2',
        type: 'BUILD_FAILURE',
        severity: 'error',
        title: 'Build Failed: pipe-200',
        message: 'Timeout in test stage',
        timestamp: new Date().toISOString(),
      },
      {
        id: '3',
        type: 'SECURITY_ALERT',
        severity: 'critical',
        title: 'Security Alert — 1 finding',
        message: 'Leaked AWS key detected',
        timestamp: new Date().toISOString(),
      },
    ];

    render(<LiveActivityLog activityLog={mockLogs} isConnected={true} />);

    // Initially ALL shows 3 events
    expect(screen.getByText('Pipeline pipe-100')).toBeInTheDocument();
    expect(screen.getByText('Build Failed: pipe-200')).toBeInTheDocument();
    expect(screen.getByText('Security Alert — 1 finding')).toBeInTheDocument();

    // Filter by FAILURES
    fireEvent.click(screen.getByRole('button', { name: 'FAILURES' }));
    expect(screen.queryByText('Pipeline pipe-100')).not.toBeInTheDocument();
    expect(screen.getByText('Build Failed: pipe-200')).toBeInTheDocument();
    expect(screen.queryByText('Security Alert — 1 finding')).not.toBeInTheDocument();

    // Filter by SECURITY
    fireEvent.click(screen.getByRole('button', { name: 'SECURITY' }));
    expect(screen.queryByText('Build Failed: pipe-200')).not.toBeInTheDocument();
    expect(screen.getByText('Security Alert — 1 finding')).toBeInTheDocument();
  });

  it('calls onClearLog when clear button clicked', () => {
    const clearSpy = vi.fn();
    const mockLogs = [
      {
        id: '1',
        type: 'PIPELINE_UPDATE',
        severity: 'info',
        title: 'Test',
        message: 'Test message',
        timestamp: new Date().toISOString(),
      },
    ];

    render(<LiveActivityLog activityLog={mockLogs} isConnected={true} onClearLog={clearSpy} />);
    const clearBtn = screen.getByTitle('Clear log');
    fireEvent.click(clearBtn);
    expect(clearSpy).toHaveBeenCalledTimes(1);
  });
});

