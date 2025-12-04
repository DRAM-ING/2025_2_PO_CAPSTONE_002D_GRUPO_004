"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";
import RoleGuard from "@/components/RoleGuard";
import { useDataRefresh } from "@/lib/dataRefresh";

export default function SchedulingPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const itemsPerPage = 20;
  const toast = useToast();
  const { hasRole } = useAuth();

  async function load(page: number = 1) {
    try {
      const r = await fetch(`/api/proxy/scheduling/agendas/?page=${page}&page_size=${itemsPerPage}`, {
        credentials: "include",
      });
      
      if (!r.ok) {
        if (r.status === 401 || r.status === 404) {
          console.warn("No autorizado o sin datos para ver agenda");
          setRows([]);
          return;
        }
        // Solo lanzar error para errores críticos (500+)
        if (r.status >= 500) {
          throw new Error(`HTTP ${r.status}`);
        }
        // Para otros errores, simplemente retornar sin mostrar alerta
        console.warn(`Respuesta HTTP ${r.status} - sin datos disponibles`);
        setRows([]);
        return;
      }
      
      const text = await r.text();
      if (!text || text.trim() === "") {
        setRows([]);
        return;
      }
      
      const j = JSON.parse(text);
      setRows(j.results ?? j ?? []);
      setTotalPages(Math.ceil((j.count || j.results?.length || 0) / itemsPerPage));
    } catch (e) {
      console.error("Error cargando agenda", e);
      toast.error("Error al cargar agenda");
      setRows([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load(currentPage);
  }, [currentPage]);

  // Escuchar eventos de refresh de datos
  useDataRefresh("SCHEDULING", () => load(currentPage));

  const canEdit = hasRole(["ADMIN", "SUPERVISOR", "COORDINADOR_ZONA"]);

  const getEstadoColor = (estado: string) => {
    const colors: Record<string, string> = {
      PROGRAMADA: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
      CONFIRMADA: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
      EN_PROCESO: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
      COMPLETADA: "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200",
      CANCELADA: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
      REPROGRAMADA: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200",
    };
    return colors[estado] || "bg-gray-100 text-gray-800";
  };

  return (
    <RoleGuard allow={["ADMIN", "SUPERVISOR", "COORDINADOR_ZONA"]}>
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Agenda y Programación</h1>
          {canEdit && (
            <Link 
              href="/scheduling/create" 
              className="px-4 py-2 text-white rounded-lg transition-colors font-medium shadow-sm hover:shadow"
              style={{ backgroundColor: '#003DA5' }}
            >
              + Nueva Programación
            </Link>
          )}
        </div>

        <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
          <table className="min-w-full">
            <thead className="bg-gray-100 dark:bg-gray-700">
              <tr>
                <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Vehículo</th>
                <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Fecha Programada</th>
                <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Tipo</th>
                <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Estado</th>
                <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Zona</th>
                <th className="p-3 text-right text-sm font-semibold text-gray-700 dark:text-gray-300">Acciones</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="p-6 text-center text-gray-500">
                    Cargando agenda...
                  </td>
                </tr>
              ) : rows.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-6 text-center text-gray-500">
                    No hay programaciones registradas
                  </td>
                </tr>
              ) : (
                rows.map((row) => (
                  <tr key={row.id} className="border-t border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="p-3 text-sm text-gray-900 dark:text-gray-100">
                      {row.vehiculo_patente || "N/A"}
                    </td>
                    <td className="p-3 text-sm text-gray-900 dark:text-gray-100">
                      {row.fecha_programada ? new Date(row.fecha_programada).toLocaleString('es-CL') : "N/A"}
                    </td>
                    <td className="p-3 text-sm text-gray-900 dark:text-gray-100">
                      {row.tipo_mantenimiento || "N/A"}
                    </td>
                    <td className="p-3 text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getEstadoColor(row.estado)}`}>
                        {row.estado || "N/A"}
                      </span>
                    </td>
                    <td className="p-3 text-sm text-gray-900 dark:text-gray-100">
                      {row.zona || "N/A"}
                    </td>
                    <td className="p-3 text-right">
                      <div className="flex justify-end gap-2">
                      <Link
                        href={`/scheduling/${row.id}`}
                        className="px-3 py-1 text-sm bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 rounded transition-colors"
                      >
                        Ver
                      </Link>
                      {canEdit && (
                        <>
                          <Link
                            href={`/scheduling/${row.id}/edit`}
                            className="px-3 py-1 text-sm text-white rounded transition-colors"
                            style={{ backgroundColor: '#003DA5' }}
                          >
                            Editar
                          </Link>
                        </>
                      )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>

          {totalPages > 1 && (
            <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <div className="text-sm text-gray-700 dark:text-gray-300">
                Página {currentPage} de {totalPages}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 text-sm bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Anterior
                </button>
                <button
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="px-3 py-1 text-sm bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Siguiente
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </RoleGuard>
  );
}

