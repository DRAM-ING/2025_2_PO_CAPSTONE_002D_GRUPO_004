/**
 * Tests para el hook useItems
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useItems } from '@/hooks/useItems';

describe('useItems', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it('debe retornar la función crearItem', () => {
    const { result } = renderHook(() => useItems());
    
    expect(result.current).toHaveProperty('crearItem');
    expect(typeof result.current.crearItem).toBe('function');
  });

  it('debe crear item exitosamente', async () => {
    const mockData = { id: '1', descripcion: 'Item Test' };
    
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify(mockData),
      json: async () => mockData,
    });

    const { result } = renderHook(() => useItems());
    
    const response = await result.current.crearItem({ descripcion: 'Test' });
    
    expect(response).toEqual(mockData);
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/work/items/create',
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

    const { result } = renderHook(() => useItems());
    
    await expect(result.current.crearItem({})).rejects.toThrow('Error de validación');
  });
});

