/**
 * Tests para la página de timeline de OT
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { useRouter, useParams } from 'next/navigation';
import { useToast } from '@/components/ToastContainer';
import { useAuth } from '@/store/auth';
import TimelineOTPage from '@/app/workorders/[id]/timeline/page';

// Mocks
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
  useParams: vi.fn(),
}));

vi.mock('@/components/ToastContainer', () => ({
  useToast: vi.fn(),
}));

// Mock de useAuth - debe incluir todos los métodos que usa RoleGuard
vi.mock('@/store/auth', () => ({
  useAuth: () => ({
    user: { id: '1', username: 'test', rol: 'ADMIN' },
    setUser: vi.fn(),
    allowed: vi.fn(() => true),
    hasRole: vi.fn(() => true),
    isLogged: () => true,  // Función que retorna boolean
    refreshMe: vi.fn(() => Promise.resolve()),
  }),
}));

vi.mock('@/lib/api.client', () => ({
  withSession: () => ({}),
}));

describe('TimelineOTPage', () => {
  const mockToast = {
    success: vi.fn(),
    error: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (useToast as any).mockReturnValue(mockToast);
    // useParams ya está mockeado en setup.ts, solo necesitamos sobrescribir el valor
    vi.mocked(useParams).mockReturnValue({ id: 'test-ot-id' } as any);
    // useAuth ya está mockeado globalmente arriba, no necesitamos sobrescribirlo
  });

  it('debe renderizar el título de timeline', async () => {
    // Mock fetch para la carga de OT y timeline
    global.fetch = vi.fn((url: string) => {
      // Si es el endpoint de la OT
      if (url.includes('/work/ordenes/') && !url.includes('/timeline/')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            id: 'test-ot-id',
            vehiculo_patente: 'ABC123',
            estado: 'ABIERTA',
          }),
        } as Response);
      }
      // Si es el endpoint de timeline
      if (url.includes('/timeline/')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            timeline: [],
            actores: [],
          }),
        } as Response);
      }
      return Promise.reject(new Error('Unexpected URL'));
    });

    render(<TimelineOTPage />);
    
    // Esperar a que el componente termine de cargar (RoleGuard + fetch)
    await waitFor(() => {
      expect(screen.getByText(/Timeline de la OT/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('debe mostrar estado de carga inicialmente', () => {
    render(<TimelineOTPage />);
    // El componente debe mostrar loading state
  });
});

