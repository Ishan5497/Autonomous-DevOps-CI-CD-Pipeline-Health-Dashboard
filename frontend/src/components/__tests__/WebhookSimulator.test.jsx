import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import WebhookSimulator from '../WebhookSimulator';
import { api } from '../../services/api';

vi.mock('../../services/api', () => ({
  api: {
    simulatePush: vi.fn(),
    simulatePullRequest: vi.fn(),
    simulateBuildStatus: vi.fn(),
  },
}));

describe('WebhookSimulator Component', () => {
  it('renders simulator buttons and response console', () => {
    render(<WebhookSimulator />);
    expect(screen.getByText('Safe Push')).toBeInTheDocument();
    expect(screen.getByText('Push (Secret Leak)')).toBeInTheDocument();
    expect(screen.getByText('Pull Request')).toBeInTheDocument();
    expect(screen.getByText('Passing Build')).toBeInTheDocument();
    expect(screen.getByText('Failing Build')).toBeInTheDocument();
    expect(screen.getByText(/FastAPI Response Telemetry/i)).toBeInTheDocument();
  });

  it('triggers safe push simulation and updates output console', async () => {
    const eventSentSpy = vi.fn();
    api.simulatePush.mockResolvedValueOnce({
      status: 'success',
      message: 'Simulated push processed',
    });

    render(<WebhookSimulator onEventSent={eventSentSpy} />);
    const pushBtn = screen.getByText('Safe Push');
    fireEvent.click(pushBtn);

    await waitFor(() => {
      expect(api.simulatePush).toHaveBeenCalledTimes(1);
      expect(eventSentSpy).toHaveBeenCalledTimes(1);
      expect(screen.getByText('200 OK (PUSH)')).toBeInTheDocument();
    });
  });
});

