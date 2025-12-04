"use client";

import { useState, useEffect } from "react";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";
import RoleGuard from "@/components/RoleGuard";
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

export default function ReportsPage() {
  const toast = useToast();
  const { hasRole } = useAuth();
  const [fechaInicio, setFechaInicio] = useState("");
  const [fechaFin, setFechaFin] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(false);
  const [reportData, setReportData] = useState<any>(null);
  const [tipoReporte, setTipoReporte] = useState<"diario" | "semanal" | "mensual" | null>(null);

  const canAccess = hasRole(["EJECUTIVO", "ADMIN", "JEFE_TALLER", "SUPERVISOR", "COORDINADOR_ZONA", "SUBGERENTE_NACIONAL"]);

  // Cargar datos del reporte
  const cargarDatosReporte = async (tipo: "diario" | "semanal" | "mensual") => {
    if (!canAccess) {
      toast.error("No tienes permisos para acceder a reportes");
      return;
    }

    // Validar fechas según el tipo
    if (tipo === "diario" && !fechaInicio) {
      toast.error("Por favor selecciona una fecha para el reporte diario");
      return;
    }

    if ((tipo === "semanal" || tipo === "mensual") && (!fechaInicio || !fechaFin)) {
      // Establecer fechas por defecto si no están configuradas
      setDefaultDates(tipo);
      // Esperar un momento para que se actualicen las fechas
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    setLoadingData(true);
    setTipoReporte(tipo);

    try {
      // Usar el endpoint de dashboard ejecutivo para mostrar los datos
      const r = await fetch("/api/proxy/reports/dashboard-ejecutivo/", {
        credentials: "include",
      });

      if (!r.ok) {
        const error = await r.json().catch(() => ({ detail: "Error al cargar datos del reporte" }));
        toast.error(error.detail || "Error al cargar datos del reporte");
        return;
      }

      const text = await r.text();
      if (!text || text.trim() === "") {
        toast.error("No se recibieron datos del reporte");
        return;
      }

      const data = JSON.parse(text);
      setReportData(data);
      toast.success("Reporte cargado correctamente");
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al cargar datos del reporte");
    } finally {
      setLoadingData(false);
    }
  };

  // Exportar a PDF
  const exportarPDF = async () => {
    if (!tipoReporte) {
      toast.error("Primero debes cargar un reporte");
      return;
    }

    setLoading(true);

    try {
      let url = `/api/proxy/reports/pdf/?tipo=${tipoReporte}`;
      
      // Para reporte diario, usar fechaInicio
      if (tipoReporte === "diario" && fechaInicio) {
        url += `&fecha_inicio=${fechaInicio}`;
      }
      
      // Para reportes semanal y mensual, usar ambas fechas
      if ((tipoReporte === "semanal" || tipoReporte === "mensual")) {
        if (fechaInicio) {
          url += `&fecha_inicio=${fechaInicio}`;
        }
        if (fechaFin) {
          url += `&fecha_fin=${fechaFin}`;
        }
      }

      const r = await fetch(url, {
        credentials: "include",
      });

      if (!r.ok) {
        const errorText = await r.text();
        let errorMessage = "Error al generar PDF";
        try {
          const errorJson = JSON.parse(errorText);
          errorMessage = errorJson.detail || errorMessage;
        } catch {
          errorMessage = errorText || errorMessage;
        }
        toast.error(errorMessage);
        return;
      }

      // Verificar que la respuesta sea un PDF
      const contentType = r.headers.get("content-type");
      if (!contentType || !contentType.includes("application/pdf")) {
        toast.error("La respuesta no es un PDF válido");
        return;
      }

      // Descargar PDF
      const blob = await r.blob();
      
      // Verificar que el blob no esté vacío
      if (blob.size === 0) {
        toast.error("El PDF generado está vacío");
        return;
      }
      
      const urlBlob = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = urlBlob;
      const fechaStr = fechaInicio || new Date().toISOString().split('T')[0];
      a.download = `reporte_${tipoReporte}_${fechaStr}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(urlBlob);

      toast.success("PDF descargado correctamente");
    } catch (error) {
      console.error("Error al exportar PDF:", error);
      toast.error("Error al descargar PDF: " + (error instanceof Error ? error.message : "Error desconocido"));
    } finally {
      setLoading(false);
    }
  };

  // Establecer fechas por defecto
  const setDefaultDates = (tipo: "semanal" | "mensual") => {
    const hoy = new Date();
    const fin = hoy.toISOString().split('T')[0];
    
    if (tipo === "semanal") {
      const inicio = new Date(hoy);
      inicio.setDate(hoy.getDate() - 7);
      setFechaInicio(inicio.toISOString().split('T')[0]);
    } else {
      const inicio = new Date(hoy);
      inicio.setMonth(hoy.getMonth() - 1);
      setFechaInicio(inicio.toISOString().split('T')[0]);
    }
    
    setFechaFin(fin);
  };

  return (
    <RoleGuard allow={["EJECUTIVO", "ADMIN", "JEFE_TALLER", "SUPERVISOR", "COORDINADOR_ZONA", "SPONSOR"]}>
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Reportes</h1>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Reporte Diario */}
          <div className={`bg-white dark:bg-gray-800 shadow rounded-lg p-6 border-2 ${
            tipoReporte === "diario" ? "border-blue-500" : "border-transparent"
          }`}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Reporte Diario</h2>
              {tipoReporte === "diario" && (
                <span className="px-2 py-1 bg-blue-500 text-white text-xs rounded">Seleccionado</span>
              )}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Visualiza y exporta el reporte del día seleccionado.
            </p>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Fecha
              </label>
              <input
                type="date"
                value={fechaInicio}
                onChange={(e) => setFechaInicio(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
            <div className="space-y-2">
              <button
                onClick={() => {
                  const hoy = new Date().toISOString().split('T')[0];
                  setFechaInicio(hoy);
                }}
                className="w-full px-3 py-1 text-sm bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors"
              >
                Usar Hoy
              </button>
              <button
                onClick={() => cargarDatosReporte("diario")}
                disabled={loadingData || !fechaInicio}
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loadingData && tipoReporte === "diario" ? "Cargando..." : "Ver Reporte"}
              </button>
            </div>
          </div>

          {/* Reporte Semanal */}
          <div className={`bg-white dark:bg-gray-800 shadow rounded-lg p-6 border-2 ${
            tipoReporte === "semanal" ? "border-blue-500" : "border-transparent"
          }`}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Reporte Semanal</h2>
              {tipoReporte === "semanal" && (
                <span className="px-2 py-1 bg-blue-500 text-white text-xs rounded">Seleccionado</span>
              )}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Visualiza y exporta el reporte de la última semana.
            </p>
            <div className="mb-4 space-y-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Fecha Inicio
                </label>
                <input
                  type="date"
                  value={fechaInicio}
                  onChange={(e) => setFechaInicio(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Fecha Fin
                </label>
                <input
                  type="date"
                  value={fechaFin}
                  onChange={(e) => setFechaFin(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <button
                onClick={() => setDefaultDates("semanal")}
                className="w-full px-3 py-1 text-sm bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors"
              >
                Últimos 7 días
              </button>
            </div>
            <button
              onClick={() => cargarDatosReporte("semanal")}
              disabled={loadingData}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loadingData && tipoReporte === "semanal" ? "Cargando..." : "Ver Reporte"}
            </button>
          </div>

          {/* Reporte Mensual */}
          <div className={`bg-white dark:bg-gray-800 shadow rounded-lg p-6 border-2 ${
            tipoReporte === "mensual" ? "border-blue-500" : "border-transparent"
          }`}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Reporte Mensual</h2>
              {tipoReporte === "mensual" && (
                <span className="px-2 py-1 bg-blue-500 text-white text-xs rounded">Seleccionado</span>
              )}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Visualiza y exporta el reporte del último mes.
            </p>
            <div className="mb-4 space-y-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Fecha Inicio
                </label>
                <input
                  type="date"
                  value={fechaInicio}
                  onChange={(e) => setFechaInicio(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Fecha Fin
                </label>
                <input
                  type="date"
                  value={fechaFin}
                  onChange={(e) => setFechaFin(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <button
                onClick={() => setDefaultDates("mensual")}
                className="w-full px-3 py-1 text-sm bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors"
              >
                Últimos 30 días
              </button>
            </div>
            <button
              onClick={() => cargarDatosReporte("mensual")}
              disabled={loadingData}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loadingData && tipoReporte === "mensual" ? "Cargando..." : "Ver Reporte"}
            </button>
          </div>
        </div>

        {/* Mostrar datos del reporte */}
        {reportData && (
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mt-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Reporte {tipoReporte === "diario" ? "Diario" : tipoReporte === "semanal" ? "Semanal" : "Mensual"}
              </h2>
              <button
                onClick={exportarPDF}
                disabled={loading}
                className="px-6 py-3 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90"
                style={{ backgroundColor: '#003DA5' }}
              >
                {loading ? "Generando PDF..." : "📄 Exportar a PDF"}
              </button>
            </div>

            {loadingData ? (
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
                <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando datos...</p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* KPIs */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <KpiCard title="OT Abiertas" value={reportData.kpis?.ot_abiertas || 0} color="bg-blue-500" />
                  <KpiCard title="OT en Ejecución" value={reportData.kpis?.ot_en_ejecucion || 0} color="bg-yellow-500" />
                  <KpiCard title="OT en Pausa" value={reportData.kpis?.ot_en_pausa || 0} color="bg-orange-500" />
                  <KpiCard title="OT en QA" value={reportData.kpis?.ot_en_qa || 0} color="bg-purple-500" />
                  <KpiCard title="OT Cerradas Hoy" value={reportData.kpis?.ot_cerradas_hoy || 0} color="bg-green-600" />
                  <KpiCard title="Vehículos en Taller" value={reportData.kpis?.vehiculos_en_taller || 0} color="bg-indigo-500" />
                  <KpiCard title="Productividad (7 días)" value={reportData.kpis?.productividad_7_dias || 0} color="bg-teal-500" />
                </div>

                {/* Últimas 5 OT */}
                {reportData.ultimas_5_ot && reportData.ultimas_5_ot.length > 0 && (
                  <section>
                    <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Últimas 5 Órdenes de Trabajo</h3>
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
                          {reportData.ultimas_5_ot.map((ot: any) => (
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
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </section>
                )}

                {/* Gráficos */}
                {reportData.graficos && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
                    {/* Gráfico de OT cerradas por día */}
                    {reportData.graficos.ot_cerradas_por_dia && reportData.graficos.ot_cerradas_por_dia.length > 0 && (
                      <section className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                        <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                          Productividad - OT Cerradas (Últimos 7 Días)
                        </h3>
                        <ResponsiveContainer width="100%" height={300}>
                          <LineChart data={reportData.graficos.ot_cerradas_por_dia}>
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
                    {reportData.graficos.ot_por_estado && reportData.graficos.ot_por_estado.length > 0 && (
                      <section className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                        <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                          Distribución de OT por Estado
                        </h3>
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart data={reportData.graficos.ot_por_estado}>
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
                    {reportData.graficos.mecanicos_productividad && reportData.graficos.mecanicos_productividad.length > 0 && (
                      <section className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 lg:col-span-2">
                        <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                          Productividad por Mecánico (Últimos 7 Días)
                        </h3>
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart data={reportData.graficos.mecanicos_productividad} layout="vertical">
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

                    {/* Gráfico de pausas más frecuentes */}
                    {reportData.pausas_frecuentes && reportData.pausas_frecuentes.length > 0 && (
                      <section className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                        <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                          Pausas Más Frecuentes
                        </h3>
                        <ResponsiveContainer width="100%" height={300}>
                          <PieChart>
                            <Pie
                              data={reportData.pausas_frecuentes}
                              cx="50%"
                              cy="50%"
                              labelLine={false}
                              label={({ motivo, cantidad, percent }) => `${motivo}: ${cantidad} (${(percent * 100).toFixed(0)}%)`}
                              outerRadius={100}
                              fill="#8884d8"
                              dataKey="cantidad"
                              nameKey="motivo"
                            >
                              {reportData.pausas_frecuentes.map((entry: any, index: number) => {
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
            )}
          </div>
        )}
      </div>
    </RoleGuard>
  );
}

function KpiCard({ title, value, color }: any) {
  return (
    <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg flex flex-col">
      <span className="text-gray-600 dark:text-gray-400 text-sm mb-2">{title}</span>
      <span className={`text-3xl font-bold ${color} text-white px-3 py-2 rounded`}>
        {value}
      </span>
    </div>
  );
}
