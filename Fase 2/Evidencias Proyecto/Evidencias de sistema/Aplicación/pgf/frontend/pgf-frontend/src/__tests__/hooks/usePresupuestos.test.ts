/**
 * Tests para el hook usePresupuestos
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { usePresupuestos } from '@/hooks/usePresupuestos';

describe('usePresupuestos', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it('debe retornar la función crearPresupuesto', () => {
    const { result } = renderHook(() => usePresupuestos());
    
    expect(result.current).toHaveProperty('crearPresupuesto');
    expect(typeof result.current.crearPresupuesto).toBe('function');
  });

  it('debe crear presupuesto exitosamente', async () => {
    const mockData = { id: '1', total: 1000 };
    
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify(mockData),
      json: async () => mockData,
    });

    const { result } = renderHook(() => usePresupuestos());
    
    const response = await result.current.crearPresupuesto({ total: 1000 });
    
    expect(response).toEqual(mockData);
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/work/presupuestos/create',
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
      })
    );
  });

  it('debe manejar errores HTTP', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 400,
      text: async () => 'Error de validación',
    });

    const { result } = renderHook(() => usePresupuestos());
    
    await expect(result.current.crearPresupuesto({})).rejects.toThrow('Error de validación');
  });
});

