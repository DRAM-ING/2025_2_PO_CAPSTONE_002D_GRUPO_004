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
 * Dashboard de Auditoría para Auditor Interno.
 * 
 * Muestra:
 * - Últimos cambios críticos
 * - Actividad por usuario
 * - Evidencias marcadas como inválidas
 * 
 * Permisos:
 * - Solo ADMIN puede acceder (Auditor usa rol ADMIN con permisos de solo lectura)
 */
export default function AuditorDashboardPage() {
  const router = useRouter();
  const toast = useToast();
  const { hasRole } = useAuth();

  const [cambiosCriticos, setCambiosCriticos] = useState<any[]>([]);
  const [actividadUsuario, setActividadUsuario] = useState<any[]>([]);
  const [evidenciasInvalidadas, setEvidenciasInvalidadas] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    cargarDatos();
  }, []);

  const cargarDatos = async () => {
    setLoading(true);
    try {
      // Cargar cambios críticos
      const cambiosRes = await fetch(ENDPOINTS.AUDITORIA_CAMBIOS_CRITICOS, {
        method: "GET",
        ...withSession(),
      });
      if (cambiosRes.ok) {
        const cambios = await cambiosRes.json();
        setCambiosCriticos(cambios);
      }

      // Cargar actividad por usuario
      const actividadRes = await fetch(ENDPOINTS.AUDITORIA_ACTIVIDAD_USUARIO, {
        method: "GET",
        ...withSession(),
      });
      if (actividadRes.ok) {
        const actividad = await actividadRes.json();
        setActividadUsuario(actividad);
      }

      // Cargar evidencias invalidadas
      const evidenciasRes = await fetch(ENDPOINTS.AUDITORIA_EVIDENCIAS_INVALIDADAS, {
        method: "GET",
        ...withSession(),
      });
      if (evidenciasRes.ok) {
        const evidencias = await evidenciasRes.json();
        setEvidenciasInvalidadas(evidencias);
      }
    } catch (error) {
      console.error("Error al cargar datos de auditoría:", error);
      toast.error("Error al cargar información de auditoría");
    } finally {
      setLoading(false);
    }
  };

  return (
    <RoleGuard allow={["ADMIN"]}>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Dashboard de Auditoría
          </h1>
          <div className="flex gap-2">
            <Link
              href="/auditor/logs"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
            >
              Ver Logs
            </Link>
          </div>
        </div>

        {/* Últimos Cambios Críticos */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
            Últimos Cambios Críticos
          </h2>
          {loading ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
            </div>
          ) : cambiosCriticos.length > 0 ? (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {cambiosCriticos.map((cambio: any) => (
                <div
                  key={cambio.id}
                  className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-gray-900 dark:text-white">
                      {cambio.accion}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {new Date(cambio.ts).toLocaleString('es-CL')}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    <p><strong>Usuario:</strong> {cambio.usuario_nombre || "Sistema"}</p>
                    <p><strong>Objeto:</strong> {cambio.objeto_tipo} - {cambio.objeto_id}</p>
                    {cambio.payload && Object.keys(cambio.payload).length > 0 && (
                      <p className="mt-1 text-xs">
                        <strong>Detalles:</strong> {JSON.stringify(cambio.payload)}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 dark:text-gray-400">No hay cambios críticos registrados.</p>
          )}
        </div>

        {/* Actividad por Usuario */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
            Actividad por Usuario (Últimos 30 días)
          </h2>
          {loading ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
            </div>
          ) : actividadUsuario.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Usuario
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Rol
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Total Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {actividadUsuario.map((item: any) => (
                    <tr key={item.usuario_id}>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {item.nombre_completo}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                        {item.rol}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                        {item.total_acciones}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500 dark:text-gray-400">No hay actividad registrada.</p>
          )}
        </div>

        {/* Evidencias Invalidadas */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
            Evidencias Marcadas como Inválidas
          </h2>
          {loading ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
            </div>
          ) : evidenciasInvalidadas.length > 0 ? (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {evidenciasInvalidadas.map((evidencia: any) => (
                <div
                  key={evidencia.id}
                  className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-gray-900 dark:text-white">
                      Evidencia #{evidencia.id.substring(0, 8)}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {evidencia.invalidado_en 
                        ? new Date(evidencia.invalidado_en).toLocaleString('es-CL')
                        : "Sin fecha"}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    <p><strong>Invalidada por:</strong> {evidencia.invalidado_por?.get_full_name || "N/A"}</p>
                    <p><strong>Motivo:</strong> {evidencia.motivo_invalidacion || "Sin motivo especificado"}</p>
                    {evidencia.ot && (
                      <Link
                        href={`/workorders/${evidencia.ot}`}
                        className="text-blue-600 hover:text-blue-700 dark:text-blue-400 mt-2 inline-block"
                      >
                        Ver OT #{typeof evidencia.ot === 'string' ? evidencia.ot.substring(0, 8) : evidencia.ot}
                      </Link>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 dark:text-gray-400">No hay evidencias invalidadas.</p>
          )}
        </div>
      </div>
    </RoleGuard>
  );
}

