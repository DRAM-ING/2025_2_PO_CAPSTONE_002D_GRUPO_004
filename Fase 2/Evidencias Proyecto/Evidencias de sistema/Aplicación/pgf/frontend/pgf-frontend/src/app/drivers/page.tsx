"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";
import { ENDPOINTS } from "@/lib/constants";
import { withSession } from "@/lib/api.client";
import { useDataRefresh } from "@/lib/dataRefresh";

export default function DriversPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const itemsPerPage = 20;
  const toast = useToast();
  const { hasRole } = useAuth();

  async function load(page: number = 1) {
    try {
      const r = await fetch(`${ENDPOINTS.DRIVERS}?page=${page}&page_size=${itemsPerPage}`, {
        ...withSession(),
      });
      
      if (!r.ok) {
        if (r.status === 401 || r.status === 404) {
          console.warn("No autorizado o sin datos para ver choferes");
          setRows([]);
          return;
        }
        // Solo mostrar error para errores críticos (500, 502, 503, etc.)
        if (r.status >= 500) {
          const errorText = await r.text().catch(() => "Error desconocido");
          console.error(`Error HTTP ${r.status} al cargar choferes:`, errorText);
          toast.error(`Error al cargar choferes: ${r.status}`);
        } else {
          console.warn(`Respuesta HTTP ${r.status} - sin datos disponibles`);
        }
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
      setTotalItems(j.count || j.results?.length || 0);
    } catch (e) {
      console.error("Error cargando choferes", e);
      toast.error("Error al cargar choferes");
      setRows([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load(currentPage);
  }, [currentPage]);

  // Escuchar eventos de refresh de datos
  useDataRefresh("DRIVERS", () => load(currentPage));

  const canEdit = hasRole(["ADMIN", "SUPERVISOR", "JEFE_TALLER"]);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Choferes</h1>
        <div className="flex gap-3">
          {canEdit && (
            <>
              <Link 
                href="/drivers/asignacion" 
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors font-medium shadow-sm hover:shadow"
              >
                🚗 Asignar Vehículos
              </Link>
              <Link 
                href="/drivers/create" 
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium shadow-sm hover:shadow"
                style={{ backgroundColor: '#003DA5' }}
              >
                + Nuevo Chofer
              </Link>
            </>
          )}
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
        <table className="min-w-full">
          <thead className="bg-gray-100 dark:bg-gray-700">
            <tr>
              <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Nombre</th>
              <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">RUT</th>
              <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Teléfono</th>
              <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Zona</th>
              <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Vehículo</th>
              <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Estado</th>
              <th className="p-3 text-right text-sm font-semibold text-gray-700 dark:text-gray-300">Acciones</th>
            </tr>
          </thead>

          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} className="p-6 text-center text-gray-500">
                  Cargando choferes...
                </td>
              </tr>
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={7} className="p-6 text-center text-gray-500">
                  No hay choferes registrados
                </td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr key={row.id} className="border-t border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                  <td className="p-3 text-sm text-gray-900 dark:text-gray-100">
                    {row.nombre_completo || "N/A"}
                  </td>
                  <td className="p-3 text-sm text-gray-900 dark:text-gray-100">
                    {row.rut || "N/A"}
                  </td>
                  <td className="p-3 text-sm text-gray-900 dark:text-gray-100">
                    {row.telefono || "N/A"}
                  </td>
                  <td className="p-3 text-sm text-gray-900 dark:text-gray-100">
                    {row.zona || "N/A"}
                  </td>
                  <td className="p-3 text-sm text-gray-900 dark:text-gray-100">
                    {row.vehiculo_patente || "Sin asignar"}
                  </td>
                  <td className="p-3 text-sm">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      row.activo 
                        ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" 
                        : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                    }`}>
                      {row.activo ? "Activo" : "Inactivo"}
                    </span>
                  </td>
                  <td className="p-3 text-right">
                    <div className="flex justify-end gap-2">
                      <Link
                        href={`/drivers/${row.id}`}
                        className="px-3 py-1 text-sm bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 rounded transition-colors"
                      >
                        Ver
                      </Link>
                      {canEdit && (
                        <>
                          <Link
                            href={`/drivers/${row.id}/edit`}
                            className="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
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
              Mostrando {((currentPage - 1) * itemsPerPage) + 1} a {Math.min(currentPage * itemsPerPage, totalItems)} de {totalItems} choferes
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 text-sm bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Anterior
              </button>
              <span className="px-3 py-1 text-sm text-gray-700 dark:text-gray-300">
                Página {currentPage} de {totalPages}
              </span>
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
  );
}

