/**
 * Tests para el hook useAprobaciones
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useAprobaciones } from '@/hooks/useAprobaciones';

describe('useAprobaciones', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it('debe retornar las funciones aprobar y rechazar', () => {
    const { result } = renderHook(() => useAprobaciones());
    
    expect(result.current).toHaveProperty('aprobar');
    expect(result.current).toHaveProperty('rechazar');
    expect(typeof result.current.aprobar).toBe('function');
    expect(typeof result.current.rechazar).toBe('function');
  });

  it('debe aprobar exitosamente', async () => {
    const mockData = { id: '1', estado: 'APROBADO' };
    
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify(mockData),
      json: async () => mockData,
    });

    const { result } = renderHook(() => useAprobaciones());
    
    const response = await result.current.aprobar('test-id');
    
    expect(response).toEqual(mockData);
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/work/aprobaciones/test-id/aprobar',
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
      })
    );
  });

  it('debe rechazar exitosamente', async () => {
    const mockData = { id: '1', estado: 'RECHAZADO' };
    
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify(mockData),
      json: async () => mockData,
    });

    const { result } = renderHook(() => useAprobaciones());
    
    const response = await result.current.rechazar('test-id');
    
    expect(response).toEqual(mockData);
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/work/aprobaciones/test-id/rechazar',
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
      })
    );
  });

  it('debe manejar errores HTTP en aprobar', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 400,
      text: async () => 'Error de validación',
    });

    const { result } = renderHook(() => useAprobaciones());
    
    await expect(result.current.aprobar('test-id')).rejects.toThrow('Error de validación');
  });

  it('debe manejar errores HTTP en rechazar', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 400,
      text: async () => 'Error de validación',
    });

    const { result } = renderHook(() => useAprobaciones());
    
    await expect(result.current.rechazar('test-id')).rejects.toThrow('Error de validación');
  });
});

