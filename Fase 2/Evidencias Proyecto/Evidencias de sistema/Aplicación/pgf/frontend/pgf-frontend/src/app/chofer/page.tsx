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
 * Vista principal para Chofer/Conductor.
 * 
 * Muestra:
 * - Estado actual de su vehículo asignado
 * - Estado de la OT actual (si existe)
 * - Notificaciones recientes
 * - Acceso rápido a historial
 * 
 * Permisos:
 * - Solo CHOFER puede acceder
 */
export default function ChoferPage() {
  const router = useRouter();
  const toast = useToast();
  const { user } = useAuth();

  const [vehiculo, setVehiculo] = useState<any>(null);
  const [otActual, setOtActual] = useState<any>(null);
  const [notificaciones, setNotificaciones] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    cargarDatos();
  }, []);

  const cargarDatos = async () => {
    setLoading(true);
    try {
      // Cargar vehículo asignado al chofer
      // Nota: Esto requiere que el backend tenga un endpoint para obtener vehículo por chofer
      // Por ahora, asumimos que hay un endpoint /api/v1/drivers/me/vehiculo/
      
      // Cargar notificaciones
      const notifResponse = await fetch(ENDPOINTS.NOTIFICATIONS_NO_LEIDAS, {
        method: "GET",
        ...withSession(),
      });

      if (notifResponse.ok) {
        const notifData = await notifResponse.json();
        setNotificaciones(notifData.results || []);
      }
    } catch (error) {
      console.error("Error al cargar datos:", error);
      toast.error("Error al cargar información");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <RoleGuard allow={["CHOFER"]}>
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
    <RoleGuard allow={["CHOFER"]}>
      <div className="p-6 max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Mi Vehículo
          </h1>
        </div>

        {/* Estado del Vehículo */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
            Estado Actual del Vehículo
          </h2>
          
          {vehiculo ? (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">Patente:</span>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    {vehiculo.patente}
                  </p>
                </div>
                <div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">Modelo:</span>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    {vehiculo.marca} {vehiculo.modelo}
                  </p>
                </div>
              </div>

              <div>
                <span className="text-sm text-gray-600 dark:text-gray-400">Estado:</span>
                <div className="mt-2">
                  <span
                    className={`px-3 py-1 text-sm font-medium rounded ${
                      vehiculo.estado === "ACTIVO"
                        ? "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300"
                        : vehiculo.estado === "EN_ESPERA"
                        ? "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300"
                        : "bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300"
                    }`}
                  >
                    {vehiculo.estado === "ACTIVO" && "Operativo"}
                    {vehiculo.estado === "EN_ESPERA" && "Esperando Revisión"}
                    {vehiculo.estado === "EN_MANTENIMIENTO" && "En Mantenimiento"}
                    {vehiculo.estado === "BAJA" && "Dado de Baja"}
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-gray-500 dark:text-gray-400">
              No tienes un vehículo asignado actualmente.
            </p>
          )}
        </div>

        {/* Estado de la OT */}
        {otActual && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              Estado de la Orden de Trabajo
            </h2>
            <div className="space-y-4">
              <div>
                <span className="text-sm text-gray-600 dark:text-gray-400">Estado:</span>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">
                  {otActual.estado}
                </p>
              </div>
              {otActual.mecanico && (
                <div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">Mecánico Asignado:</span>
                  <p className="text-lg text-gray-900 dark:text-white">
                    {otActual.mecanico_nombre || otActual.mecanico?.username}
                  </p>
                </div>
              )}
              <Link
                href={`/workorders/${otActual.id}`}
                className="inline-block px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
              >
                Ver Detalles de la OT
              </Link>
            </div>
          </div>
        )}

        {/* Notificaciones Recientes */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Notificaciones Recientes
            </h2>
            <Link
              href="/notifications"
              className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
            >
              Ver todas
            </Link>
          </div>
          {notificaciones.length > 0 ? (
            <div className="space-y-2">
              {notificaciones.slice(0, 5).map((notif) => (
                <div
                  key={notif.id}
                  className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600"
                >
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {notif.titulo}
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    {notif.mensaje}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    {new Date(notif.creada_en).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 dark:text-gray-400">
              No hay notificaciones nuevas.
            </p>
          )}
        </div>

        {/* Accesos Rápidos */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Link
            href="/chofer/historial"
            className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Historial de Ingresos
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Ver todos los registros pasados de ingresos al taller
            </p>
          </Link>
          <Link
            href="/chofer/comprobantes"
            className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Comprobantes
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Descargar comprobantes de ingreso y salida
            </p>
          </Link>
        </div>
      </div>
    </RoleGuard>
  );
}

