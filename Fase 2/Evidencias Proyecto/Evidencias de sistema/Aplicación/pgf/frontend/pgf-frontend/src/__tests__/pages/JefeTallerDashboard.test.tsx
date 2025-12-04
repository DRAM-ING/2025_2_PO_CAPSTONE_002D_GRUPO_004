/**
 * Tests para el dashboard de Jefe de Taller
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useRouter } from 'next/navigation';
import { useToast } from '@/components/ToastContainer';
import { useAuth } from '@/store/auth';
import JefeTallerDashboardPage from '@/app/jefe-taller/dashboard/page';

// Mocks
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
}));

vi.mock('@/components/ToastContainer', () => ({
  useToast: vi.fn(),
}));

vi.mock('@/store/auth', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/lib/api.client', () => ({
  withSession: () => ({}),
}));

describe('JefeTallerDashboardPage', () => {
  const mockToast = {
    success: vi.fn(),
    error: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (useToast as any).mockReturnValue(mockToast);
    (useAuth as any).mockReturnValue({
      user: { id: '1', username: 'test', rol: 'JEFE_TALLER' },
      hasRole: () => true,
      isLogged: () => true,
      refreshMe: vi.fn(() => Promise.resolve()),
    });
    
    // Mock de fetch para cargar datos del dashboard
    global.fetch = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          kpis: {
            ots_abiertas: 5,
            mecanicos_activos: 3,
            promedio_ejecucion: 2.5,
            ots_atrasadas: 1,
          },
          mecanicos_carga: [],
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          results: [],
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });
  });

  it('debe renderizar el título del dashboard', async () => {
    render(<JefeTallerDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText(/Dashboard del Taller/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('debe mostrar KPIs del taller', async () => {
    render(<JefeTallerDashboardPage />);
    // Esperar a que se carguen los datos y se muestren los KPIs
    await waitFor(() => {
      expect(screen.getByText(/OTs Abiertas/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });
});

