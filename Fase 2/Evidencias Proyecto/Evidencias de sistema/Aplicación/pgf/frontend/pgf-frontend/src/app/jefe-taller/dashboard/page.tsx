"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";
import RoleGuard from "@/components/RoleGuard";
import Link from "next/link";
import { ENDPOINTS } from "@/lib/constants";
import { withSession } from "@/lib/api.client";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

/**
 * Dashboard del Taller para Jefe de Taller.
 * 
 * Muestra:
 * - KPIs: OTs abiertas, Mecánicos activos, Promedio de ejecución, OTs atrasadas
 * - Gráfico de carga por mecánico
 * - Tabla de OTs del día
 * 
 * Permisos:
 * - Solo JEFE_TALLER puede acceder
 */
export default function JefeTallerDashboardPage() {
  const router = useRouter();
  const toast = useToast();
  const { hasRole } = useAuth();

  const [kpis, setKpis] = useState<any>({});
  const [otsHoy, setOtsHoy] = useState<any[]>([]);
  const [mecanicosCarga, setMecanicosCarga] = useState<any[]>([]);
  const [reporteJefeTaller, setReporteJefeTaller] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    cargarDatos();
    // Refrescar cada 30 segundos para mantener datos actualizados
    const interval = setInterval(() => {
      cargarDatos();
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const cargarDatos = async (forceRefresh = false) => {
    setLoading(true);
    try {
      // Cargar dashboard ejecutivo (tiene los KPIs que necesitamos)
      // Agregar parámetro refresh=true para invalidar caché si se solicita
      const url = forceRefresh 
        ? "/api/proxy/reports/dashboard-ejecutivo/?refresh=true"
        : "/api/proxy/reports/dashboard-ejecutivo/";
      const dashboardResponse = await fetch(url, {
        method: "GET",
        ...withSession(),
      });

      if (dashboardResponse.ok) {
        const dashboardData = await dashboardResponse.json();
        setKpis(dashboardData.kpis || {});
        setMecanicosCarga(dashboardData.mecanicos_carga || []);
      } else {
        const errorText = await dashboardResponse.text();
        let errorMessage = "Error al cargar KPIs del dashboard";
        try {
          const errorData = JSON.parse(errorText);
          errorMessage = errorData.detail || errorMessage;
        } catch {
          errorMessage = errorText || errorMessage;
        }
        console.error("Error al cargar dashboard:", errorMessage);
        toast.error(errorMessage);
      }

      // Cargar OTs del día
      const hoy = new Date().toISOString().split("T")[0];
      const otsResponse = await fetch(`${ENDPOINTS.WORK_ORDERS}?apertura__date=${hoy}`, {
        method: "GET",
        ...withSession(),
      });

      if (otsResponse.ok) {
        const otsData = await otsResponse.json();
        setOtsHoy(otsData.results || otsData || []);
      } else {
        console.error("Error al cargar OTs del día:", otsResponse.status, otsResponse.statusText);
      }

      // Cargar reporte específico de Jefe de Taller
      const reporteResponse = await fetch(forceRefresh 
        ? "/api/proxy/reports/dashboard-jefe-taller/?refresh=true"
        : "/api/proxy/reports/dashboard-jefe-taller/", {
        method: "GET",
        ...withSession(),
      });

      if (reporteResponse.ok) {
        const reporteData = await reporteResponse.json();
        setReporteJefeTaller(reporteData);
      } else {
        console.error("Error al cargar reporte de jefe de taller:", reporteResponse.status);
      }
    } catch (error) {
      console.error("Error al cargar datos:", error);
      toast.error("Error al cargar información del dashboard");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <RoleGuard allow={["JEFE_TALLER", "ADMIN"]}>
        <div className="p-6 flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando dashboard...</p>
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
            Dashboard del Taller
          </h1>
          <div className="flex gap-2">
            <button
              onClick={() => cargarDatos(true)}
              disabled={loading}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              title="Refrescar datos"
            >
              {loading ? "🔄 Cargando..." : "🔄 Refrescar"}
            </button>
            <Link
              href="/workorders/create"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
            >
              Crear OT
            </Link>
            <Link
              href="/jefe-taller/gestor"
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
            >
              Gestor de OTs
            </Link>
          </div>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
              OTs Abiertas
            </h3>
            <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">
              {kpis.ot_abiertas || 0}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
              OTs en Ejecución
            </h3>
            <p className="text-3xl font-bold text-yellow-600 dark:text-yellow-400">
              {kpis.ot_en_ejecucion || 0}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
              OTs en Pausa
            </h3>
            <p className="text-3xl font-bold text-orange-600 dark:text-orange-400">
              {kpis.ot_en_pausa || 0}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
              OTs Cerradas Hoy
            </h3>
            <p className="text-3xl font-bold text-green-600 dark:text-green-400">
              {kpis.ot_cerradas_hoy || 0}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
              OTs Atrasadas
            </h3>
            <p className="text-3xl font-bold text-red-600 dark:text-red-400">
              {reporteJefeTaller?.total_atrasadas || kpis.ot_atrasadas || 0}
            </p>
          </div>
        </div>

        {/* OTs Atrasadas */}
        {reporteJefeTaller && reporteJefeTaller.ot_atrasadas && reporteJefeTaller.ot_atrasadas.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              OTs Atrasadas ({reporteJefeTaller.total_atrasadas})
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">OT</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Patente</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Mecánico</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Días Atraso</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Acciones</th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {reporteJefeTaller.ot_atrasadas.map((ot: any) => (
                    <tr key={ot.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                        #{ot.id.slice(0, 8)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {ot.patente}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {ot.mecanico}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600 dark:text-red-400 font-bold">
                        {ot.dias_atraso} días
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <Link
                          href={`/workorders/${ot.id}`}
                          className="text-blue-600 hover:text-blue-900 dark:text-blue-400"
                        >
                          Ver
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Información de Guardias */}
        {kpis.guardias && kpis.guardias.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              Ingresos Registrados Hoy por Guardia
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {kpis.guardias.map((guardia: any) => (
                <div key={guardia.id} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Guardia</p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white">{guardia.nombre}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">@{guardia.username}</p>
                  <p className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-2">
                    {guardia.ingresos_hoy} ingresos
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Gráfico de Carga por Mecánico */}
        {mecanicosCarga.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              Carga de Trabajo por Mecánico
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart 
                data={mecanicosCarga.map((m: any) => ({
                  nombre: m.mecanico_nombre || m.nombre || "N/A",
                  cantidad: m.total_ots || 0
                }))}
                layout="vertical"
              >
                <CartesianGrid strokeDasharray="3 3" className="stroke-gray-300 dark:stroke-gray-600" />
                <XAxis 
                  type="number"
                  className="text-gray-600 dark:text-gray-400"
                  tick={{ fill: 'currentColor' }}
                />
                <YAxis 
                  dataKey="nombre" 
                  type="category"
                  width={120}
                  className="text-gray-600 dark:text-gray-400"
                  tick={{ fill: 'currentColor' }}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px'
                  }}
                />
                <Legend />
                <Bar 
                  dataKey="cantidad" 
                  fill="#003DA5"
                  name="OTs Activas"
                  radius={[0, 8, 8, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Historial por Vehículo */}
        {reporteJefeTaller && reporteJefeTaller.historial_por_vehiculo && reporteJefeTaller.historial_por_vehiculo.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              Historial de OTs por Vehículo (Últimos 30 días)
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Patente</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Marca/Modelo</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Total OTs</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Cerradas</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Activas</th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {reporteJefeTaller.historial_por_vehiculo.map((v: any, idx: number) => (
                    <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                        {v.patente}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {v.marca} {v.modelo}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {v.total_ots}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600 dark:text-green-400">
                        {v.ot_cerradas}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-yellow-600 dark:text-yellow-400">
                        {v.ot_activas}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Historial por Mecánico */}
        {reporteJefeTaller && reporteJefeTaller.historial_por_mecanico && reporteJefeTaller.historial_por_mecanico.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              Historial de OTs por Mecánico (Últimos 30 días)
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Mecánico</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Total OTs</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Cerradas</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Activas</th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {reporteJefeTaller.historial_por_mecanico.map((m: any) => (
                    <tr key={m.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                        {m.nombre}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {m.total_ots}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600 dark:text-green-400">
                        {m.ot_cerradas}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-yellow-600 dark:text-yellow-400">
                        {m.ot_activas}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tabla de OTs del Día */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              OTs del Día
            </h2>
          </div>
          <div className="overflow-x-auto">
            {otsHoy.length > 0 ? (
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                      OT
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                      Patente
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                      Estado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                      Mecánico
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                      Prioridad
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {otsHoy.map((ot) => (
                    <tr key={ot.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                        #{ot.id.slice(0, 8)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {ot.vehiculo_patente || ot.vehiculo?.patente}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded ${
                            ot.estado === "ABIERTA"
                              ? "bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300"
                              : ot.estado === "EN_EJECUCION"
                              ? "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300"
                              : "bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300"
                          }`}
                        >
                          {ot.estado}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {ot.mecanico_nombre || "Sin asignar"}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {ot.prioridad || "MEDIA"}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <Link
                          href={`/workorders/${ot.id}`}
                          className="text-blue-600 hover:text-blue-900 dark:text-blue-400"
                        >
                          Ver
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-6 text-center text-gray-500 dark:text-gray-400">
                No hay OTs creadas hoy.
              </div>
            )}
          </div>
        </div>
      </div>
    </RoleGuard>
  );
}

