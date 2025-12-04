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
 * Vista de Auditoría de Vehículos para Subgerente Nacional.
 * 
 * Muestra:
 * - Historial completo de mantenciones
 * - Evidencias (solo lectura)
 * - OTs agrupadas por tipo
 * 
 * Permisos:
 * - Solo EJECUTIVO, ADMIN pueden acceder
 */
export default function SubgerenteAuditoriaPage() {
  const router = useRouter();
  const toast = useToast();
  const { hasRole } = useAuth();

  const [vehiculos, setVehiculos] = useState<any[]>([]);
  const [vehiculoSeleccionado, setVehiculoSeleccionado] = useState<any>(null);
  const [historial, setHistorial] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    cargarVehiculos();
  }, []);

  const cargarVehiculos = async () => {
    setLoading(true);
    try {
      let todosVehiculos: any[] = [];
      let nextUrl: string | null = ENDPOINTS.VEHICLES;
      
      // Cargar todos los vehículos con paginación
      while (nextUrl) {
        const response = await fetch(nextUrl, {
          method: "GET",
          ...withSession(),
        });

        if (response.ok) {
          const data = await response.json();
          const vehiculosPagina = data.results || data || [];
          todosVehiculos = [...todosVehiculos, ...vehiculosPagina];
          
          // Si hay siguiente página, continuar
          // data.next viene como URL completa, extraer solo el path
          if (data.next) {
            try {
              const url = new URL(data.next);
              nextUrl = url.pathname + url.search;
            } catch {
              nextUrl = null;
            }
          } else {
            nextUrl = null;
          }
        } else {
          break;
        }
      }
      
      setVehiculos(todosVehiculos);
    } catch (error) {
      console.error("Error al cargar vehículos:", error);
      toast.error("Error al cargar vehículos");
    } finally {
      setLoading(false);
    }
  };

  const cargarHistorial = async (vehiculoId: string) => {
    try {
      const response = await fetch(`${ENDPOINTS.VEHICLES}${vehiculoId}/historial/`, {
        method: "GET",
        ...withSession(),
      });

      if (response.ok) {
        const data = await response.json();
        // El endpoint retorna un objeto con eventos, ordenes_trabajo, ingresos, etc.
        // Usar eventos si está disponible, sino usar ordenes_trabajo como fallback
        const eventos = data.eventos || data.results || [];
        setHistorial(eventos);
        
        const vehiculo = vehiculos.find((v) => v.id === vehiculoId);
        setVehiculoSeleccionado(vehiculo);
      } else {
        const errorData = await response.json().catch(() => ({ detail: "Error al cargar historial" }));
        toast.error(errorData.detail || "Error al cargar historial");
      }
    } catch (error) {
      console.error("Error al cargar historial:", error);
      toast.error("Error al cargar historial");
    }
  };

  return (
    <RoleGuard allow={["EJECUTIVO", "ADMIN"]}>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Auditoría de Vehículos
          </h1>
          <Link
            href="/subgerente/dashboard"
            className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
          >
            ← Volver
          </Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Lista de Vehículos */}
          <div className="lg:col-span-1">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Vehículos
                </h2>
              </div>
              <div className="divide-y divide-gray-200 dark:divide-gray-700 max-h-96 overflow-y-auto">
                {loading ? (
                  <div className="p-4 text-center">
                    <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900 dark:border-gray-100"></div>
                  </div>
                ) : vehiculos.length > 0 ? (
                  vehiculos.map((vehiculo) => (
                    <button
                      key={vehiculo.id}
                      onClick={() => cargarHistorial(vehiculo.id)}
                      className={`w-full p-4 text-left hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors ${
                        vehiculoSeleccionado?.id === vehiculo.id ? "bg-blue-50 dark:bg-blue-900/20" : ""
                      }`}
                    >
                      <div className="font-medium text-gray-900 dark:text-white">
                        {vehiculo.patente || vehiculo.vehiculo_detalle?.patente}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        {vehiculo.marca_detalle?.nombre || vehiculo.marca} {vehiculo.modelo}
                      </div>
                    </button>
                  ))
                ) : (
                  <div className="p-4 text-center text-gray-500 dark:text-gray-400">
                    No hay vehículos registrados.
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Historial del Vehículo Seleccionado */}
          <div className="lg:col-span-2">
            {vehiculoSeleccionado ? (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
                  Historial Completo - {vehiculoSeleccionado.patente}
                </h2>
                {historial.length > 0 ? (
                  <div className="space-y-4">
                    {historial.map((evento: any) => (
                      <div
                        key={evento.id}
                        className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-gray-900 dark:text-white">
                            {evento.tipo_evento || "Evento"}
                          </span>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {evento.creado_en 
                              ? new Date(evento.creado_en).toLocaleString()
                              : evento.fecha_ingreso 
                              ? new Date(evento.fecha_ingreso).toLocaleString()
                              : "Sin fecha"}
                          </span>
                        </div>
                        {evento.descripcion && (
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                            {evento.descripcion}
                          </p>
                        )}
                        {evento.falla && (
                          <p className="text-sm text-red-600 dark:text-red-400 mb-2">
                            <strong>Falla:</strong> {evento.falla}
                          </p>
                        )}
                        <div className="grid grid-cols-2 gap-2 text-xs text-gray-600 dark:text-gray-400 mb-2">
                          {evento.estado_antes && (
                            <div>
                              <strong>Estado antes:</strong> {evento.estado_antes}
                            </div>
                          )}
                          {evento.estado_despues && (
                            <div>
                              <strong>Estado después:</strong> {evento.estado_despues}
                            </div>
                          )}
                        </div>
                        {evento.tiempo_permanencia && (
                          <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                            <strong>Tiempo de permanencia:</strong> {evento.tiempo_permanencia}
                          </p>
                        )}
                        {evento.ot && (
                          <Link
                            href={`/workorders/${evento.ot.id || evento.ot}`}
                            className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 mt-2 inline-block"
                          >
                            Ver OT #{typeof evento.ot === 'string' ? evento.ot.slice(0, 8) : evento.ot.id?.slice(0, 8) || evento.ot.id}
                          </Link>
                        )}
                        {evento.backup_patente && (
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                            <strong>Backup utilizado:</strong> {evento.backup_patente}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 dark:text-gray-400">
                    No hay historial registrado para este vehículo.
                  </p>
                )}
              </div>
            ) : (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 text-center">
                <p className="text-gray-500 dark:text-gray-400">
                  Selecciona un vehículo para ver su historial completo.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </RoleGuard>
  );
}

