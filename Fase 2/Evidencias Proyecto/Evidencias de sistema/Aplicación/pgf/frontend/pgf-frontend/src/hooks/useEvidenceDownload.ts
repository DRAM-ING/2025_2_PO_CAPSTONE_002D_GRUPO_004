import { useState } from 'react';

/**
 * Hook para obtener URLs presignadas de descarga de evidencias
 */
export function useEvidenceDownload() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Obtiene una URL presignada para descargar/ver una evidencia
   */
  const getDownloadUrl = async (evidenciaId: string): Promise<string | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/proxy/work/evidencias/${evidenciaId}/download/`, {
        credentials: "include",
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `Error ${response.status}` }));
        throw new Error(errorData.detail || `Error ${response.status}`);
      }
      
      const data = await response.json();
      return data.download_url;
    } catch (err: any) {
      setError(err.message || "Error al obtener URL de descarga");
      console.error("Error al obtener URL de descarga:", err);
      return null;
    } finally {
      setLoading(false);
    }
  };

  /**
   * Abre una evidencia en una nueva pestaña usando URL presignada
   */
  const openEvidence = async (evidenciaId: string) => {
    const url = await getDownloadUrl(evidenciaId);
    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer');
    }
    return url !== null;
  };

  return {
    getDownloadUrl,
    openEvidence,
    loading,
    error,
  };
}

