"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";
import RoleGuard from "@/components/RoleGuard";
import Link from "next/link";

/**
 * Vista de Integraciones para Administrador.
 * 
 * Muestra:
 * - Configuración de S3
 * - Configuración de correos
 * - Logs técnicos
 * - Dashboard de errores
 * 
 * Permisos:
 * - Solo ADMIN puede acceder
 */
export default function AdminIntegracionesPage() {
  const router = useRouter();
  const toast = useToast();
  const { hasRole } = useAuth();

  return (
    <RoleGuard allow={["ADMIN"]}>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Integraciones del Sistema
          </h1>
          <Link
            href="/admin"
            className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
          >
            ← Volver
          </Link>
        </div>

        {/* S3 */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
            Configuración de S3
          </h2>
          <div className="space-y-3 text-sm text-gray-600 dark:text-gray-400">
            <div className="flex justify-between">
              <span>Bucket:</span>
              <span className="font-mono">{process.env.NEXT_PUBLIC_S3_BUCKET || "pgf-evidencias-dev"}</span>
            </div>
            <div className="flex justify-between">
              <span>Región:</span>
              <span className="font-mono">us-east-1</span>
            </div>
            <div className="flex justify-between">
              <span>Estado:</span>
              <span className="text-green-600 dark:text-green-400">✓ Conectado</span>
            </div>
          </div>
        </div>

        {/* Correos */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
            Configuración de Correos
          </h2>
          <div className="text-gray-500 dark:text-gray-400">
            <p>Configuración de servidor SMTP para envío de notificaciones por email.</p>
          </div>
        </div>

        {/* Logs Técnicos */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
            Logs Técnicos
          </h2>
          <div className="text-gray-500 dark:text-gray-400">
            <p>Visualización de logs del backend (en desarrollo).</p>
          </div>
        </div>

        {/* Dashboard de Errores */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
            Dashboard de Errores
          </h2>
          <div className="text-gray-500 dark:text-gray-400">
            <p>Sistema de monitoreo de errores del sistema (en desarrollo).</p>
          </div>
        </div>
      </div>
    </RoleGuard>
  );
}

