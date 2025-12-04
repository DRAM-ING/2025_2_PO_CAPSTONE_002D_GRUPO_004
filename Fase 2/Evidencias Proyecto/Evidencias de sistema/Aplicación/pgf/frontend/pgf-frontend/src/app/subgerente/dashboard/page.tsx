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
 * Dashboard Nacional para Subgerente de Flota Nacional.
 * 
 * Muestra:
 * - OTs por región
 * - SLA nacional
 * - Ranking de talleres
 * - Tendencias históricas
 * - Flota operativa vs no operativa
 * 
 * Permisos:
 * - Solo EJECUTIVO, ADMIN pueden acceder (Subgerente usa rol EJECUTIVO)
 */
export default function SubgerenteDashboardPage() {
  const router = useRouter();
  const toast = useToast();
  const { hasRole } = useAuth();

  const [kpis, setKpis] = useState<any>({});
  const [reporteSubgerente, setReporteSubgerente] = useState<any>(null);
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
      const dashboardResponse = await fetch(forceRefresh 
        ? "/api/proxy/reports/dashboard-ejecutivo/?refresh=true"
        : "/api/proxy/reports/dashboard-ejecutivo/", {
        method: "GET",
        ...withSession(),
      });

      if (dashboardResponse.ok) {
        const dashboardData = await dashboardResponse.json();
        setKpis(dashboardData.kpis || {});
      }

      // Cargar reporte específico de Subgerente
      const reporteResponse = await fetch(forceRefresh 
        ? "/api/proxy/reports/dashboard-subgerente/?refresh=true"
        : "/api/proxy/reports/dashboard-subgerente/", {
        method: "GET",
        ...withSession(),
      });

      if (reporteResponse.ok) {
        const reporteData = await reporteResponse.json();
        setReporteSubgerente(reporteData);
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
      <RoleGuard allow={["EJECUTIVO", "ADMIN"]}>
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
    <RoleGuard allow={["EJECUTIVO", "ADMIN"]}>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Dashboard Nacional
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
              href="/subgerente/analisis"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
            >
              Análisis Estratégico
            </Link>
            <Link
              href="/reports"
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
            >
              Reportes
            </Link>
          </div>
        </div>

        {/* KPIs Nacionales */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
              OTs Mensuales
            </h3>
            <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">
              {reporteSubgerente?.kpis?.ot_mensuales || 0}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
              OTs Cerradas (Mes)
            </h3>
            <p className="text-3xl font-bold text-green-600 dark:text-green-400">
              {reporteSubgerente?.kpis?.ot_cerradas_mes || 0}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
              Tiempo Reparación Promedio
            </h3>
            <p className="text-3xl font-bold text-teal-600 dark:text-teal-400">
              {reporteSubgerente?.kpis?.tiempo_reparacion_promedio_horas || "N/A"}h
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
              Disponibilidad Flota
            </h3>
            <p className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
              {reporteSubgerente?.kpis?.disponibilidad_flota || "N/A"}%
            </p>
          </div>
        </div>

        {/* Tendencias Semanales */}
        {reporteSubgerente && reporteSubgerente.tendencias_semanales && reporteSubgerente.tendencias_semanales.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              Tendencias Semanales (Último Mes)
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Semana</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Período</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">OT Creadas</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">OT Cerradas</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Eficiencia</th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {reporteSubgerente.tendencias_semanales.map((semana: any, idx: number) => {
                    const eficiencia = semana.ot_creadas > 0 
                      ? Math.round((semana.ot_cerradas / semana.ot_creadas) * 100)
                      : 0;
                    return (
                      <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                          {semana.semana}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                          {new Date(semana.fecha_inicio).toLocaleDateString()} - {new Date(semana.fecha_fin).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                          {semana.ot_creadas}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600 dark:text-green-400">
                          {semana.ot_cerradas}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                          {eficiencia}%
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </RoleGuard>
  );
}

