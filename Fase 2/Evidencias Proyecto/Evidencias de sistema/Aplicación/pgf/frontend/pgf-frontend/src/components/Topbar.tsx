"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/store/auth";
import NotificationBell from "@/components/NotificationBell";

export default function Topbar() {
  const [user, setUser] = useState<any>(null);
  const router = useRouter();
  const { setUser: setAuthUser } = useAuth();

  useEffect(() => {
    const loadUser = async () => {
      try {
        const res = await fetch("/api/auth/me", { credentials: "include" });
        if (res.ok) {
          const data = await res.json();
          setUser(data);
          setAuthUser(data);
        }
      } catch (err) {
        console.error("Error loading user:", err);
      }
    };
    loadUser();
  }, [setAuthUser]);

  async function logout() {
    try {
      await fetch("/api/auth/logout", { 
        method: "POST",
        credentials: "include"
      });
      setAuthUser(null);
      router.push("/auth/login");
    } catch (error) {
      console.error("Error al cerrar sesión:", error);
      // Forzar redirección incluso si hay error
      setAuthUser(null);
      router.push("/auth/login");
    }
  }

  // Función para obtener el título según el rol
  const getPanelTitle = (rol: string | undefined): string => {
    if (!rol) return "PGF - Plataforma de Gestión de Flota";
    
    const titles: Record<string, string> = {
      ADMIN: "Panel de Administración",
      SUPERVISOR: "Panel de Supervisor",
      JEFE_TALLER: "Panel del Taller",
      MECANICO: "Panel del Mecánico",
      GUARDIA: "Panel de Guardia",
      COORDINADOR_ZONA: "Panel de Coordinación",
      EJECUTIVO: "Panel Ejecutivo",
      SPONSOR: "Panel de Sponsor",
      CHOFER: "Panel del Chofer",
    };
    
    return titles[rol] || "PGF - Plataforma de Gestión de Flota";
  };

  return (
    <header className="h-16 bg-white dark:bg-gray-800 shadow-lg flex items-center justify-between px-6 border-b-2 border-[#003DA5]/20 dark:border-[#003DA5]/30">
      <h1 className="text-xl font-bold text-[#003DA5] dark:text-white">
        {getPanelTitle(user?.rol)}
      </h1>

      <div className="flex items-center gap-4">
        {/* Componente de notificaciones */}
        {user && <NotificationBell />}
        
        {user && (
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                {user.first_name} {user.last_name}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {user.rol}
              </p>
            </div>
            <div className="w-10 h-10 rounded-full bg-[#003DA5] flex items-center justify-center text-white font-semibold shadow-md">
              {user.first_name?.[0]}{user.last_name?.[0]}
            </div>
          </div>
        )}

        {user && (
          <>
            <a
              href="/profile/preferences"
              className="px-3 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-[#003DA5]/10 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 rounded-lg transition-all duration-200 text-sm font-medium border border-gray-200 dark:border-gray-600 hover:border-[#003DA5]/30"
            >
              Preferencias
            </a>
            <a
              href="/profile/change-password"
              className="px-3 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-[#003DA5]/10 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 rounded-lg transition-all duration-200 text-sm font-medium border border-gray-200 dark:border-gray-600 hover:border-[#003DA5]/30"
            >
              Cambiar Contraseña
            </a>
          </>
        )}

        <button
          onClick={logout}
          className="px-4 py-2 bg-[#E60012] hover:bg-[#CC0010] text-white rounded-lg transition-all duration-200 text-sm font-semibold shadow-md hover:shadow-lg transform hover:-translate-y-0.5"
        >
          Cerrar sesión
        </button>
      </div>
    </header>
  );
}

