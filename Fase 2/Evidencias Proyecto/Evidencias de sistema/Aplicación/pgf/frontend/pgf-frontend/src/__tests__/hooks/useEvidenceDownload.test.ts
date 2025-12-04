/**
 * Tests para el hook useEvidenceDownload
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useEvidenceDownload } from '@/hooks/useEvidenceDownload';

describe('useEvidenceDownload', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it('debe retornar las funciones getDownloadUrl y openEvidence', () => {
    const { result } = renderHook(() => useEvidenceDownload());
    
    expect(result.current).toHaveProperty('getDownloadUrl');
    expect(result.current).toHaveProperty('openEvidence');
    expect(result.current).toHaveProperty('loading');
    expect(result.current).toHaveProperty('error');
    expect(typeof result.current.getDownloadUrl).toBe('function');
    expect(typeof result.current.openEvidence).toBe('function');
  });

  it('debe obtener URL de descarga exitosamente', async () => {
    const mockData = { download_url: 'https://test.com/file.jpg' };
    
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    });

    const { result } = renderHook(() => useEvidenceDownload());
    
    const url = await result.current.getDownloadUrl('evidence-id');
    
    expect(url).toBe('https://test.com/file.jpg');
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/proxy/work/evidencias/evidence-id/download/',
      expect.objectContaining({
        credentials: 'include',
      })
    );
  });

  it('debe manejar errores HTTP', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'Not found' }),
    });

    const { result } = renderHook(() => useEvidenceDownload());
    
    const url = await result.current.getDownloadUrl('invalid-id');
    
    expect(url).toBeNull();
    expect(result.current.error).toBeDefined();
  });

  it('debe abrir evidencia en nueva pestaña', async () => {
    const mockData = { download_url: 'https://test.com/file.jpg' };
    const mockOpen = vi.fn();
    window.open = mockOpen;
    
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    });

    const { result } = renderHook(() => useEvidenceDownload());
    
    const opened = await result.current.openEvidence('evidence-id');
    
    expect(opened).toBe(true);
    expect(mockOpen).toHaveBeenCalledWith('https://test.com/file.jpg', '_blank', 'noopener,noreferrer');
  });
});

