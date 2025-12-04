/**
 * Tests para el componente EvidenceUploader
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { EvidenceUploader } from '@/components/EvidenceUploader';
import * as http from '@/lib/http';

// Mock de http
vi.mock('@/lib/http', () => ({
  apiPost: vi.fn(),
}));

describe('EvidenceUploader', () => {
  const mockApiPost = vi.mocked(http.apiPost);

  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it('debe renderizar el input de archivo', () => {
    const { container } = render(<EvidenceUploader otId="test-ot-id" />);
    
    const input = container.querySelector('input[type="file"]');
    expect(input).toBeInTheDocument();
  });

  it('debe mostrar mensaje de carga mientras sube', async () => {
    mockApiPost.mockResolvedValue({
      upload: {
        url: 'https://test.com/upload',
        fields: { key: 'value' },
      },
      file_url: 'https://test.com/file.jpg',
    });

    (global.fetch as any).mockResolvedValue({
      ok: true,
    });

    render(<EvidenceUploader otId="test-ot-id" />);
    
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
    
    fireEvent.change(input, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(screen.getByText(/subiendo/i)).toBeInTheDocument();
    });
  });

  it('debe mostrar mensaje de éxito después de subir', async () => {
    mockApiPost.mockResolvedValue({
      upload: {
        url: 'https://test.com/upload',
        fields: { key: 'value' },
      },
      file_url: 'https://test.com/file.jpg',
    });

    (global.fetch as any).mockResolvedValue({
      ok: true,
    });

    render(<EvidenceUploader otId="test-ot-id" />);
    
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
    
    fireEvent.change(input, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(screen.getByText(/evidencia subida/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('debe mostrar mensaje de error si falla la subida', async () => {
    mockApiPost.mockRejectedValue(new Error('Error de red'));

    render(<EvidenceUploader otId="test-ot-id" />);
    
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
    
    fireEvent.change(input, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('debe deshabilitar el input mientras sube', async () => {
    let resolveUpload: any;
    const uploadPromise = new Promise((resolve) => {
      resolveUpload = resolve;
    });

    mockApiPost.mockReturnValue(uploadPromise as any);

    render(<EvidenceUploader otId="test-ot-id" />);
    
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
    
    fireEvent.change(input, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(input).toBeDisabled();
    });

    resolveUpload({
      upload: { url: 'https://test.com/upload', fields: {} },
      file_url: 'https://test.com/file.jpg',
    });
  });
});

