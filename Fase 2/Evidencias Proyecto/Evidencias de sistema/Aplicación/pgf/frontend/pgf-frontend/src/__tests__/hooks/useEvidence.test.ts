/**
 * Tests para el hook useEvidence
 * 
 * Nota: Este hook usa SWR que es difícil de mockear completamente.
 * Nos enfocamos en testear la función presigned que es independiente de SWR.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useEvidence } from '@/hooks/useEvidence';

// Mock simplificado de SWR
const mockMutate = vi.fn();
vi.mock('swr', () => ({
  default: vi.fn(() => ({
    data: null,
    error: null,
    isLoading: false,
    mutate: mockMutate,
  })),
}));

describe('useEvidence', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it('debe retornar funciones y estado inicial', () => {
    const { result } = renderHook(() => useEvidence());
    
    expect(result.current).toHaveProperty('evidencias');
    expect(result.current).toHaveProperty('loading');
    expect(result.current).toHaveProperty('error');
    expect(result.current).toHaveProperty('refresh');
    expect(result.current).toHaveProperty('presigned');
    expect(Array.isArray(result.current.evidencias)).toBe(true);
    expect(typeof result.current.presigned).toBe('function');
  });

  it('debe obtener URL presignada exitosamente', async () => {
    const mockData = { upload: { url: 'https://test.com' }, file_url: 'https://test.com/file.jpg' };
    
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify(mockData),
      json: async () => mockData,
    });

    const { result } = renderHook(() => useEvidence());
    
    const response = await result.current.presigned('ot-id', 'test.jpg', 'image/jpeg');
    
    expect(response).toEqual(mockData);
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/work/evidencias/presigned',
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ot: 'ot-id', filename: 'test.jpg', content_type: 'image/jpeg' }),
      })
    );
  });

  it('debe manejar errores HTTP en presigned', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 400,
    });

    const { result } = renderHook(() => useEvidence());
    
    await expect(result.current.presigned('ot-id', 'test.jpg')).rejects.toThrow('HTTP 400');
  });

  it('debe manejar respuesta vacía en presigned', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      text: async () => '',
    });

    const { result } = renderHook(() => useEvidence());
    
    await expect(result.current.presigned('ot-id', 'test.jpg')).rejects.toThrow('Empty response');
  });

  it('debe manejar JSON inválido en presigned', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      text: async () => 'invalid json',
    });

    const { result } = renderHook(() => useEvidence());
    
    await expect(result.current.presigned('ot-id', 'test.jpg')).rejects.toThrow('Invalid JSON response');
  });
});

