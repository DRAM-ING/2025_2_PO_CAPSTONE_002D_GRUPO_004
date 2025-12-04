"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/store/auth";
import RoleGuard from "@/components/RoleGuard";
import { useToast } from "@/components/ToastContainer";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
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

export default function DashboardEjecutivo() {
  const [kpis, setKpis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const toast = useToast();

  const load = async (forceRefresh = false) => {
    if (forceRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    try {
      const url = forceRefresh 
        ? "/api/proxy/reports/dashboard-ejecutivo/?refresh=true"
        : "/api/proxy/reports/dashboard-ejecutivo/";
      const r = await fetch(url, {
        credentials: "include",
      });

      if (!r.ok) {
        toast.error("Error al cargar el dashboard ejecutivo");
        return;
      }

      const text = await r.text();
      if (!text || text.trim() === "") {
        return;
      }

      const data = JSON.parse(text);
      setKpis(data);
      if (forceRefresh) {
        toast.success("Datos actualizados");
      }
    } catch (e) {
      console.error("Error:", e);
      toast.error("Error al cargar el dashboard ejecutivo");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    load();
    // Refrescar cada 30 segundos para mantener datos actualizados
    const interval = setInterval(() => {
      load();
    }, 30000);
    return () => clearInterval(interval);
  }, [toast]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando dashboard...</p>
        </div>
      </div>
    );
  }

  if (!kpis) {
    return <div className="p-6">No hay datos disponibles</div>;
  }

  const downloadDailyReport = async () => {
    const hoy = new Date().toISOString().split('T')[0];
    setLoading(true);
    
    try {
      const r = await fetch(`/api/proxy/reports/pdf/?tipo=diario&fecha_inicio=${hoy}`, {
        credentials: "include",
      });

      if (!r.ok) {
        const error = await r.json().catch(() => ({ detail: "Error al generar reporte" }));
        toast.error(error.detail || "Error al generar reporte");
        return;
      }

      // Descargar PDF
      const blob = await r.blob();
      const urlBlob = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = urlBlob;
      a.download = `reporte_diario_${hoy}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(urlBlob);

      toast.success("Reporte diario descargado correctamente");
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al descargar reporte");
    } finally {
      setLoading(false);
    }
  };

  return (
    <RoleGuard allow={["EJECUTIVO", "ADMIN", "SPONSOR", "JEFE_TALLER"]}>
      <div className="p-6 space-y-8">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard Ejecutivo</h1>
          <div className="flex gap-2">
            <button
              onClick={() => load(true)}
              disabled={refreshing || loading}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              title="Refrescar datos"
            >
              {refreshing ? "🔄 Actualizando..." : "🔄 Refrescar"}
            </button>
            {/* Botón de reporte diario para ADMIN, SPONSOR, JEFE_TALLER */}
            <button
              onClick={downloadDailyReport}
              disabled={loading}
              className="px-6 py-3 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90"
              style={{ backgroundColor: '#003DA5' }}
            >
              {loading ? "Generando..." : "📊 Reporte Diario"}
            </button>
          </div>
        </div>

        {/* Información de Guardias */}
        {kpis && kpis.guardias && kpis.guardias.length > 0 && (
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

        {/* KPIs principales */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <KpiCard title="OT Abiertas" value={kpis.kpis?.ot_abiertas || 0} color="bg-blue-500" />
          <KpiCard title="OT en Ejecución" value={kpis.kpis?.ot_en_ejecucion || 0} color="bg-yellow-500" />
          <KpiCard title="OT en Pausa" value={kpis.kpis?.ot_en_pausa || 0} color="bg-orange-500" />
          <KpiCard title="OT en QA" value={kpis.kpis?.ot_en_qa || 0} color="bg-purple-500" />
          <KpiCard title="OT Cerradas Hoy" value={kpis.kpis?.ot_cerradas_hoy || 0} color="bg-green-600" />
          <KpiCard title="Vehículos en Taller" value={kpis.kpis?.vehiculos_en_taller || 0} color="bg-indigo-500" />
          <KpiCard title="Productividad (7 días)" value={kpis.kpis?.productividad_7_dias || 0} color="bg-teal-500" />
        </div>

        {/* Últimas 5 OT */}
        <section className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Últimas 5 Órdenes de Trabajo</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="bg-gray-100 dark:bg-gray-700">
                  <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">ID</th>
                  <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Patente</th>
                  <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Estado</th>
                  <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Responsable</th>
                  <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Apertura</th>
                </tr>
              </thead>
              <tbody>
                {kpis.ultimas_5_ot?.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="p-4 text-center text-gray-500 dark:text-gray-400">
                      No hay órdenes de trabajo
                    </td>
                  </tr>
                ) : (
                  kpis.ultimas_5_ot?.map((ot: any) => (
                    <tr key={ot.id} className="border-t border-gray-200 dark:border-gray-700">
                      <td className="p-3 text-gray-900 dark:text-white">#{ot.id.substring(0, 8)}</td>
                      <td className="p-3 text-gray-700 dark:text-gray-300">{ot.patente}</td>
                      <td className="p-3">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          ot.estado === "ABIERTA" ? "bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-400" :
                          ot.estado === "EN_EJECUCION" ? "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-400" :
                          ot.estado === "EN_PAUSA" ? "bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-400" :
                          ot.estado === "EN_QA" ? "bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-400" :
                          "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400"
                        }`}>
                          {ot.estado}
                        </span>
                      </td>
                      <td className="p-3 text-gray-700 dark:text-gray-300">{ot.responsable || "Sin responsable"}</td>
                      <td className="p-3 text-gray-700 dark:text-gray-300">
                        {(() => {
                          const fechaApertura = ot.apertura || ot.fecha_apertura;
                          if (!fechaApertura) return "N/A";
                          try {
                            const fecha = new Date(fechaApertura);
                            if (isNaN(fecha.getTime())) return "N/A";
                            return fecha.toLocaleDateString('es-CL', {
                              year: 'numeric',
                              month: '2-digit',
                              day: '2-digit',
                              hour: '2-digit',
                              minute: '2-digit'
                            });
                          } catch (e) {
                            return "N/A";
                          }
                        })()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* Pausas más frecuentes */}
        {kpis.pausas_frecuentes && kpis.pausas_frecuentes.length > 0 && (
          <section className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Pausas Más Frecuentes</h2>
            <div className="space-y-2">
              {kpis.pausas_frecuentes.map((p: any, idx: number) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded">
                  <span className="text-gray-700 dark:text-gray-300">{p.motivo}</span>
                  <span className="font-semibold text-gray-900 dark:text-white">{p.cantidad} veces</span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Mecánicos con más carga */}
        {kpis.mecanicos_carga && kpis.mecanicos_carga.length > 0 && (
          <section className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Mecánicos con Más Carga de Trabajo</h2>
            <div className="space-y-2">
              {kpis.mecanicos_carga.map((m: any) => (
                <div key={m.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded">
                  <span className="text-gray-700 dark:text-gray-300">{m.nombre}</span>
                  <span className="font-semibold text-gray-900 dark:text-white">{m.total_ots} OT</span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Tiempos promedio */}
        {kpis.tiempos_promedio && (
          <section className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Tiempos Promedio por Estado</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(kpis.tiempos_promedio).map(([estado, tiempo]: [string, any]) => (
                <div key={estado} className="p-3 bg-gray-50 dark:bg-gray-700 rounded">
                  <span className="text-sm text-gray-600 dark:text-gray-400">{estado}:</span>
                  <span className="ml-2 font-semibold text-gray-900 dark:text-white">
                    {tiempo ? formatDuration(tiempo) : "N/A"}
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Gráficos */}
        {kpis.graficos && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Gráfico de OT cerradas por día (últimos 7 días) */}
            {kpis.graficos.ot_cerradas_por_dia && kpis.graficos.ot_cerradas_por_dia.length > 0 && (
              <section className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                  Productividad - OT Cerradas (Últimos 7 Días)
                </h2>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={kpis.graficos.ot_cerradas_por_dia}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-gray-300 dark:stroke-gray-600" />
                    <XAxis 
                      dataKey="dia" 
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
                    <Line 
                      type="monotone" 
                      dataKey="cantidad" 
                      stroke="#003DA5" 
                      strokeWidth={3}
                      name="OT Cerradas"
                      dot={{ fill: '#003DA5', r: 5 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </section>
            )}

            {/* Gráfico de OT por estado */}
            {kpis.graficos.ot_por_estado && kpis.graficos.ot_por_estado.length > 0 && (
              <section className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                  Distribución de OT por Estado
                </h2>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={kpis.graficos.ot_por_estado}>
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
              </section>
            )}

            {/* Gráfico de productividad por mecánico */}
            {kpis.graficos.mecanicos_productividad && kpis.graficos.mecanicos_productividad.length > 0 && (
              <section className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 lg:col-span-2">
                <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                  Productividad por Mecánico (Últimos 7 Días)
                </h2>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={kpis.graficos.mecanicos_productividad} layout="vertical">
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
                      dataKey="ot_cerradas" 
                      fill="#10b981"
                      name="OT Cerradas"
                      radius={[0, 8, 8, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </section>
            )}

            {/* Gráfico de pausas más frecuentes (Pie Chart) */}
            {kpis.pausas_frecuentes && kpis.pausas_frecuentes.length > 0 && (
              <section className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                  Pausas Más Frecuentes
                </h2>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={kpis.pausas_frecuentes}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ motivo, cantidad, percent }) => `${motivo}: ${cantidad} (${(percent * 100).toFixed(0)}%)`}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="cantidad"
                      nameKey="motivo"
                    >
                      {kpis.pausas_frecuentes.map((entry: any, index: number) => {
                        const colors = ['#003DA5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
                        return <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />;
                      })}
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
              </section>
            )}
          </div>
        )}
      </div>
    </RoleGuard>
  );
}

function KpiCard({ title, value, color }: any) {
  return (
    <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow flex flex-col">
      <span className="text-gray-600 dark:text-gray-400 text-sm mb-2">{title}</span>
      <span className={`text-4xl font-bold ${color} text-white px-4 py-2 rounded`}>
        {value}
      </span>
    </div>
  );
}

function formatDuration(durationStr: string): string {
  // Formatea duración desde string ISO
  try {
    const match = durationStr.match(/(\d+) days?, (\d+):(\d+):(\d+)/);
    if (match) {
      const days = parseInt(match[1]);
      const hours = parseInt(match[2]);
      const minutes = parseInt(match[3]);
      if (days > 0) {
        return `${days}d ${hours}h ${minutes}m`;
      }
      return `${hours}h ${minutes}m`;
    }
    return durationStr;
  } catch {
    return durationStr;
  }
}

