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
 * Página para asignar vehículos a choferes.
 * 
 * Permite:
 * - Ver lista de choferes sin vehículo asignado
 * - Ver lista de vehículos disponibles
 * - Asignar un vehículo a un chofer
 * - Reasignar vehículo a otro chofer
 * - Ver historial de asignaciones
 * 
 * Permisos:
 * - ADMIN, SUPERVISOR, JEFE_TALLER, COORDINADOR_ZONA
 */
export default function AsignacionVehiculosPage() {
  const router = useRouter();
  const toast = useToast();
  const { hasRole } = useAuth();

  const [choferes, setChoferes] = useState<any[]>([]);
  const [vehiculos, setVehiculos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [asignando, setAsignando] = useState(false);
  const [filtroChofer, setFiltroChofer] = useState<string>("");
  const [filtroVehiculo, setFiltroVehiculo] = useState<string>("");
  const [mostrarSinAsignar, setMostrarSinAsignar] = useState(false);

  const canAccess = hasRole(["ADMIN", "SUPERVISOR", "JEFE_TALLER", "COORDINADOR_ZONA"]);

  useEffect(() => {
    if (canAccess) {
      cargarDatos();
    }
  }, [canAccess]);

  const cargarDatos = async () => {
    setLoading(true);
    try {
      // Cargar choferes
      const choferesResponse = await fetch(`${ENDPOINTS.DRIVERS}?activo=true`, {
        method: "GET",
        ...withSession(),
      });

      if (choferesResponse.ok) {
        const choferesData = await choferesResponse.json();
        setChoferes(choferesData.results || choferesData || []);
      }

      // Cargar vehículos disponibles (estado ACTIVO)
      const vehiculosResponse = await fetch(`${ENDPOINTS.VEHICLES}?estado=ACTIVO`, {
        method: "GET",
        ...withSession(),
      });

      if (vehiculosResponse.ok) {
        const vehiculosData = await vehiculosResponse.json();
        setVehiculos(vehiculosData.results || vehiculosData || []);
      }
    } catch (error) {
      console.error("Error al cargar datos:", error);
      toast.error("Error al cargar información");
    } finally {
      setLoading(false);
    }
  };

  const handleAsignar = async (choferId: string, vehiculoId: string) => {
    setAsignando(true);
    try {
      const response = await fetch(ENDPOINTS.DRIVER_ASIGNAR_VEHICULO(choferId), {
        method: "POST",
        ...withSession(),
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          vehiculo_id: vehiculoId,
        }),
      });

      const text = await response.text();
      
      // Detectar si la respuesta es HTML (error del servidor)
      if (text.trim().startsWith("<!DOCTYPE") || text.trim().startsWith("<html")) {
        console.error("Backend retornó HTML en lugar de JSON:", text.substring(0, 200));
        toast.error("Error del servidor. Por favor intenta nuevamente.");
        return;
      }
      
      let data;
      try {
        data = JSON.parse(text);
      } catch (e) {
        console.error("Error parseando JSON:", e, "Response:", text.substring(0, 200));
        toast.error("Error procesando respuesta del servidor");
        return;
      }

      if (!response.ok) {
        const errorMessage = data.detail || data.message || "Error al asignar vehículo";
        toast.error(errorMessage);
        return;
      }

      toast.success("Vehículo asignado correctamente");
      await cargarDatos(); // Recargar datos
    } catch (error) {
      console.error("Error al asignar:", error);
      toast.error("Error al asignar vehículo");
    } finally {
      setAsignando(false);
    }
  };

  // Filtrar choferes
  const choferesFiltrados = choferes.filter((chofer) => {
    if (mostrarSinAsignar && chofer.vehiculo_asignado) return false;
    if (filtroChofer && !chofer.nombre_completo.toLowerCase().includes(filtroChofer.toLowerCase())) return false;
    return true;
  });

  // Filtrar vehículos
  const vehiculosFiltrados = vehiculos.filter((vehiculo) => {
    if (filtroVehiculo && !vehiculo.patente.toLowerCase().includes(filtroVehiculo.toLowerCase())) return false;
    return true;
  });

  if (!canAccess) {
    return (
      <RoleGuard allow={["ADMIN", "SUPERVISOR", "JEFE_TALLER", "COORDINADOR_ZONA"]}>
        <div></div>
      </RoleGuard>
    );
  }

  return (
    <RoleGuard allow={["ADMIN", "SUPERVISOR", "JEFE_TALLER", "COORDINADOR_ZONA"]}>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Asignación de Vehículos a Choferes
          </h1>
          <Link
            href="/drivers"
            className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
          >
            ← Volver a Choferes
          </Link>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando información...</p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Lista de Choferes */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                    Choferes ({choferesFiltrados.length})
                  </h2>
                </div>
                
                {/* Filtros */}
                <div className="space-y-2">
                  <input
                    type="text"
                    placeholder="Buscar chofer por nombre..."
                    value={filtroChofer}
                    onChange={(e) => setFiltroChofer(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                  />
                  <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                    <input
                      type="checkbox"
                      checked={mostrarSinAsignar}
                      onChange={(e) => setMostrarSinAsignar(e.target.checked)}
                      className="rounded"
                    />
                    Mostrar solo choferes sin vehículo asignado
                  </label>
                </div>
              </div>

              <div className="divide-y divide-gray-200 dark:divide-gray-700 max-h-[600px] overflow-y-auto">
                {choferesFiltrados.length === 0 ? (
                  <div className="p-6 text-center text-gray-500 dark:text-gray-400">
                    No hay choferes disponibles
                  </div>
                ) : (
                  choferesFiltrados.map((chofer) => (
                    <div
                      key={chofer.id}
                      className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="font-semibold text-gray-900 dark:text-white">
                            {chofer.nombre_completo}
                          </h3>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            RUT: {chofer.rut}
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            Zona: {chofer.zona || "N/A"}
                          </p>
                          {chofer.vehiculo_asignado && (
                            <div className="mt-2">
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300">
                                Vehículo: {chofer.vehiculo_asignado_info?.patente || (typeof chofer.vehiculo_asignado === 'string' ? chofer.vehiculo_asignado : chofer.vehiculo_asignado?.patente) || "N/A"}
                              </span>
                            </div>
                          )}
                        </div>
                        <div className="ml-4">
                          <select
                            onChange={(e) => {
                              if (e.target.value) {
                                handleAsignar(chofer.id, e.target.value);
                                e.target.value = ""; // Resetear selección
                              }
                            }}
                            disabled={asignando}
                            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            <option value="">
                              {chofer.vehiculo_asignado ? "Reasignar..." : "Asignar vehículo..."}
                            </option>
                            {vehiculosFiltrados.map((vehiculo) => (
                              <option key={vehiculo.id} value={vehiculo.id}>
                                {vehiculo.patente} - {vehiculo.marca} {vehiculo.modelo}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Lista de Vehículos */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  Vehículos Disponibles ({vehiculosFiltrados.length})
                </h2>
                
                {/* Filtro */}
                <input
                  type="text"
                  placeholder="Buscar vehículo por patente..."
                  value={filtroVehiculo}
                  onChange={(e) => setFiltroVehiculo(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                />
              </div>

              <div className="divide-y divide-gray-200 dark:divide-gray-700 max-h-[600px] overflow-y-auto">
                {vehiculosFiltrados.length === 0 ? (
                  <div className="p-6 text-center text-gray-500 dark:text-gray-400">
                    No hay vehículos disponibles
                  </div>
                ) : (
                  vehiculosFiltrados.map((vehiculo) => {
                    const choferAsignado = choferes.find((c) => {
                      if (c.vehiculo_asignado_info?.id === vehiculo.id) return true;
                      if (typeof c.vehiculo_asignado === 'string' && c.vehiculo_asignado === vehiculo.id) return true;
                      if (c.vehiculo_asignado?.id === vehiculo.id) return true;
                      return false;
                    });
                    
                    return (
                      <div
                        key={vehiculo.id}
                        className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h3 className="font-semibold text-gray-900 dark:text-white">
                              {vehiculo.patente}
                            </h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              {vehiculo.marca} {vehiculo.modelo} ({vehiculo.anio || "N/A"})
                            </p>
                            {choferAsignado && (
                              <div className="mt-2">
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300">
                                  Asignado a: {choferAsignado.nombre_completo}
                                </span>
                              </div>
                            )}
                          </div>
                          <div className="ml-4">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              choferAsignado
                                ? "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300"
                                : "bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300"
                            }`}>
                              {choferAsignado ? "Asignado" : "Disponible"}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        )}

        {/* Información adicional */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">
            Información
          </h3>
          <ul className="text-sm text-gray-700 dark:text-gray-300 space-y-1 list-disc list-inside">
            <li>Puedes asignar un vehículo a un chofer seleccionándolo desde el dropdown.</li>
            <li>Si un chofer ya tiene un vehículo asignado, se puede reasignar a otro.</li>
            <li>Las asignaciones anteriores se guardan en el historial automáticamente.</li>
            <li>Solo se muestran vehículos con estado ACTIVO y choferes activos.</li>
          </ul>
        </div>
      </div>
    </RoleGuard>
  );
}

