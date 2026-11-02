import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Header from '../Header';

describe('Header Component', () => {
  it('renders title, live indicator, and buttons', () => {
    render(
      <Header
        onRefresh={() => {}}
        onSeedData={() => {}}
        isRefreshing={false}
        isSeeding={false}
      />
    );
    expect(screen.getByText('DevOps Operations Center')).toBeInTheDocument();
    expect(screen.getByText('LIVE TELEMETRY')).toBeInTheDocument();
    expect(screen.getByText('Seed Demo Data')).toBeInTheDocument();
    expect(screen.getByText('Refresh')).toBeInTheDocument();
  });

  it('triggers onRefresh and onSeedData callbacks', () => {
    const refreshSpy = vi.fn();
    const seedSpy = vi.fn();

    render(
      <Header
        onRefresh={refreshSpy}
        onSeedData={seedSpy}
        isRefreshing={false}
        isSeeding={false}
      />
    );

    fireEvent.click(screen.getByText('Refresh'));
    expect(refreshSpy).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByText('Seed Demo Data'));
    expect(seedSpy).toHaveBeenCalledTimes(1);
  });

  it('displays loading labels when busy', () => {
    render(
      <Header
        onRefresh={() => {}}
        onSeedData={() => {}}
        isRefreshing={true}
        isSeeding={true}
      />
    );
    expect(screen.getByText('Seeding...')).toBeInTheDocument();
  });
});

