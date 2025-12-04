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
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

/**
 * Analizador de OTs para Supervisor Zonal.
 * 
 * Muestra:
 * - Tabla con todas las OTs de la zona
 * - Filtros múltiples (taller, mecánico, fechas, tipo de OT)
 * - Información detallada de cada OT
 * 
 * Permisos:
 * - Solo SUPERVISOR puede acceder
 */
export default function SupervisorAnalizadorPage() {
  const router = useRouter();
  const toast = useToast();
  const { hasRole } = useAuth();

  const [ots, setOts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtros, setFiltros] = useState({
    estado: "",
    tipo: "",
    prioridad: "",
    fecha_inicio: "",
    fecha_fin: "",
  });

  useEffect(() => {
    cargarOTs();
  }, [filtros]);

  const cargarOTs = async () => {
    setLoading(true);
    try {
      let url = ENDPOINTS.WORK_ORDERS;
      const params = new URLSearchParams();
      
      if (filtros.estado) params.append("estado", filtros.estado);
      if (filtros.tipo) params.append("tipo", filtros.tipo);
      if (filtros.prioridad) params.append("prioridad", filtros.prioridad);
      if (filtros.fecha_inicio) params.append("apertura__gte", filtros.fecha_inicio);
      if (filtros.fecha_fin) params.append("apertura__lte", filtros.fecha_fin);

      if (params.toString()) {
        url += `?${params.toString()}`;
      }

      const response = await fetch(url, {
        method: "GET",
        ...withSession(),
      });

      if (!response.ok) {
        // Intentar obtener mensaje de error del backend
        let errorMessage = "Error al cargar órdenes de trabajo";
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch {
          // Si no se puede parsear, usar mensaje genérico
          if (response.status === 401) {
            errorMessage = "No autorizado. Por favor, inicia sesión nuevamente.";
          } else if (response.status === 403) {
            errorMessage = "No tienes permisos para ver estas órdenes de trabajo.";
          } else if (response.status === 404) {
            errorMessage = "No se encontraron órdenes de trabajo.";
          } else if (response.status >= 500) {
            errorMessage = "Error del servidor. Por favor, intenta más tarde.";
          }
        }
        toast.error(errorMessage);
        setOts([]);
        setLoading(false);
        return;
      }

      const text = await response.text();
      if (!text || text.trim() === "") {
        setOts([]);
        setLoading(false);
        return;
      }

      let data;
      try {
        data = JSON.parse(text);
      } catch (e) {
        console.error("Error al parsear respuesta:", text);
        toast.error("Error al procesar la respuesta del servidor");
        setOts([]);
        setLoading(false);
        return;
      }

      setOts(data.results || data || []);
    } catch (error: any) {
      console.error("Error al cargar OTs:", error);
      toast.error(error?.message || "Error al cargar órdenes de trabajo");
      setOts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleFiltroChange = (campo: string, valor: string) => {
    setFiltros((prev) => ({ ...prev, [campo]: valor }));
  };

  // Calcular estadísticas para gráficos
  const estadisticasPorEstado = ots.reduce((acc: any, ot: any) => {
    const estado = ot.estado || "SIN_ESTADO";
    acc[estado] = (acc[estado] || 0) + 1;
    return acc;
  }, {});

  const datosPorEstado = Object.entries(estadisticasPorEstado).map(([estado, cantidad]) => ({
    estado,
    cantidad,
  }));

  const estadisticasPorTipo = ots.reduce((acc: any, ot: any) => {
    const tipo = ot.tipo || "SIN_TIPO";
    acc[tipo] = (acc[tipo] || 0) + 1;
    return acc;
  }, {});

  const datosPorTipo = Object.entries(estadisticasPorTipo).map(([tipo, cantidad]) => ({
    tipo,
    cantidad,
  }));

  const estadisticasPorPrioridad = ots.reduce((acc: any, ot: any) => {
    const prioridad = ot.prioridad || "SIN_PRIORIDAD";
    acc[prioridad] = (acc[prioridad] || 0) + 1;
    return acc;
  }, {});

  const datosPorPrioridad = Object.entries(estadisticasPorPrioridad).map(([prioridad, cantidad]) => ({
    prioridad,
    cantidad,
  }));

  const COLORS = ['#003DA5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

  return (
    <RoleGuard allow={["SUPERVISOR", "ADMIN"]}>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Analizador de OTs
          </h1>
          <Link
            href="/supervisor/dashboard"
            className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
          >
            ← Volver
          </Link>
        </div>

        {/* Filtros Múltiples */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            Filtros
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                Estado
              </label>
              <select
                value={filtros.estado}
                onChange={(e) => handleFiltroChange("estado", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">Todos</option>
                <option value="ABIERTA">Abierta</option>
                <option value="EN_EJECUCION">En Ejecución</option>
                <option value="EN_PAUSA">En Pausa</option>
                <option value="EN_QA">En QA</option>
                <option value="CERRADA">Cerrada</option>
              </select>
            </div>
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                Tipo
              </label>
              <select
                value={filtros.tipo}
                onChange={(e) => handleFiltroChange("tipo", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">Todos</option>
                <option value="MANTENCION">Mantención</option>
                <option value="REPARACION">Reparación</option>
              </select>
            </div>
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                Prioridad
              </label>
              <select
                value={filtros.prioridad}
                onChange={(e) => handleFiltroChange("prioridad", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">Todas</option>
                <option value="ALTA">Alta</option>
                <option value="MEDIA">Media</option>
                <option value="BAJA">Baja</option>
              </select>
            </div>
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                Fecha Inicio
              </label>
              <input
                type="date"
                value={filtros.fecha_inicio}
                onChange={(e) => handleFiltroChange("fecha_inicio", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                Fecha Fin
              </label>
              <input
                type="date"
                value={filtros.fecha_fin}
                onChange={(e) => handleFiltroChange("fecha_fin", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
          </div>
          <div className="mt-4">
            <button
              onClick={() => {
                setFiltros({ estado: "", tipo: "", prioridad: "", fecha_inicio: "", fecha_fin: "" });
                cargarOTs();
              }}
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
            >
              Limpiar Filtros
            </button>
          </div>
        </div>

        {/* Gráficos de Análisis */}
        {ots.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Gráfico de OTs por Estado */}
            {datosPorEstado.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                  Distribución por Estado
                </h2>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={datosPorEstado}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-gray-300 dark:stroke-gray-600" />
                    <XAxis 
                      dataKey="estado" 
                      className="text-gray-600 dark:text-gray-400"
                      tick={{ fill: 'currentColor' }}
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis 
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
                      name="Cantidad"
                      radius={[8, 8, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Gráfico de OTs por Tipo */}
            {datosPorTipo.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                  Distribución por Tipo
                </h2>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={datosPorTipo}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ tipo, cantidad, percent }) => `${tipo}: ${cantidad} (${(percent * 100).toFixed(0)}%)`}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="cantidad"
                      nameKey="tipo"
                    >
                      {datosPorTipo.map((entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px'
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Gráfico de OTs por Prioridad */}
            {datosPorPrioridad.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 lg:col-span-2">
                <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                  Distribución por Prioridad
                </h2>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={datosPorPrioridad}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-gray-300 dark:stroke-gray-600" />
                    <XAxis 
                      dataKey="prioridad" 
                      className="text-gray-600 dark:text-gray-400"
                      tick={{ fill: 'currentColor' }}
                    />
                    <YAxis 
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
                      fill="#10b981"
                      name="Cantidad"
                      radius={[8, 8, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        )}

        {/* Tabla de OTs */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            {loading ? (
              <div className="p-6 text-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
                <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando OTs...</p>
              </div>
            ) : ots.length === 0 ? (
              <div className="p-6 text-center text-gray-500 dark:text-gray-400">
                No hay órdenes de trabajo que coincidan con los filtros.
              </div>
            ) : (
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                      OT
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                      Taller
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                      Estado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                      Tiempo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                      Tipo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {ots.map((ot) => (
                    <tr key={ot.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                        #{ot.id.slice(0, 8)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {ot.zona || "N/A"}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded ${
                            ot.estado === "ABIERTA"
                              ? "bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300"
                              : ot.estado === "EN_EJECUCION"
                              ? "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300"
                              : "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300"
                          }`}
                        >
                          {ot.estado}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {ot.tiempo_display !== null && ot.tiempo_display !== undefined 
                          ? `${ot.tiempo_display} días` 
                          : ot.tiempo_total_reparacion 
                            ? `${ot.tiempo_total_reparacion} días` 
                            : "N/A"}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {ot.tipo || "N/A"}
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
            )}
          </div>
        </div>
      </div>
    </RoleGuard>
  );
}

