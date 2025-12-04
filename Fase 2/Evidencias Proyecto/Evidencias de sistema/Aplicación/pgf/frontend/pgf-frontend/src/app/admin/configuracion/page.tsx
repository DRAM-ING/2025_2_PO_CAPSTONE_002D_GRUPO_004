"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";
import RoleGuard from "@/components/RoleGuard";
import Link from "next/link";

/**
 * Vista de Configuración del Sistema para Administrador.
 * 
 * Muestra:
 * - Configuración de Checklists
 * - Tipos de OT
 * - Catálogo de talleres
 * - Zonas
 * - Políticas de seguridad
 * 
 * Permisos:
 * - Solo ADMIN puede acceder
 */
export default function AdminConfiguracionPage() {
  const router = useRouter();
  const toast = useToast();
  const { hasRole } = useAuth();

  const [activeTab, setActiveTab] = useState("tipos-ot");

  return (
    <RoleGuard allow={["ADMIN"]}>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Configuración del Sistema
          </h1>
          <Link
            href="/admin"
            className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
          >
            ← Volver
          </Link>
        </div>

        {/* Tabs */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="flex -mb-px">
              {[
                { id: "tipos-ot", label: "Tipos de OT" },
                { id: "checklists", label: "Checklists" },
                { id: "talleres", label: "Talleres" },
                { id: "zonas", label: "Zonas" },
                { id: "seguridad", label: "Políticas de Seguridad" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? "border-blue-600 text-blue-600 dark:text-blue-400"
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6">
            {activeTab === "tipos-ot" && (
              <div>
                <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
                  Tipos de Orden de Trabajo
                </h2>
                <div className="text-gray-500 dark:text-gray-400">
                  <p>Configuración de tipos de OT disponibles en el sistema.</p>
                  <p className="mt-2">Tipos actuales: Mantención, Reparación, Diagnóstico, Otro</p>
                </div>
              </div>
            )}

            {activeTab === "checklists" && (
              <div>
                <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
                  Checklists
                </h2>
                <div className="text-gray-500 dark:text-gray-400">
                  <p>Configuración de checklists de calidad para OTs.</p>
                </div>
              </div>
            )}

            {activeTab === "talleres" && (
              <div>
                <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
                  Catálogo de Talleres
                </h2>
                <div className="text-gray-500 dark:text-gray-400">
                  <p>Gestión de talleres disponibles en el sistema.</p>
                </div>
              </div>
            )}

            {activeTab === "zonas" && (
              <div>
                <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
                  Zonas
                </h2>
                <div className="text-gray-500 dark:text-gray-400">
                  <p>Configuración de zonas geográficas.</p>
                </div>
              </div>
            )}

            {activeTab === "seguridad" && (
              <div>
                <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
                  Políticas de Seguridad
                </h2>
                <div className="text-gray-500 dark:text-gray-400">
                  <p>Configuración de políticas de seguridad del sistema.</p>
                  <ul className="mt-4 space-y-2 list-disc list-inside">
                    <li>Duración de sesión: 8 horas</li>
                    <li>Refresh token: 7 días</li>
                    <li>Bloqueo por intentos fallidos: Deshabilitado</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </RoleGuard>
  );
}

