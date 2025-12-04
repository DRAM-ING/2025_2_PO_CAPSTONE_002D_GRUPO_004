"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";
import RoleGuard from "@/components/RoleGuard";
import Link from "next/link";
import { ENDPOINTS } from "@/lib/constants";
import { withSession } from "@/lib/api.client";
import { useRealtimeUpdate } from "@/hooks/useRealtimeUpdate";

/**
 * Vista de Asignación de Mecánicos para Jefe de Taller.
 * 
 * Muestra:
 * - Lista de mecánicos disponibles
 * - Indicador de carga de trabajo de cada mecánico
 * - OTs pendientes de asignación
 * - Botón para asignar/reasignar mecánicos
 * 
 * Permisos:
 * - Solo JEFE_TALLER puede acceder
 */
export default function JefeTallerAsignacionPage() {
  const router = useRouter();
  const toast = useToast();
  const { hasRole } = useAuth();

  const [mecanicos, setMecanicos] = useState<any[]>([]);
  const [otsPendientes, setOtsPendientes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0); // Clave para forzar actualización de MecanicoCard
  const [otSeleccionadaParaAsignar, setOtSeleccionadaParaAsignar] = useState<string | null>(null);
  const [mecanicoSeleccionadoParaAsignar, setMecanicoSeleccionadoParaAsignar] = useState<string>("");

  useEffect(() => {
    cargarDatos();
  }, []);
  
  // Escuchar actualizaciones en tiempo real de asignaciones y OTs
  useRealtimeUpdate({
    entityType: "assignment",
    onUpdate: (update) => {
      // Recargar datos cuando hay actualizaciones de asignaciones
      cargarDatos();
    },
  });
  
  useRealtimeUpdate({
    entityType: "workorder",
    onUpdate: (update) => {
      // Recargar datos cuando hay actualizaciones de OTs
      cargarDatos();
    },
  });

  const cargarDatos = async () => {
    setLoading(true);
    try {
      // Cargar mecánicos
      const mecanicosResponse = await fetch(`${ENDPOINTS.USERS}?rol=MECANICO`, {
        method: "GET",
        ...withSession(),
      });

      if (mecanicosResponse.ok) {
        const mecanicosData = await mecanicosResponse.json();
        const mecanicos = mecanicosData.results || mecanicosData || [];
        console.log("Mecánicos cargados:", mecanicos.length, mecanicos);
        setMecanicos(mecanicos);
      } else {
        console.error("Error al cargar mecánicos:", mecanicosResponse.status, mecanicosResponse.statusText);
        const errorText = await mecanicosResponse.text().catch(() => "Error desconocido");
        console.error("Error detallado:", errorText);
        toast.error(`Error al cargar mecánicos: ${mecanicosResponse.status}`);
      }

      // Cargar OTs pendientes de asignación
      const otsResponse = await fetch(`${ENDPOINTS.WORK_ORDERS}?estado=ABIERTA&mecanico__isnull=true`, {
        method: "GET",
        ...withSession(),
      });

      if (otsResponse.ok) {
        const otsData = await otsResponse.json();
        setOtsPendientes(otsData.results || otsData || []);
      }
    } catch (error) {
      console.error("Error al cargar datos:", error);
      toast.error("Error al cargar información");
    } finally {
      setLoading(false);
    }
  };

  const cargarCargaTrabajo = async (mecanicoId: string) => {
    try {
      // Cargar todas las OTs asignadas al mecánico (no solo las activas)
      const response = await fetch(`${ENDPOINTS.WORK_ORDERS}?mecanico=${mecanicoId}`, {
        method: "GET",
        ...withSession(),
      });

      if (response.ok) {
        const data = await response.json();
        const ots = data.results || data || [];
        // Separar por estado
        const activas = ots.filter((ot: any) => 
          ["EN_EJECUCION", "EN_PAUSA", "EN_DIAGNOSTICO", "ABIERTA"].includes(ot.estado)
        );
        const todas = ots.length;
        return { activas: activas.length, total: todas, ots: activas };
      }
      return { activas: 0, total: 0, ots: [] };
    } catch {
      return { activas: 0, total: 0, ots: [] };
    }
  };

  const handleAsignar = async (otId: string, mecanicoId: string) => {
    try {
      console.log(`[handleAsignar] Asignando mecánico ${mecanicoId} a OT ${otId}`);
      
      // Usar siempre el endpoint de aprobar-asignacion (el backend permite asignar desde cualquier estado excepto CERRADA)
      const response = await fetch(`/api/proxy/work/ordenes/${otId}/aprobar-asignacion/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          mecanico_id: mecanicoId,
        }),
      });

      const text = await response.text();
      let data: any = {};
      
      // Intentar parsear JSON solo si hay contenido
      if (text && text.trim() !== "") {
        try {
          data = JSON.parse(text);
        } catch (e) {
          // Si no es JSON válido, usar el texto como mensaje de error
          console.error("[handleAsignar] Error al parsear respuesta:", text);
          data = { detail: text || "Error desconocido" };
        }
      } else {
        // Si la respuesta está vacía, crear un mensaje basado en el status
        data = { 
          detail: `Error ${response.status}: ${response.statusText || "Error al asignar mecánico"}` 
        };
      }

      if (!response.ok) {
        const errorMessage = data.detail || data.message || data.error || `Error ${response.status}: ${response.statusText || "Error al asignar mecánico"}`;
        toast.error(errorMessage);
        console.error("[handleAsignar] Error al asignar:", {
          status: response.status,
          statusText: response.statusText,
          data: data,
          text: text,
          otId,
          mecanicoId
        });
        return;
      }

      console.log("[handleAsignar] Mecánico asignado correctamente:", data);
      toast.success("Mecánico asignado correctamente");
      
      // Invalidar cache de workorders
      const { invalidateCache } = await import("@/lib/dataRefresh");
      invalidateCache("WORKORDERS");
      
      // Recargar datos
      await cargarDatos();
      // Esperar un poco más para asegurar que la base de datos se actualice
      await new Promise(resolve => setTimeout(resolve, 1500));
      // Forzar actualización de la carga de trabajo de todos los mecánicos
      setRefreshKey(prev => prev + 1);
      // Recargar datos nuevamente después de actualizar refreshKey
      await new Promise(resolve => setTimeout(resolve, 500));
      await cargarDatos();
    } catch (error) {
      console.error("[handleAsignar] Error al asignar:", error);
      toast.error(`Error al asignar mecánico: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  if (loading) {
    return (
      <RoleGuard allow={["JEFE_TALLER", "ADMIN"]}>
        <div className="p-6 flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando información...</p>
          </div>
        </div>
      </RoleGuard>
    );
  }

  return (
    <RoleGuard allow={["JEFE_TALLER", "ADMIN"]}>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Asignación de Mecánicos
          </h1>
          <Link
            href="/jefe-taller/dashboard"
            className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
          >
            ← Volver
          </Link>
        </div>

        {/* OTs Pendientes de Asignación */}
        {otsPendientes.length > 0 && (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              OTs Pendientes de Asignación ({otsPendientes.length})
            </h2>
            <div className="space-y-2">
              {otsPendientes.map((ot) => (
                <div
                  key={ot.id}
                  className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600"
                >
                  <div>
                    <span className="font-medium text-gray-900 dark:text-white">
                      OT #{ot.id.slice(0, 8)} - {ot.vehiculo_patente || ot.vehiculo?.patente}
                    </span>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {ot.motivo?.substring(0, 100)}...
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setOtSeleccionadaParaAsignar(ot.id);
                      setMecanicoSeleccionadoParaAsignar("");
                    }}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
                  >
                    Asignar Mecánico
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Lista de Mecánicos */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Mecánicos Disponibles
            </h2>
          </div>
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {loading ? (
              <div className="p-6 text-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
                <p className="mt-4 text-gray-500 dark:text-gray-400">Cargando mecánicos...</p>
              </div>
            ) : mecanicos.length > 0 ? (
              mecanicos.map((mecanico) => (
                <MecanicoCard
                  key={mecanico.id}
                  mecanico={mecanico}
                  otsPendientes={otsPendientes}
                  onAsignar={handleAsignar}
                  refreshKey={refreshKey}
                />
              ))
            ) : (
              <div className="p-6 text-center text-gray-500 dark:text-gray-400">
                <p className="text-lg font-medium mb-2">No hay mecánicos registrados.</p>
                <p className="text-sm">Asegúrate de que existan usuarios con rol MECANICO en el sistema.</p>
                <p className="text-xs mt-2 text-gray-400 dark:text-gray-500">
                  Total cargados: {mecanicos.length}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Modal para asignar mecánico desde OTs pendientes */}
        {otSeleccionadaParaAsignar && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
              <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
                Asignar Mecánico
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Selecciona un mecánico para la OT #{otSeleccionadaParaAsignar.slice(0, 8)}
              </p>
              <select
                value={mecanicoSeleccionadoParaAsignar}
                onChange={(e) => setMecanicoSeleccionadoParaAsignar(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white mb-4"
              >
                <option value="">Seleccionar mecánico...</option>
                {mecanicos.map((mecanico) => (
                  <option key={mecanico.id} value={mecanico.id}>
                    {mecanico.get_full_name || `${mecanico.first_name || ""} ${mecanico.last_name || ""}`.trim() || mecanico.username}
                  </option>
                ))}
              </select>
              <div className="flex gap-3">
                <button
                  onClick={async () => {
                    if (mecanicoSeleccionadoParaAsignar && otSeleccionadaParaAsignar) {
                      await handleAsignar(otSeleccionadaParaAsignar, mecanicoSeleccionadoParaAsignar);
                      setOtSeleccionadaParaAsignar(null);
                      setMecanicoSeleccionadoParaAsignar("");
                    }
                  }}
                  disabled={!mecanicoSeleccionadoParaAsignar}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Asignar
                </button>
                <button
                  onClick={() => {
                    setOtSeleccionadaParaAsignar(null);
                    setMecanicoSeleccionadoParaAsignar("");
                  }}
                  className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
                >
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </RoleGuard>
  );
}

function MecanicoCard({
  mecanico,
  otsPendientes,
  onAsignar,
  refreshKey,
}: {
  mecanico: any;
  otsPendientes: any[];
  onAsignar: (otId: string, mecanicoId: string) => void;
  refreshKey?: number;
}) {
  const [cargaTrabajo, setCargaTrabajo] = useState({ activas: 0, total: 0, ots: [] });
  const [loadingCarga, setLoadingCarga] = useState(true);
  const [otSeleccionada, setOtSeleccionada] = useState<string>("");
  const [mostrarOTs, setMostrarOTs] = useState(false);

  useEffect(() => {
    cargarCarga();
  }, [refreshKey, mecanico.id]); // Recargar cuando cambie refreshKey o el mecánico

  // También recargar cuando se detecta una actualización en tiempo real
  useRealtimeUpdate({
    entityType: "workorder",
    onUpdate: (update) => {
      // Recargar si la actualización es de una OT que podría estar asignada a este mecánico
      // Verificar si la OT tiene el mecánico asignado
      if (update.data && update.data.mecanico_id) {
        // Si la actualización incluye un mecánico, verificar si es este
        if (update.data.mecanico_id === mecanico.id) {
          cargarCarga();
        }
      } else {
        // Si no hay información del mecánico, recargar de todas formas para estar seguro
        cargarCarga();
      }
    },
  });

  useRealtimeUpdate({
    entityType: "assignment",
    onUpdate: (update) => {
      // Si hay una actualización de asignación, verificar si es para este mecánico
      if (update.data && update.data.mecanico_id) {
        if (update.data.mecanico_id === mecanico.id) {
          cargarCarga();
        }
      } else {
        // Recargar de todas formas
        cargarCarga();
      }
    },
  });

  const cargarCarga = async () => {
    setLoadingCarga(true);
    try {
      // Cargar todas las OTs asignadas al mecánico
      // Agregar timestamp para evitar caché del navegador
      const timestamp = Date.now();
      const url = `${ENDPOINTS.WORK_ORDERS}?mecanico=${mecanico.id}&_t=${timestamp}`;
      console.log(`[MecanicoCard] Cargando carga de trabajo para mecánico ${mecanico.id} desde: ${url}`);
      
      const response = await fetch(url, {
        method: "GET",
        ...withSession(),
        cache: 'no-store', // No usar caché del navegador
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });

      if (response.ok) {
        const text = await response.text();
        if (!text || text.trim() === "") {
          console.log(`[MecanicoCard] Respuesta vacía para mecánico ${mecanico.id}`);
          setCargaTrabajo({ activas: 0, total: 0, ots: [] });
          return;
        }
        
        let data: any;
        try {
          data = JSON.parse(text);
        } catch (e) {
          console.error(`[MecanicoCard] Error al parsear respuesta para mecánico ${mecanico.id}:`, text);
          setCargaTrabajo({ activas: 0, total: 0, ots: [] });
          return;
        }
        
        const ots = data.results || data || [];
        console.log(`[MecanicoCard] OTs encontradas para mecánico ${mecanico.id}:`, ots.length, ots);
        
        // Separar por estado
        const activas = ots.filter((ot: any) => 
          ["EN_EJECUCION", "EN_PAUSA", "EN_DIAGNOSTICO", "ABIERTA"].includes(ot.estado)
        );
        
        console.log(`[MecanicoCard] OTs activas para mecánico ${mecanico.id}:`, activas.length, activas);
        setCargaTrabajo({ activas: activas.length, total: ots.length, ots: activas });
      } else {
        // Leer el cuerpo de la respuesta para obtener más detalles del error
        const errorText = await response.text().catch(() => "");
        let errorData: any = {};
        try {
          if (errorText) {
            errorData = JSON.parse(errorText);
          }
        } catch {
          errorData = { detail: errorText || `Error ${response.status}` };
        }
        console.error(`[MecanicoCard] Error al cargar carga de trabajo para mecánico ${mecanico.id}:`, {
          status: response.status,
          statusText: response.statusText,
          error: errorData,
          mecanicoId: mecanico.id,
          url: url
        });
        setCargaTrabajo({ activas: 0, total: 0, ots: [] });
      }
    } catch (error) {
      console.error(`[MecanicoCard] Error al cargar carga para mecánico ${mecanico.id}:`, error);
      setCargaTrabajo({ activas: 0, total: 0, ots: [] });
    } finally {
      setLoadingCarga(false);
    }
  };

  const getCargaColor = (carga: number) => {
    if (carga === 0) return "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300";
    if (carga <= 2) return "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300";
    return "bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300";
  };

  return (
    <div className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-4 mb-2">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {mecanico.get_full_name || `${mecanico.first_name || ""} ${mecanico.last_name || ""}`.trim() || mecanico.username}
            </h3>
            <span className={`px-2 py-1 text-xs font-medium rounded ${getCargaColor(cargaTrabajo.activas)}`}>
              {loadingCarga ? "Cargando..." : `${cargaTrabajo.activas} OTs activas`}
            </span>
            {cargaTrabajo.total > 0 && (
              <span className="px-2 py-1 text-xs font-medium rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                {cargaTrabajo.total} OTs totales
              </span>
            )}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
            <div>
              <span>Email: {mecanico.email || "N/A"}</span>
            </div>
            {cargaTrabajo.activas > 0 && (
              <div>
                <button
                  onClick={() => setMostrarOTs(!mostrarOTs)}
                  className="text-blue-600 dark:text-blue-400 hover:underline text-xs"
                >
                  {mostrarOTs ? "Ocultar" : "Ver"} OTs asignadas ({cargaTrabajo.activas})
                </button>
              </div>
            )}
          </div>
          {mostrarOTs && cargaTrabajo.ots.length > 0 && (
            <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600">
              <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                OTs Asignadas:
              </h4>
              <div className="space-y-1">
                {cargaTrabajo.ots.map((ot: any) => (
                  <div
                    key={ot.id}
                    className="text-xs text-gray-700 dark:text-gray-300 flex items-center justify-between"
                  >
                    <span>
                      OT #{ot.id.slice(0, 8)} - {ot.vehiculo_patente || ot.vehiculo?.patente} 
                      <span className="ml-2 px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300">
                        {ot.estado}
                      </span>
                    </span>
                    <Link
                      href={`/workorders/${ot.id}`}
                      className="text-blue-600 dark:text-blue-400 hover:underline ml-2"
                    >
                      Ver
                    </Link>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        <div className="ml-4">
          {otsPendientes.length > 0 && (
            <div className="flex gap-2">
              <select
                value={otSeleccionada}
                onChange={(e) => setOtSeleccionada(e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">Seleccionar OT...</option>
                {otsPendientes.map((ot) => (
                  <option key={ot.id} value={ot.id}>
                    OT #{ot.id.slice(0, 8)} - {ot.vehiculo_patente || ot.vehiculo?.patente}
                  </option>
                ))}
              </select>
              <button
                onClick={() => {
                  if (otSeleccionada) {
                    onAsignar(otSeleccionada, mecanico.id);
                    setOtSeleccionada("");
                  }
                }}
                disabled={!otSeleccionada}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Asignar
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

