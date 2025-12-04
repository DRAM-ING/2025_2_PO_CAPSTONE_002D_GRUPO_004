"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";
import RoleGuard from "@/components/RoleGuard";
import Link from "next/link";
import { ENDPOINTS } from "@/lib/constants";
import { withSession } from "@/lib/api.client";

/**
 * Página para ver la lista de ingresos del día.
 * 
 * Muestra:
 * - Tabla con patente, hora ingreso, hora salida, taller, estado
 * - Filtro por patente
 * - Información completa de cada ingreso
 * 
 * Permisos:
 * - GUARDIA, ADMIN, SUPERVISOR
 */
export default function IngresosHoyPage() {
  const router = useRouter();
  const toast = useToast();
  const { hasRole } = useAuth();

  const [ingresos, setIngresos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtroPatente, setFiltroPatente] = useState("");

  const canAccess = hasRole(["GUARDIA", "ADMIN", "SUPERVISOR", "JEFE_TALLER"]);

  useEffect(() => {
    if (canAccess) {
      cargarIngresos();
    }
  }, [canAccess]);

  const cargarIngresos = async () => {
    setLoading(true);
    try {
      const url = filtroPatente
        ? `${ENDPOINTS.VEHICLES_INGRESOS_HOY}?patente=${encodeURIComponent(filtroPatente)}`
        : ENDPOINTS.VEHICLES_INGRESOS_HOY;

      const response = await fetch(url, {
        method: "GET",
        ...withSession(),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `Error ${response.status}` }));
        throw new Error(errorData.detail || `Error al cargar ingresos: ${response.status}`);
      }

      const data = await response.json();
      setIngresos(data.ingresos || []);
    } catch (error) {
      console.error("Error al cargar ingresos:", error);
      toast.error("Error al cargar la lista de ingresos");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (canAccess) {
      const timeoutId = setTimeout(() => {
        cargarIngresos();
      }, 300);
      return () => clearTimeout(timeoutId);
    }
  }, [filtroPatente]);

  if (!canAccess) {
    return (
      <RoleGuard allow={["GUARDIA", "ADMIN", "SUPERVISOR", "JEFE_TALLER"]} redirectTo="/vehicles">
        <div></div>
      </RoleGuard>
    );
  }

  return (
    <RoleGuard allow={["GUARDIA", "ADMIN", "SUPERVISOR", "JEFE_TALLER"]} redirectTo="/vehicles">
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Ingresos del Día
          </h1>
          <div className="flex gap-2">
            <Link
              href="/vehicles/ingresos-historial"
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors font-medium"
            >
              📜 Ver Historial Completo
            </Link>
            <Link
              href="/vehicles/ingreso"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
            >
              Registrar Ingreso
            </Link>
            <Link
              href="/vehicles/salida"
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors font-medium"
            >
              Registrar Salida
            </Link>
            <Link
              href="/vehicles"
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
            >
              ← Volver
            </Link>
          </div>
        </div>

        {/* Filtro */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="flex gap-4 items-end">
            <div className="flex-1">
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
            <button
              onClick={cargarIngresos}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
            >
              Buscar
            </button>
            {filtroPatente && (
              <button
                onClick={() => {
                  setFiltroPatente("");
                  cargarIngresos();
                }}
                className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
              >
                Limpiar
              </button>
            )}
          </div>
        </div>

        {/* Tabla de Ingresos */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            {loading ? (
              <div className="p-6 text-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
                <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando ingresos...</p>
              </div>
            ) : ingresos.length === 0 ? (
              <div className="p-6 text-center text-gray-500 dark:text-gray-400">
                No hay ingresos registrados hoy.
              </div>
            ) : (
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Patente
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Hora Ingreso
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Hora Salida
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Guardia Ingreso
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Estado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Acciones
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Ticket
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {ingresos.map((ingreso) => {
                    const vehiculo = ingreso.vehiculo_detalle || ingreso.vehiculo;
                    const guardia = ingreso.guardia_detalle || ingreso.guardia;
                    return (
                      <tr key={ingreso.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {vehiculo?.patente || ingreso.vehiculo_patente || "N/A"}
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            {vehiculo?.marca_nombre || vehiculo?.marca?.nombre || ""} {vehiculo?.modelo || ""}
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
                            {guardia?.nombre_completo || ingreso.guardia_nombre || guardia?.username || "N/A"}
                          </div>
                          {guardia?.username && guardia?.nombre_completo && (
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              ({guardia.username})
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
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          {!ingreso.salio && (
                            <Link
                              href={`/vehicles/salida`}
                              className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
                            >
                              Registrar Salida
                            </Link>
                          )}
                          {ingreso.vehiculo && ingreso.vehiculo.id && ingreso.vehiculo.id !== "undefined" ? (
                            <Link
                              href={`/vehicles/${ingreso.vehiculo.id}`}
                              className="ml-4 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-300"
                            >
                              Ver Vehículo
                            </Link>
                          ) : null}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={async () => {
                              try {
                                const response = await fetch(
                                  ENDPOINTS.VEHICLES_TICKET_INGRESO(ingreso.id),
                                  {
                                    method: "GET",
                                    ...withSession(),
                                  }
                                );

                                if (!response.ok) {
                                  toast.error("Error al generar el ticket PDF");
                                  return;
                                }

                                // Descargar el PDF
                                const blob = await response.blob();
                                const url = window.URL.createObjectURL(blob);
                                const a = document.createElement("a");
                                a.href = url;
                                a.download = `ticket_ingreso_${ingreso.id.slice(0, 8)}.pdf`;
                                document.body.appendChild(a);
                                a.click();
                                window.URL.revokeObjectURL(url);
                                document.body.removeChild(a);
                                toast.success("Ticket PDF descargado correctamente");
                              } catch (error) {
                                console.error("Error al descargar PDF:", error);
                                toast.error("Error al descargar el ticket PDF");
                              }
                            }}
                            className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
                            title="Descargar Ticket PDF"
                          >
                            📄 PDF
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </RoleGuard>
  );
}

