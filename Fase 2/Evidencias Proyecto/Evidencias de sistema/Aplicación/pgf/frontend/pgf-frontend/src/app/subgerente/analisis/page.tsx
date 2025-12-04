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
 * Vista de Análisis Estratégico para Subgerente Nacional.
 * 
 * Muestra:
 * - Gráficos de líneas, barras, heatmap
 * - Filtros por año, zona, tipo de OT, taller
 * - Análisis comparativo
 * 
 * Permisos:
 * - Solo EJECUTIVO, ADMIN pueden acceder
 */
export default function SubgerenteAnalisisPage() {
  const router = useRouter();
  const toast = useToast();
  const { hasRole } = useAuth();

  const [filtros, setFiltros] = useState({
    año: new Date().getFullYear().toString(),
    zona: "",
    tipo_ot: "",
    taller: "",
  });

  return (
    <RoleGuard allow={["EJECUTIVO", "ADMIN"]}>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Análisis Estratégico
          </h1>
          <Link
            href="/subgerente/dashboard"
            className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
          >
            ← Volver
          </Link>
        </div>

        {/* Filtros */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            Filtros de Análisis
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                Año
              </label>
              <input
                type="number"
                value={filtros.año}
                onChange={(e) => setFiltros({ ...filtros, año: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                min="2020"
                max="2100"
              />
            </div>
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                Zona
              </label>
              <input
                type="text"
                value={filtros.zona}
                onChange={(e) => setFiltros({ ...filtros, zona: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Todas"
              />
            </div>
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                Tipo de OT
              </label>
              <select
                value={filtros.tipo_ot}
                onChange={(e) => setFiltros({ ...filtros, tipo_ot: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">Todos</option>
                <option value="MANTENCION">Mantención</option>
                <option value="REPARACION">Reparación</option>
                <option value="DIAGNOSTICO">Diagnóstico</option>
                <option value="OTRO">Otro</option>
              </select>
            </div>
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                Taller
              </label>
              <input
                type="text"
                value={filtros.taller}
                onChange={(e) => setFiltros({ ...filtros, taller: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Todos"
              />
            </div>
          </div>
        </div>

        {/* Gráficos */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              Gráfico de Líneas
            </h2>
            <div className="text-gray-500 dark:text-gray-400">
              <p>Evolución de OTs en el tiempo (en desarrollo).</p>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              Gráfico de Barras
            </h2>
            <div className="text-gray-500 dark:text-gray-400">
              <p>Comparativa por tipo de OT (en desarrollo).</p>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 lg:col-span-2">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              Heatmap
            </h2>
            <div className="text-gray-500 dark:text-gray-400">
              <p>Distribución de OTs por zona y tipo (en desarrollo).</p>
            </div>
          </div>
        </div>
      </div>
    </RoleGuard>
  );
}

