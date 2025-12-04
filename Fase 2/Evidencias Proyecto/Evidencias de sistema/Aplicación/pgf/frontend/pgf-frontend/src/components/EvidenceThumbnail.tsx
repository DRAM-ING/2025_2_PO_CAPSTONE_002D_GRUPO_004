"use client";

import { useEffect, useState, useRef } from "react";

interface EvidenceThumbnailProps {
  evidenciaId: string;
  url?: string;
  alt?: string;
  className?: string;
  tipo?: string;
}

// Cache global para errores 404 (evitar múltiples intentos)
const notFoundCache = new Set<string>();

/**
 * Componente reutilizable para mostrar miniaturas de evidencias.
 * 
 * Maneja:
 * - Carga de imágenes desde URLs presignadas
 * - Estados de carga y error
 * - Limpieza de blob URLs
 * - Fallback para tipos de archivo no-imagen
 * - Cache de errores 404 para evitar reintentos
 */
export default function EvidenceThumbnail({ 
  evidenciaId, 
  url, 
  alt = "Evidencia", 
  className = "",
  tipo = "FOTO"
}: EvidenceThumbnailProps) {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const hasAttemptedRef = useRef(false);

  useEffect(() => {
    // Solo cargar si es una imagen
    if (tipo !== "FOTO") {
      setLoading(false);
      return;
    }

    // Si ya sabemos que este archivo no existe, no intentar descargarlo
    if (notFoundCache.has(evidenciaId)) {
      setError("Archivo no disponible");
      setLoading(false);
      return;
    }

    // Evitar múltiples intentos simultáneos
    if (hasAttemptedRef.current) {
      return;
    }
    hasAttemptedRef.current = true;

    // Usar directamente la URL del proxy que devuelve el archivo
    const proxyUrl = `/api/proxy/work/evidencias/${evidenciaId}/download/`;
    
    fetch(proxyUrl, {
      credentials: "include",
    })
      .then(async (r) => {
        if (!r.ok) {
          const text = await r.text();
          let errorData;
          try {
            errorData = JSON.parse(text);
          } catch {
            errorData = { detail: text || `Error ${r.status}` };
          }
          
          if (r.status === 404) {
            // Cachear el error 404 para evitar reintentos
            notFoundCache.add(evidenciaId);
            setError("Archivo no disponible");
            setLoading(false);
            return;
          }
          
          setError("Error al cargar");
          setLoading(false);
          return;
        }
        
        const contentType = r.headers.get("content-type") || "";
        
        if (contentType.startsWith("image/")) {
          const blob = await r.blob();
          const blobUrl = URL.createObjectURL(blob);
          setImageUrl(blobUrl);
          setLoading(false);
        } else {
          // Si no es una imagen, intentar obtener URL directa
          const text = await r.text();
          try {
            const data = JSON.parse(text);
            if (data.download_url) {
              setImageUrl(data.download_url);
              setLoading(false);
            } else {
              setError("URL no disponible");
              setLoading(false);
            }
          } catch (e) {
            // Si falla, usar la URL del proxy directamente
            setImageUrl(proxyUrl);
            setLoading(false);
          }
        }
      })
      .catch((err) => {
        // Solo loguear errores que no sean 404 (ya están cacheados)
        if (!notFoundCache.has(evidenciaId)) {
          console.error("Error al obtener imagen:", err);
        }
        setError("Error de conexión");
        setLoading(false);
      });
  }, [evidenciaId, tipo]);

  // Limpiar blob URL al desmontar
  useEffect(() => {
    return () => {
      if (imageUrl && imageUrl.startsWith("blob:")) {
        URL.revokeObjectURL(imageUrl);
      }
    };
  }, [imageUrl]);

  // Si no es una imagen, mostrar icono según tipo
  if (tipo !== "FOTO") {
    return (
      <div className={`${className} bg-gray-100 dark:bg-gray-700 flex items-center justify-center`}>
        <span className="text-4xl">
          {tipo === "PDF" && "📄"}
          {tipo === "HOJA_CALCULO" && "📊"}
          {tipo === "DOCUMENTO" && "📝"}
          {tipo === "COMPRIMIDO" && "📦"}
          {!["PDF", "HOJA_CALCULO", "DOCUMENTO", "COMPRIMIDO"].includes(tipo) && "📎"}
        </span>
      </div>
    );
  }

  // Estado de carga
  if (loading) {
    return (
      <div className={`${className} bg-gray-100 dark:bg-gray-700 flex items-center justify-center`}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
      </div>
    );
  }

  // Estado de error
  if (error || !imageUrl) {
    return (
      <div className={`${className} bg-gray-100 dark:bg-gray-700 flex flex-col items-center justify-center p-4`}>
        <span className="text-gray-400 text-xs text-center mb-1">⚠️ {error || "No disponible"}</span>
        <span className="text-gray-500 text-xs text-center">El archivo puede haber sido eliminado</span>
      </div>
    );
  }

  // Imagen cargada correctamente
  return (
    <img 
      src={imageUrl} 
      className={className} 
      alt={alt}
      onError={() => {
        setError("Error al cargar imagen");
        setImageUrl(null);
      }}
      loading="lazy"
    />
  );
}

