"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";
import RoleGuard from "@/components/RoleGuard";
import Link from "next/link";
import { ENDPOINTS } from "@/lib/constants";
import { withSession } from "@/lib/api.client";
import Pagination from "@/components/Pagination";

/**
 * Página para ver el historial completo de ingresos con filtros de fecha.
 * 
 * Muestra:
 * - Tabla con patente, hora ingreso, hora salida, taller, estado
 * - Filtros por fecha (desde/hasta), patente, estado de salida
 * - Paginación
 * - Información completa de cada ingreso
 * 
 * Permisos:
 * - GUARDIA, ADMIN, SUPERVISOR, JEFE_TALLER
 */
export default function IngresosHistorialPage() {
  const router = useRouter();
  const toast = useToast();
  const { hasRole } = useAuth();

  const [ingresos, setIngresos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtroPatente, setFiltroPatente] = useState("");
  const [filtroFechaDesde, setFiltroFechaDesde] = useState("");
  const [filtroFechaHasta, setFiltroFechaHasta] = useState("");
  const [filtroSalio, setFiltroSalio] = useState<string>("");
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const itemsPerPage = 50;

  const canAccess = hasRole(["GUARDIA", "ADMIN", "SUPERVISOR", "JEFE_TALLER"]);

  const cargarIngresos = async () => {
    if (!canAccess) return;
    
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append("page", currentPage.toString());
      params.append("page_size", itemsPerPage.toString());
      
      if (filtroPatente) {
        params.append("patente", filtroPatente);
      }
      if (filtroFechaDesde) {
        params.append("fecha_desde", filtroFechaDesde);
      }
      if (filtroFechaHasta) {
        params.append("fecha_hasta", filtroFechaHasta);
      }
      if (filtroSalio) {
        params.append("salio", filtroSalio);
      }

      const url = `${ENDPOINTS.VEHICLES_INGRESOS_HISTORIAL}?${params.toString()}`;

      const response = await fetch(url, {
        method: "GET",
        ...withSession(),
      });

      if (!response.ok) {
        let errorMessage = `Error ${response.status}`;
        try {
          const errorText = await response.text();
          if (errorText) {
            const errorData = JSON.parse(errorText);
            errorMessage = errorData.detail || errorMessage;
          }
        } catch (e) {
          // Si no se puede parsear el error, usar el mensaje por defecto
        }
        throw new Error(errorMessage);
      }

      const text = await response.text();
      if (!text || text.trim() === "") {
        setIngresos([]);
        setTotalPages(1);
        setTotalItems(0);
        return;
      }

      let data;
      try {
        data = JSON.parse(text);
      } catch (e) {
        console.error("Error parsing JSON:", e, "Response text:", text.substring(0, 200));
        throw new Error("Respuesta inválida del servidor");
      }

      setIngresos(data.results || []);
      setTotalPages(data.total_pages || 1);
      setTotalItems(data.count || 0);
    } catch (error) {
      console.error("Error al cargar historial:", error);
      toast.error(error instanceof Error ? error.message : "Error al cargar el historial de ingresos");
      setIngresos([]);
      setTotalPages(1);
      setTotalItems(0);
    } finally {
      setLoading(false);
    }
  };

  // Cargar cuando cambia la página o cuando se monta el componente
  useEffect(() => {
    if (canAccess) {
      cargarIngresos();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canAccess, currentPage]);

  // Resetear a página 1 cuando cambian los filtros (esto disparará el useEffect anterior)
  useEffect(() => {
    if (canAccess && currentPage !== 1) {
      setCurrentPage(1);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtroPatente, filtroFechaDesde, filtroFechaHasta, filtroSalio]);

  const limpiarFiltros = () => {
    setFiltroPatente("");
    setFiltroFechaDesde("");
    setFiltroFechaHasta("");
    setFiltroSalio("");
    setCurrentPage(1);
  };

  if (!canAccess) {
    return (
      <RoleGuard allow={["GUARDIA", "ADMIN", "SUPERVISOR", "JEFE_TALLER"]}>
        <div></div>
      </RoleGuard>
    );
  }

  return (
    <RoleGuard allow={["GUARDIA", "ADMIN", "SUPERVISOR", "JEFE_TALLER"]}>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Historial de Ingresos
          </h1>
          <div className="flex gap-2">
            <Link
              href="/vehicles/ingresos-hoy"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
            >
              Ver Ingresos de Hoy
            </Link>
            <Link
              href="/vehicles/ingreso"
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors font-medium"
            >
              Registrar Ingreso
            </Link>
            <Link
              href="/vehicles"
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
            >
              ← Volver
            </Link>
          </div>
        </div>

        {/* Filtros */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                Filtrar por Patente
              </label>
              <input
                type="text"
                value={filtroPatente}
                onChange={(e) => setFiltroPatente(e.target.value.toUpperCase())}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="ABC123"
              />
            </div>
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
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
              <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
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
              <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                Estado
              </label>
              <select
                value={filtroSalio}
                onChange={(e) => setFiltroSalio(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">Todos</option>
                <option value="false">En Taller</option>
                <option value="true">Salidos</option>
              </select>
            </div>
            <div className="flex items-end">
              <button
                onClick={limpiarFiltros}
                className="w-full px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
              >
                Limpiar Filtros
              </button>
            </div>
          </div>
        </div>

        {/* Información de resultados */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <p className="text-sm text-blue-800 dark:text-blue-300">
            Mostrando {ingresos.length} de {totalItems} ingresos
            {filtroFechaDesde || filtroFechaHasta ? (
              <span>
                {" "}en el rango seleccionado
              </span>
            ) : (
              <span> (últimos 30 días por defecto)</span>
            )}
          </p>
        </div>

        {/* Tabla de Ingresos */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            {loading ? (
              <div className="p-6 text-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
                <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando historial...</p>
              </div>
            ) : ingresos.length === 0 ? (
              <div className="p-6 text-center text-gray-500 dark:text-gray-400">
                No se encontraron ingresos con los filtros seleccionados.
              </div>
            ) : (
              <>
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Patente
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Fecha Ingreso
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Fecha Salida
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Guardia Ingreso
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Estado
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Kilometraje
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        OT Relacionadas
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Acciones
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {ingresos.map((ingreso) => {
                      // Usar vehiculo_detalle si está disponible, sino usar vehiculo
                      const vehiculo = ingreso.vehiculo_detalle || ingreso.vehiculo;
                      return (
                      <tr key={ingreso.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {vehiculo?.patente || ingreso.vehiculo_patente || "N/A"}
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            {vehiculo?.marca} {vehiculo?.modelo}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900 dark:text-white">
                            {new Date(ingreso.fecha_ingreso).toLocaleString()}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900 dark:text-white">
                            {ingreso.fecha_salida
                              ? new Date(ingreso.fecha_salida).toLocaleString()
                              : "Pendiente"}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900 dark:text-white">
                            {ingreso.guardia_detalle?.nombre_completo || ingreso.guardia_nombre || ingreso.guardia?.username || "N/A"}
                          </div>
                          {ingreso.guardia_detalle?.username && (
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              @{ingreso.guardia_detalle.username}
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`px-2 py-1 text-xs font-medium rounded ${
                              ingreso.salio
                                ? "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300"
                                : "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300"
                            }`}
                          >
                            {ingreso.salio ? "Salido" : "En Taller"}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900 dark:text-white">
                            {ingreso.kilometraje ? `${ingreso.kilometraje.toLocaleString()} km` : "N/A"}
                            {ingreso.kilometraje_salida && (
                              <div className="text-xs text-gray-500 dark:text-gray-400">
                                Salida: {ingreso.kilometraje_salida.toLocaleString()} km
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900 dark:text-white">
                            {ingreso.ot_relacionadas && ingreso.ot_relacionadas.length > 0 ? (
                              <div className="space-y-1">
                                {ingreso.ot_relacionadas.map((ot: any) => (
                                  <Link
                                    key={ot.id}
                                    href={`/workorders/${ot.id}`}
                                    className="block text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
                                  >
                                    OT {ot.id.substring(0, 8)} - {ot.estado}
                                  </Link>
                                ))}
                              </div>
                            ) : (
                              <span className="text-gray-400 dark:text-gray-500 text-xs">Sin OT</span>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          {(() => {
                            const vehiculoId = vehiculo?.id || (typeof ingreso.vehiculo === 'string' ? ingreso.vehiculo : ingreso.vehiculo?.id);
                            if (vehiculoId && vehiculoId !== "undefined" && typeof vehiculoId === 'string') {
                              return (
                                <Link
                                  href={`/vehicles/${vehiculoId}`}
                                  className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
                                >
                                  Ver Vehículo
                                </Link>
                              );
                            }
                            return <span className="text-gray-400 dark:text-gray-500 text-xs">N/A</span>;
                          })()}
                        </td>
                      </tr>
                    );
                    })}
                  </tbody>
                </table>
                {totalPages > 1 && (
                  <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                    <Pagination
                      currentPage={currentPage}
                      totalPages={totalPages}
                      onPageChange={setCurrentPage}
                    />
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </RoleGuard>
  );
}

