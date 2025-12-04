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
 * Vista de Gestión de Vehículos para Coordinador de Zona.
 * 
 * Muestra:
 * - Crear vehículo
 * - Editar ficha técnica
 * - Subir documentos administrativos (padrón, seguros, facturas)
 * 
 * Permisos:
 * - Solo COORDINADOR_ZONA, ADMIN pueden acceder
 */
export default function CoordinadorVehiculosPage() {
  const router = useRouter();
  const toast = useToast();
  const { hasRole } = useAuth();

  const [vehiculos, setVehiculos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    cargarVehiculos();
  }, []);

  const cargarVehiculos = async () => {
    setLoading(true);
    try {
      const response = await fetch(ENDPOINTS.VEHICLES, {
        method: "GET",
        ...withSession(),
      });

      if (response.ok) {
        const data = await response.json();
        setVehiculos(data.results || data || []);
      }
    } catch (error) {
      console.error("Error al cargar vehículos:", error);
      toast.error("Error al cargar vehículos");
    } finally {
      setLoading(false);
    }
  };

  return (
    <RoleGuard allow={["COORDINADOR_ZONA", "ADMIN"]}>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Gestión de Vehículos
          </h1>
          <div className="flex gap-2">
            <Link
              href="/vehicles/create"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
            >
              Crear Vehículo
            </Link>
            <Link
              href="/coordinador"
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
            >
              ← Volver
            </Link>
          </div>
        </div>

        {/* Lista de Vehículos */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Vehículos de la Zona
            </h2>
          </div>
          {loading ? (
            <div className="p-6 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando vehículos...</p>
            </div>
          ) : vehiculos.length === 0 ? (
            <div className="p-6 text-center text-gray-500 dark:text-gray-400">
              No hay vehículos registrados.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                      Patente
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                      Marca/Modelo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                      Estado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                      Zona
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {vehiculos.map((vehiculo) => (
                    <tr key={vehiculo.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                        {vehiculo.patente}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {vehiculo.marca} {vehiculo.modelo}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded ${
                            vehiculo.estado === "ACTIVO"
                              ? "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300"
                              : "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300"
                          }`}
                        >
                          {vehiculo.estado}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {vehiculo.zona || "N/A"}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <Link
                          href={`/vehicles/${vehiculo.id}/edit`}
                          className="text-blue-600 hover:text-blue-900 dark:text-blue-400 mr-4"
                        >
                          Editar
                        </Link>
                        <Link
                          href={`/vehicles/${vehiculo.id}`}
                          className="text-gray-600 hover:text-gray-900 dark:text-gray-400"
                        >
                          Ver
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </RoleGuard>
  );
}

