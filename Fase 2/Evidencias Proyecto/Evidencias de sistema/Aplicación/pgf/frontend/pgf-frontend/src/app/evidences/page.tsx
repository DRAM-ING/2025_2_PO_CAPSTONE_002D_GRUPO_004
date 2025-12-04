"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";
import RoleGuard from "@/components/RoleGuard";
import Link from "next/link";
import ConfirmDialog from "@/components/ConfirmDialog";
import EvidenceThumbnail from "@/components/EvidenceThumbnail";

/**
 * Página general de evidencias.
 * 
 * Permite:
 * - Ver todas las evidencias del sistema
 * - Filtrar por tipo, OT, fecha
 * - Subir nuevas evidencias
 * - Ver detalles de evidencias
 * 
 * Permisos:
 * - ADMIN, SUPERVISOR, MECANICO, JEFE_TALLER pueden ver y subir
 * - Otros roles según configuración
 */
export default function EvidencesPage() {
  const router = useRouter();
  const toast = useToast();
  const { hasRole, user } = useAuth();

  const [evidencias, setEvidencias] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [evidenciaToDelete, setEvidenciaToDelete] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  
  // Filtros
  const [filtroTipo, setFiltroTipo] = useState<string>("");
  const [filtroOT, setFiltroOT] = useState<string>("");
  const [filtroFechaDesde, setFiltroFechaDesde] = useState<string>("");
  const [filtroFechaHasta, setFiltroFechaHasta] = useState<string>("");
  const [busqueda, setBusqueda] = useState<string>("");

  const canUpload = hasRole(["ADMIN", "SUPERVISOR", "MECANICO", "JEFE_TALLER", "GUARDIA"]);

  // Función para verificar si el usuario puede eliminar una evidencia
  const canDeleteEvidence = (evidencia: any): boolean => {
    if (!user) return false;
    
    const userRole = user.rol;
    
    // ADMIN y JEFE_TALLER pueden eliminar todas las evidencias
    if (userRole === "ADMIN" || userRole === "JEFE_TALLER") {
      return true;
    }
    
    // MECANICO y GUARDIA solo pueden eliminar las que ellos subieron
    if (userRole === "MECANICO" || userRole === "GUARDIA") {
      return evidencia.subido_por === user.id || evidencia.subido_por?.id === user.id;
    }
    
    return false;
  };

  const handleDelete = async (evidenciaId: string) => {
    setDeleting(true);
    try {
      const response = await fetch(`/api/proxy/work/evidencias/${evidenciaId}/`, {
        method: "DELETE",
        credentials: "include",
      });

      if (!response.ok) {
        const text = await response.text();
        let errorData;
        try {
          errorData = JSON.parse(text);
        } catch {
          errorData = { detail: text || "Error desconocido" };
        }
        toast.error(errorData.detail || "Error al eliminar la evidencia");
        return;
      }

      toast.success("Evidencia eliminada correctamente");
      setEvidenciaToDelete(null);
      // Recargar evidencias
      loadEvidencias();
    } catch (error: any) {
      console.error("Error al eliminar evidencia:", error);
      toast.error(error?.message || "Error al eliminar la evidencia");
    } finally {
      setDeleting(false);
    }
  };

  const loadEvidencias = async () => {
    setLoading(true);
    try {
      let url = "/api/proxy/work/evidencias/?";
      const params = new URLSearchParams();
      
      if (filtroTipo) params.append("tipo", filtroTipo);
      if (filtroOT) params.append("ot", filtroOT);
      if (filtroFechaDesde) params.append("subido_en__gte", filtroFechaDesde);
      if (filtroFechaHasta) params.append("subido_en__lte", filtroFechaHasta);
      
      url += params.toString();

      const r = await fetch(url, {
        credentials: "include",
      });

      if (!r.ok) {
        // Para errores, simplemente retornar array vacío sin lanzar excepciones
        console.warn(`Error al cargar evidencias: HTTP ${r.status}`);
        setEvidencias([]);
        setLoading(false);
        return;
      }

      const data = await r.json();
      let results = data.results || data || [];

      // Filtrar por búsqueda en descripción
      if (busqueda) {
        results = results.filter((e: any) =>
          e.descripcion?.toLowerCase().includes(busqueda.toLowerCase()) ||
          e.tipo?.toLowerCase().includes(busqueda.toLowerCase())
        );
      }

      setEvidencias(results);
    } catch (error) {
      console.error("Error al cargar evidencias:", error);
      toast.error("Error al cargar evidencias");
      setEvidencias([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvidencias();
  }, [filtroTipo, filtroOT, filtroFechaDesde, filtroFechaHasta]);

  const handleSearch = () => {
    loadEvidencias();
  };

  return (
    <RoleGuard allow={["ADMIN", "SUPERVISOR", "MECANICO", "JEFE_TALLER", "EJECUTIVO", "COORDINADOR_ZONA"]}>
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Evidencias</h1>
          {canUpload && (
            <Link
              href="/evidences/upload"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
            >
              + Subir Evidencia
            </Link>
          )}
        </div>

        {/* Filtros */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Filtros</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Tipo
              </label>
              <select
                value={filtroTipo}
                onChange={(e) => setFiltroTipo(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">Todos</option>
                <option value="FOTO">FOTO</option>
                <option value="PDF">PDF</option>
                <option value="HOJA_CALCULO">Hoja de Cálculo</option>
                <option value="DOCUMENTO">Documento</option>
                <option value="COMPRIMIDO">Comprimido</option>
                <option value="OTRO">Otro</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Fecha Desde
              </label>
              <input
                type="date"
                value={filtroFechaDesde}
                onChange={(e) => setFiltroFechaDesde(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Fecha Hasta
              </label>
              <input
                type="date"
                value={filtroFechaHasta}
                onChange={(e) => setFiltroFechaHasta(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Búsqueda
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={busqueda}
                  onChange={(e) => setBusqueda(e.target.value)}
                  placeholder="Buscar en descripción..."
                  className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  onKeyPress={(e) => e.key === "Enter" && handleSearch()}
                />
                <button
                  onClick={handleSearch}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  Buscar
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Lista de evidencias */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando evidencias...</p>
            </div>
          </div>
        ) : evidencias.length === 0 ? (
          <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg shadow">
            <p className="text-gray-500 dark:text-gray-400">No se encontraron evidencias</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {evidencias.map((e) => (
              <div
                key={e.id}
                className="bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-lg transition p-4"
              >
                <EvidenceThumbnail
                  evidenciaId={e.id}
                  url={e.url}
                  alt={e.descripcion || "Evidencia"}
                  className="w-full h-48 object-cover rounded mb-3"
                  tipo={e.tipo}
                />
                
                <div className="space-y-2">
                  <h3 className="font-semibold text-gray-900 dark:text-white truncate">
                    {e.descripcion || e.tipo || "Evidencia"}
                  </h3>
                  
                  <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
                    <span>{e.tipo}</span>
                    <span>{new Date(e.subido_en).toLocaleDateString()}</span>
                  </div>

                  {e.ot ? (
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      OT: <Link href={`/workorders/${e.ot}`} className="text-blue-600 dark:text-blue-400 hover:underline">
                        #{typeof e.ot === 'string' ? e.ot.substring(0, 8) : e.ot.id?.substring(0, 8) || 'N/A'}
                      </Link>
                    </div>
                  ) : (
                    <div className="text-sm text-gray-500 dark:text-gray-500 italic">
                      Evidencia general
                    </div>
                  )}

                  <div className="flex gap-2 mt-3">
                    <button
                      onClick={async () => {
                        try {
                          // El proxy ahora devuelve el archivo directamente o una URL
                          const response = await fetch(`/api/proxy/work/evidencias/${e.id}/download/`, {
                            credentials: "include",
                          });
                          
                          if (!response.ok) {
                            const text = await response.text();
                            let errorData;
                            try {
                              errorData = JSON.parse(text);
                            } catch {
                              errorData = { detail: text || `Error ${response.status}` };
                            }
                            
                            // Mensaje específico para 404
                            if (response.status === 404) {
                              toast.error("El archivo no está disponible. Puede haber sido eliminado o nunca se subió correctamente.");
                            } else {
                              toast.error(errorData.detail || `Error ${response.status}`);
                            }
                            return;
                          }
                          
                          // Verificar si es un archivo (imagen, PDF, etc.) o JSON con URL
                          const contentType = response.headers.get("content-type") || "";
                          
                          if (contentType.startsWith("image/") || contentType.includes("pdf") || contentType.includes("application/octet-stream")) {
                            // Es un archivo, descargarlo o abrirlo
                            const blob = await response.blob();
                            const blobUrl = URL.createObjectURL(blob);
                            window.open(blobUrl, '_blank', 'noopener,noreferrer');
                            // Limpiar el blob URL después de un tiempo
                            setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
                          } else {
                            // Es JSON con URL
                            const text = await response.text();
                            let data;
                            try {
                              data = JSON.parse(text);
                            } catch (e) {
                              console.error("Error al parsear respuesta:", text);
                              toast.error("Respuesta inválida del servidor");
                              return;
                            }
                            
                            if (data.download_url) {
                              window.open(data.download_url, '_blank', 'noopener,noreferrer');
                            } else {
                              toast.error("No se recibió URL de descarga");
                            }
                          }
                        } catch (error: any) {
                          console.error("Error al obtener evidencia:", error);
                          toast.error(error?.message || "Error al descargar evidencia");
                        }
                      }}
                      className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-center rounded-lg transition-colors"
                    >
                      Ver/Descargar
                    </button>
                    {canDeleteEvidence(e) && (
                      <button
                        onClick={() => setEvidenciaToDelete(e.id)}
                        className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
                        title="Eliminar evidencia"
                      >
                        🗑️
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Diálogo de confirmación para eliminar */}
      <ConfirmDialog
        isOpen={evidenciaToDelete !== null}
        title="Eliminar Evidencia"
        message="¿Estás seguro de que deseas eliminar esta evidencia? Esta acción no se puede deshacer."
        confirmText="Eliminar"
        cancelText="Cancelar"
        type="danger"
        onConfirm={() => {
          if (evidenciaToDelete) {
            handleDelete(evidenciaToDelete);
          }
        }}
        onCancel={() => setEvidenciaToDelete(null)}
      />
    </RoleGuard>
  );
}

