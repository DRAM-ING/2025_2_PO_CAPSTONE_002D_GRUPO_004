/**
 * Tests para el hook usePausas
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { usePausas } from '@/hooks/usePausas';

describe('usePausas', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it('debe retornar la función crearPausa', () => {
    const { result } = renderHook(() => usePausas());
    
    expect(result.current).toHaveProperty('crearPausa');
    expect(typeof result.current.crearPausa).toBe('function');
  });

  it('debe crear pausa exitosamente', async () => {
    const mockData = { id: '1', motivo: 'Pausa Test' };
    
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify(mockData),
      json: async () => mockData,
    });

    const { result } = renderHook(() => usePausas());
    
    const response = await result.current.crearPausa({ motivo: 'Test' });
    
    expect(response).toEqual(mockData);
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/work/pausas',
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

    const { result } = renderHook(() => usePausas());
    
    await expect(result.current.crearPausa({})).rejects.toThrow('Error de validación');
  });
});

