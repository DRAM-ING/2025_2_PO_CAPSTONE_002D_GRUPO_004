/**
 * Tests para la página de comentarios de OT
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { useRouter, useParams } from 'next/navigation';
import { useToast } from '@/components/ToastContainer';
import { useAuth } from '@/store/auth';
import ComentariosOTPage from '@/app/workorders/[id]/comentarios/page';

// Mocks
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
  useParams: vi.fn(),
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

describe('ComentariosOTPage', () => {
  const mockToast = {
    success: vi.fn(),
    error: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (useToast as any).mockReturnValue(mockToast);
    // useParams ya está mockeado en setup.ts, solo necesitamos sobrescribir el valor
    vi.mocked(useParams).mockReturnValue({ id: 'test-ot-id' } as any);
    (useAuth as any).mockReturnValue({
      user: { id: 'user-1', username: 'test_user', rol: 'MECANICO' },
      hasRole: () => true,
      isLogged: () => true,
      refreshMe: vi.fn(() => Promise.resolve()),
    });
    
    // Mock de fetch para cargar datos de la OT y comentarios
    global.fetch = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 'test-ot-id',
          vehiculo_patente: 'ABC123',
          estado: 'ABIERTA',
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          results: [],
        }),
      });
  });

  it('debe renderizar el título de comentarios', async () => {
    render(<ComentariosOTPage />);
    await waitFor(() => {
      expect(screen.getByText(/Comentarios de la OT/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('debe mostrar formulario para agregar comentario', async () => {
    render(<ComentariosOTPage />);
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Escribe tu comentario/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });
});

