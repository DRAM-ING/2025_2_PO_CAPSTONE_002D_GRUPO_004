/**
 * Tests para el hook useChecklists
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useChecklists } from '@/hooks/useChecklists';

describe('useChecklists', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it('debe retornar la función crearChecklist', () => {
    const { result } = renderHook(() => useChecklists());
    
    expect(result.current).toHaveProperty('crearChecklist');
    expect(typeof result.current.crearChecklist).toBe('function');
  });

  it('debe crear checklist exitosamente', async () => {
    const mockData = { id: '1', nombre: 'Checklist Test' };
    
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify(mockData),
      json: async () => mockData,
    });

    const { result } = renderHook(() => useChecklists());
    
    const response = await result.current.crearChecklist({ nombre: 'Test' });
    
    expect(response).toEqual(mockData);
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/work/checklists',
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
      })
    );
  });

  it('debe manejar respuesta vacía', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      text: async () => '',
      json: async () => ({}),
    });

    const { result } = renderHook(() => useChecklists());
    
    const response = await result.current.crearChecklist({});
    
    expect(response).toEqual({});
  });

  it('debe manejar errores HTTP', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 400,
      text: async () => 'Error de validación',
    });

    const { result } = renderHook(() => useChecklists());
    
    await expect(result.current.crearChecklist({})).rejects.toThrow('Error de validación');
  });

  it('debe manejar errores de red', async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useChecklists());
    
    await expect(result.current.crearChecklist({})).rejects.toThrow('Network error');
  });

  it('debe manejar JSON inválido', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      text: async () => 'invalid json',
      json: async () => { throw new Error('Invalid JSON'); },
    });

    const { result } = renderHook(() => useChecklists());
    
    await expect(result.current.crearChecklist({})).rejects.toThrow('Invalid JSON response from server');
  });
});

