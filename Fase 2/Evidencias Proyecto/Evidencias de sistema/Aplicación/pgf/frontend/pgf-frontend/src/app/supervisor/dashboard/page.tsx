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
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

/**
 * Dashboard de Zona para Supervisor Zonal - Taller Santa Marta.
 * 
 * Muestra:
 * - KPIs principales (OT abiertas, cumplimiento SLA, productividad, vehículos en taller)
 * - Gráfico de cumplimiento SLA (últimos 7 días)
 * - Gráfico de productividad (OT cerradas por día)
 * 
 * Permisos:
 * - SUPERVISOR y ADMIN pueden acceder
 * 
 * Nota: Este dashboard muestra datos del taller Santa Marta (única sucursal).
 */
export default function SupervisorDashboardPage() {
  const router = useRouter();
  const toast = useToast();
  const { hasRole, user } = useAuth();

  const [kpis, setKpis] = useState<any>({});
  const [graficos, setGraficos] = useState<any>({});
  const [reporteSupervisor, setReporteSupervisor] = useState<any>(null);
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
        setGraficos(dashboardData.graficos || {});
      } else {
        // Si hay un error, mostrar mensaje específico
        const errorData = await dashboardResponse.json().catch(() => ({ detail: "Error desconocido" }));
        if (dashboardResponse.status === 403) {
          toast.error("No tiene permisos para ver el dashboard");
        } else {
          toast.error(errorData.detail || "Error al cargar información del dashboard");
        }
      }

      // Cargar reporte específico de Supervisor
      const reporteResponse = await fetch(forceRefresh 
        ? "/api/proxy/reports/dashboard-supervisor/?refresh=true"
        : "/api/proxy/reports/dashboard-supervisor/", {
        method: "GET",
        ...withSession(),
      });

      if (reporteResponse.ok) {
        const reporteData = await reporteResponse.json();
        setReporteSupervisor(reporteData);
      } else {
        console.error("Error al cargar reporte de supervisor:", reporteResponse.status);
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
      <RoleGuard allow={["SUPERVISOR", "ADMIN"]}>
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
    <RoleGuard allow={["SUPERVISOR", "ADMIN"]}>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Dashboard - Taller Santa Marta
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
              href="/supervisor/analizador"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
            >
              Analizador de OTs
            </Link>
            <Link
              href="/reports"
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
            >
              Reportes
            </Link>
          </div>
        </div>

        {/* KPIs Principales */}
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
              Cumplimiento SLA
            </h3>
            <p className="text-3xl font-bold text-green-600 dark:text-green-400">
              {kpis.sla_cumplimiento || "N/A"}%
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
              Productividad (7 días)
            </h3>
            <p className="text-3xl font-bold text-teal-600 dark:text-teal-400">
              {kpis.productividad_7_dias || 0}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
              Vehículos en Taller
            </h3>
            <p className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
              {kpis.vehiculos_en_taller || 0}
            </p>
          </div>
        </div>

        {/* Gráfico de Cumplimiento SLA */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
            Cumplimiento SLA - Últimos 7 días
          </h2>
          {graficos.cumplimiento_sla_por_dia && graficos.cumplimiento_sla_por_dia.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart
                data={graficos.cumplimiento_sla_por_dia}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="dia" 
                  tick={{ fill: '#6b7280' }}
                />
                <YAxis 
                  domain={[0, 100]}
                  tick={{ fill: '#6b7280' }}
                  label={{ value: 'Cumplimiento (%)', angle: -90, position: 'insideLeft', fill: '#6b7280' }}
                />
                <Tooltip 
                  formatter={(value: any) => [`${value}%`, 'Cumplimiento']}
                  labelFormatter={(label) => `Día: ${label}`}
                  contentStyle={{ backgroundColor: '#f9fafb', border: '1px solid #e5e7eb' }}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="cumplimiento" 
                  stroke="#10b981" 
                  strokeWidth={2}
                  name="Cumplimiento SLA (%)"
                  dot={{ fill: '#10b981', r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-gray-500 dark:text-gray-400 text-center py-8">
              <p>No hay datos de cumplimiento SLA disponibles para los últimos 7 días.</p>
            </div>
          )}
        </div>

        {/* Comparación entre Talleres */}
        {reporteSupervisor && reporteSupervisor.comparacion_talleres && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              Comparación entre Talleres
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {reporteSupervisor.comparacion_talleres.map((taller: any, idx: number) => (
                <div key={idx} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-3">{taller.nombre}</h3>
                  <div className="space-y-2">
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">OT Activas</p>
                      <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{taller.ot_activas}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">OT Cerradas (Mes)</p>
                      <p className="text-2xl font-bold text-green-600 dark:text-green-400">{taller.ot_cerradas_mes}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Cumplimiento SLA</p>
                      <p className="text-2xl font-bold text-teal-600 dark:text-teal-400">{taller.sla_cumplimiento}%</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tiempos Promedio */}
        {reporteSupervisor && reporteSupervisor.tiempos_promedio && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              Tiempos Promedio por Estado (Últimos 30 días)
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {Object.entries(reporteSupervisor.tiempos_promedio).map(([estado, horas]: [string, any]) => (
                <div key={estado} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">{estado}</p>
                  <p className="text-xl font-bold text-gray-900 dark:text-white">
                    {horas !== null ? `${horas}h` : "N/A"}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Carga de Trabajo */}
        {reporteSupervisor && reporteSupervisor.carga_trabajo && reporteSupervisor.carga_trabajo.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              Carga de Trabajo por Estado
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {reporteSupervisor.carga_trabajo.map((item: any, idx: number) => (
                <div key={idx} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">{item.estado}</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{item.cantidad}</p>
                </div>
              ))}
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

        {/* Productividad del Taller */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
            Productividad del Taller - Últimos 7 días
          </h2>
          {graficos.ot_cerradas_por_dia && graficos.ot_cerradas_por_dia.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart
                data={graficos.ot_cerradas_por_dia}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="dia" 
                  tick={{ fill: '#6b7280' }}
                />
                <YAxis 
                  tick={{ fill: '#6b7280' }}
                  label={{ value: 'OT Cerradas', angle: -90, position: 'insideLeft', fill: '#6b7280' }}
                />
                <Tooltip 
                  formatter={(value: any) => [value, 'OT Cerradas']}
                  labelFormatter={(label) => `Día: ${label}`}
                  contentStyle={{ backgroundColor: '#f9fafb', border: '1px solid #e5e7eb' }}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="cantidad" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  name="OT Cerradas"
                  dot={{ fill: '#3b82f6', r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-gray-500 dark:text-gray-400 text-center py-8">
              <p>No hay datos de productividad disponibles para los últimos 7 días.</p>
            </div>
          )}
        </div>
      </div>
    </RoleGuard>
  );
}

