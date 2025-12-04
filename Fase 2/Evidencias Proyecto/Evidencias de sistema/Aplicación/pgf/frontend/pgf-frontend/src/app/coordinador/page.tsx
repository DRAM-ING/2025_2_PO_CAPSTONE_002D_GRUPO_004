"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";
import RoleGuard from "@/components/RoleGuard";
import Link from "next/link";

/**
 * Vista principal para Coordinador de Zona.
 * 
 * Muestra:
 * - Accesos rápidos a funcionalidades principales
 * - Resumen de OTs abiertas
 * - Enlaces a gestión de vehículos, documentos, reportes
 * 
 * Permisos:
 * - Solo COORDINADOR_ZONA, ADMIN pueden acceder
 */
export default function CoordinadorPage() {
  const router = useRouter();
  const toast = useToast();
  const { hasRole } = useAuth();

  return (
    <RoleGuard allow={["COORDINADOR_ZONA", "ADMIN"]}>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Panel de Coordinador de Zona
          </h1>
        </div>

        {/* Accesos Rápidos */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link
            href="/coordinador/vehiculos"
            className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Gestión de Vehículos
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Crear, editar y gestionar vehículos de la zona
            </p>
          </Link>
          <Link
            href="/coordinador/documentos"
            className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Soporte de Documentos
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Subir facturas, guías e informes administrativos
            </p>
          </Link>
          <Link
            href="/workorders"
            className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Órdenes de Trabajo
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Ver OTs abiertas y cerradas (solo lectura técnica)
            </p>
          </Link>
          <Link
            href="/reports"
            className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Reportes Operacionales
            </h3>
            <p className="text-sm text-gray-400">
              Tiempos, cargas y estado de flota
            </p>
          </Link>
        </div>
      </div>
    </RoleGuard>
  );
}

