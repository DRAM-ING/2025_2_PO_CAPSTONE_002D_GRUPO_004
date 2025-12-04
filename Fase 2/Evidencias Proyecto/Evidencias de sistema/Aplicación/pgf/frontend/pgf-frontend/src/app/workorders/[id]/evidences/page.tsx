"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ENDPOINTS } from "@/lib/constants";
import { withSession } from "@/lib/api.client";
import Link from "next/link";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";
import { handleApiError, getRoleHomePage } from "@/lib/permissions";
import ConfirmDialog from "@/components/ConfirmDialog";
import EvidenceThumbnail from "@/components/EvidenceThumbnail";

/**
 * Página de evidencias de una Orden de Trabajo.
 * 
 * Características:
 * - Lista todas las evidencias de una OT
 * - Filtros por tipo de evidencia
 * - Filtros por fecha (desde/hasta)
 * - Búsqueda por descripción
 * - Ordenamiento por fecha
 * - Vista previa de imágenes
 * - Descarga de archivos
 */
export default function EvidencesPage() {
  const params = useParams();
  const router = useRouter();
  const otId = params.id as string;
  const toast = useToast();
  const { hasRole, user } = useAuth();

  // Roles autorizados para subir evidencias
  const canUpload = hasRole(["MECANICO", "SUPERVISOR", "ADMIN", "GUARDIA", "JEFE_TALLER"]);

  const [rows, setRows] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [evidenciaToDelete, setEvidenciaToDelete] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  
  // Filtros
  const [filtroTipo, setFiltroTipo] = useState<string>("");
  const [filtroFechaDesde, setFiltroFechaDesde] = useState<string>("");
  const [filtroFechaHasta, setFiltroFechaHasta] = useState<string>("");
  const [busqueda, setBusqueda] = useState<string>("");
  const [orden, setOrden] = useState<"subido_en" | "-subido_en">("-subido_en");

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
      load();
    } catch (error: any) {
      console.error("Error al eliminar evidencia:", error);
      toast.error(error?.message || "Error al eliminar la evidencia");
    } finally {
      setDeleting(false);
    }
  };

  const load = async () => {
    setLoading(true);
    try {
      // Construir URL con filtros
      let url = `${ENDPOINTS.EVIDENCES}?ot=${otId}`;
      
      if (filtroTipo) {
        url += `&tipo=${filtroTipo}`;
      }
      
      if (filtroFechaDesde) {
        url += `&subido_en__gte=${filtroFechaDesde}`;
      }
      
      if (filtroFechaHasta) {
        url += `&subido_en__lte=${filtroFechaHasta}`;
      }
      
      if (orden) {
        url += `&ordering=${orden}`;
      }

      const r = await fetch(url, withSession());
      if (!r.ok) {
        if (r.status === 403) {
          toast.error("Permisos insuficientes. No tiene acceso a ver evidencias.");
          setTimeout(() => {
            router.push(getRoleHomePage(user?.rol));
          }, 2000);
          return;
        }
        const errorData = await r.json().catch(() => ({ detail: "Error al cargar evidencias" }));
        handleApiError({ status: r.status, detail: errorData.detail }, router, toast, user?.rol);
        return;
      }
      
      const j = await r.json();
      let evidencias = j.results ?? j;
      
      // Filtrar por búsqueda en el frontend (descripción)
      if (busqueda) {
        evidencias = evidencias.filter((e: any) =>
          (e.descripcion || "").toLowerCase().includes(busqueda.toLowerCase()) ||
          (e.tipo || "").toLowerCase().includes(busqueda.toLowerCase())
        );
      }
      
      setRows(evidencias);
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al cargar evidencias");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [filtroTipo, filtroFechaDesde, filtroFechaHasta, orden]);

  // Búsqueda con debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      load();
    }, 300);
    return () => clearTimeout(timer);
  }, [busqueda]);

  const limpiarFiltros = () => {
    setFiltroTipo("");
    setFiltroFechaDesde("");
    setFiltroFechaHasta("");
    setBusqueda("");
    setOrden("-subido_en");
  };

  const formatFecha = (fechaStr: string) => {
    if (!fechaStr) return "";
    try {
      const fecha = new Date(fechaStr);
      return fecha.toLocaleDateString("es-CL", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return fechaStr;
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* HEADER */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Evidencias</h1>
        {canUpload && (
          <Link
            href={`/workorders/${otId}/evidences/upload`}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
            style={{ backgroundColor: '#003DA5' }}
          >
            + Subir Evidencia
          </Link>
        )}
      </div>

      {/* FILTROS Y BÚSQUEDA */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* Búsqueda */}
          <div className="lg:col-span-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Buscar
            </label>
            <input
              type="text"
              placeholder="Buscar por descripción o tipo..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              className="input w-full"
            />
          </div>

          {/* Filtro por tipo */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Tipo
            </label>
            <select
              value={filtroTipo}
              onChange={(e) => setFiltroTipo(e.target.value)}
              className="input w-full"
            >
              <option value="">Todos</option>
              <option value="FOTO">FOTO</option>
              <option value="PDF">PDF</option>
              <option value="HOJA_CALCULO">HOJA_CALCULO</option>
              <option value="DOCUMENTO">DOCUMENTO</option>
              <option value="COMPRIMIDO">COMPRIMIDO</option>
              <option value="OTRO">OTRO</option>
            </select>
          </div>

          {/* Orden */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Ordenar
            </label>
            <select
              value={orden}
              onChange={(e) => setOrden(e.target.value as any)}
              className="input w-full"
            >
              <option value="-subido_en">Más recientes</option>
              <option value="subido_en">Más antiguas</option>
            </select>
          </div>

          {/* Botón limpiar */}
          <div className="flex items-end">
            <button
              onClick={limpiarFiltros}
              className="w-full px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
            >
              Limpiar
            </button>
          </div>
        </div>

        {/* Filtros de fecha */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Desde
            </label>
            <input
              type="date"
              value={filtroFechaDesde}
              onChange={(e) => setFiltroFechaDesde(e.target.value)}
              className="input w-full"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Hasta
            </label>
            <input
              type="date"
              value={filtroFechaHasta}
              onChange={(e) => setFiltroFechaHasta(e.target.value)}
              className="input w-full"
            />
          </div>
        </div>
      </div>

      {/* CONTADOR Y RESULTADOS */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {rows.length} evidencia{rows.length !== 1 ? "s" : ""} encontrada{rows.length !== 1 ? "s" : ""}
        </p>
      </div>

      {/* GRID DE EVIDENCIAS */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando evidencias...</p>
          </div>
        </div>
      ) : rows.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg shadow">
          <p className="text-gray-500 dark:text-gray-400">No se encontraron evidencias</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {rows.map((e) => (
            <div
              key={e.id}
              className="bg-white dark:bg-gray-800 rounded-lg shadow cursor-pointer hover:shadow-lg transition p-4"
              onClick={() => setSelected(e)}
            >
              <EvidenceThumbnail
                evidenciaId={e.id}
                url={e.url}
                alt={e.descripcion || "Evidencia"}
                className="w-full h-32 object-cover rounded mb-2"
                tipo={e.tipo}
              />
              <p className="font-semibold text-sm text-gray-900 dark:text-white truncate">
                {e.descripcion || e.tipo}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {formatFecha(e.subido_en)}
              </p>
              <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                {e.tipo}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* MODAL DE PREVIEW */}
      {selected && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                {selected.descripcion || selected.tipo}
              </h2>
              <button
                onClick={() => setSelected(null)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
              <p><strong>Tipo:</strong> {selected.tipo}</p>
              <p><strong>Subido:</strong> {formatFecha(selected.subido_en)}</p>
              {selected.descripcion && (
                <p><strong>Descripción:</strong> {selected.descripcion}</p>
              )}
              {selected.subido_por_nombre && (
                <p><strong>Subido por:</strong> {selected.subido_por_nombre}</p>
              )}
            </div>

            {selected.tipo === "FOTO" ? (
              <div className="w-full">
                <EvidenceThumbnail
                  evidenciaId={selected.id}
                  tipo={selected.tipo}
                  descripcion={selected.descripcion || "Evidencia"}
                  className="w-full max-h-96 object-contain rounded"
                />
              </div>
            ) : (
              <div className="space-y-2">
                <button
                  onClick={async () => {
                    try {
                      const response = await fetch(`/api/proxy/work/evidencias/${selected.id}/download/`, {
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
                      
                      const contentType = response.headers.get("content-type") || "";
                      
                      if (contentType.startsWith("image/") || contentType.includes("pdf") || contentType.includes("application/octet-stream")) {
                        // El proxy devolvió el archivo directamente
                        const blob = await response.blob();
                        const blobUrl = URL.createObjectURL(blob);
                        window.open(blobUrl, '_blank', 'noopener,noreferrer');
                        setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
                      } else {
                        // El proxy devolvió JSON con URL
                        const text = await response.text();
                        if (!text || text.trim() === "") {
                          toast.error("Respuesta vacía del servidor");
                          return;
                        }
                        
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
                      console.error("Error al descargar evidencia:", error);
                      toast.error(error?.message || "Error al descargar evidencia");
                    }
                  }}
                  className="block w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium text-center"
                  style={{ backgroundColor: '#003DA5' }}
                >
                  📥 Abrir/Descargar archivo
                </button>
                <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                  El archivo se abrirá en una nueva pestaña
                </p>
                {canDeleteEvidence(selected) && (
                  <button
                    onClick={() => setEvidenciaToDelete(selected.id)}
                    className="block w-full mt-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-center rounded-lg transition-colors font-medium"
                  >
                    🗑️ Eliminar Evidencia
                  </button>
                )}
              </div>
            )}

            <button
              onClick={() => setSelected(null)}
              className="w-full px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
            >
              Cerrar
            </button>
          </div>
        </div>
      )}

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
    </div>
  );
}
