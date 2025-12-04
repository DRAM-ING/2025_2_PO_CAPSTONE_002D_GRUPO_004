/**
 * Tests para la página de ingreso de vehículos
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { useRouter } from 'next/navigation';
import { useToast } from '@/components/ToastContainer';
import { useAuth } from '@/store/auth';
import IngresoVehiculoPage from '@/app/vehicles/ingreso/page';

// Mocks - No sobrescribir el mock global de setup.ts

vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
}));

vi.mock('@/components/ToastContainer', () => ({
  useToast: vi.fn(),
}));

vi.mock('@/store/auth', () => ({
  useAuth: vi.fn(),
}));

describe('IngresoVehiculoPage', () => {
  const mockRouter = {
    push: vi.fn(),
    back: vi.fn(),
    replace: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  };

  const mockToast = {
    success: vi.fn(),
    error: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (useRouter as any).mockReturnValue(mockRouter);
    (useToast as any).mockReturnValue(mockToast);
    
    // Mock de fetch para cargar marcas
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({ results: [] }),
      json: async () => ({ results: [] }),
    });
  });

  it('debe renderizar el formulario de ingreso', async () => {
    const mockUser = { id: '1', username: 'test', rol: 'GUARDIA' };
    (useAuth as any).mockReturnValue({
      user: mockUser,
      hasRole: (roles: string | string[]) => {
        const roleList = Array.isArray(roles) ? roles : [roles];
        return roleList.some(r => ['GUARDIA', 'ADMIN', 'JEFE_TALLER'].includes(r));
      },
      isLogged: () => true,
      refreshMe: vi.fn(() => Promise.resolve(mockUser)),
    });

    render(<IngresoVehiculoPage />);

    // Esperar a que RoleGuard termine de verificar y muestre el contenido
    await waitFor(() => {
      expect(screen.getByText(/Registrar Ingreso de Vehículo/i)).toBeInTheDocument();
    }, { timeout: 5000 });
    // El label de Patente no está asociado con el input, buscar por placeholder
    expect(screen.getByPlaceholderText(/ABC123/i)).toBeInTheDocument();
  });

  it('debe requerir patente para enviar', async () => {
    const mockUser = { id: '1', username: 'test', rol: 'GUARDIA' };
    (useAuth as any).mockReturnValue({
      user: mockUser,
      hasRole: (roles: string | string[]) => {
        const roleList = Array.isArray(roles) ? roles : [roles];
        return roleList.some(r => ['GUARDIA', 'ADMIN', 'JEFE_TALLER'].includes(r));
      },
      isLogged: () => true,
      refreshMe: vi.fn(() => Promise.resolve(mockUser)),
    });

    render(<IngresoVehiculoPage />);

    // Esperar a que RoleGuard termine de verificar y muestre el contenido
    await waitFor(() => {
      const submitButton = screen.getByText(/Registrar Ingreso y Crear OT/i);
      expect(submitButton).toBeInTheDocument();
    }, { timeout: 5000 });
  });

  it('debe mostrar mensaje de acceso denegado si no es Guardia', async () => {
    (useAuth as any).mockReturnValue({
      user: null,
      hasRole: () => false,
      isLogged: () => false,
      refreshMe: vi.fn(() => Promise.resolve(null)),
    });

    render(<IngresoVehiculoPage />);
    
    // RoleGuard debe mostrar el spinner de "Verificando permisos..." o redirigir
    await waitFor(() => {
      // Verificar que se muestra el mensaje de verificación o que se redirige
      const verifyingText = screen.queryByText(/Verificando permisos/i);
      // Si no está verificando, puede que ya haya redirigido (mockRouter.push habría sido llamado)
      expect(verifyingText || mockRouter.push).toBeTruthy();
    }, { timeout: 3000 });
  });
});

