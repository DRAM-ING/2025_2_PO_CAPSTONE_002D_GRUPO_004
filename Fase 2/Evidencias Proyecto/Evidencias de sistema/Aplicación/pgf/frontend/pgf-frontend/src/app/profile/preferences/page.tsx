"use client";

import { useEffect, useState } from "react";
import { useToast } from "@/components/ToastContainer";
import { useRouter } from "next/navigation";

/**
 * Página de preferencias de notificaciones del usuario.
 * 
 * Permite al usuario configurar:
 * - Notificaciones por email
 * - Sonido de notificaciones
 * - Notificaciones push del navegador
 */
export default function PreferencesPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [preferences, setPreferences] = useState({
    notificaciones_email: true,
    notificaciones_sonido: true,
    notificaciones_push: false,
  });
  const [pushPermission, setPushPermission] = useState<NotificationPermission>("default");
  const toast = useToast();
  const router = useRouter();

  // Cargar preferencias actuales
  useEffect(() => {
    const cargar = async () => {
      try {
        const r = await fetch("/api/proxy/users/me/", { credentials: "include" });
        if (r.ok) {
          const user = await r.json();
          if (user.profile) {
            setPreferences({
              notificaciones_email: user.profile.notificaciones_email ?? true,
              notificaciones_sonido: user.profile.notificaciones_sonido ?? true,
              notificaciones_push: user.profile.notificaciones_push ?? false,
            });
          }
        }
      } catch (error) {
        console.error("Error al cargar preferencias:", error);
        toast.error("Error al cargar preferencias");
      } finally {
        setLoading(false);
      }
    };
    cargar();

    // Verificar permiso de notificaciones push
    if ("Notification" in window) {
      setPushPermission(Notification.permission);
    }
  }, [toast]);

  // Guardar preferencias
  const guardar = async () => {
    setSaving(true);
    try {
      // Obtener usuario
      const rUser = await fetch("/api/proxy/users/me/", { credentials: "include" });
      if (!rUser.ok) throw new Error("No se pudo obtener el usuario");
      const user = await rUser.json();
      
      // Si no tiene perfil, el backend debería crearlo automáticamente
      // Pero por si acaso, intentamos crear uno si no existe
      if (!user.profile?.id) {
        // Intentar crear perfil
        try {
          const rCreate = await fetch("/api/proxy/users/profiles/", {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              first_name: user.first_name || "",
              last_name: user.last_name || "",
              ...preferences,
            }),
          });

          if (rCreate.ok) {
            toast.success("Preferencias guardadas correctamente");
            // Actualizar localStorage
            localStorage.setItem("notificaciones_sonido", preferences.notificaciones_sonido ? "true" : "false");
            localStorage.setItem("notificaciones_push", preferences.notificaciones_push ? "true" : "false");
            return;
          }
        } catch (createError) {
          // Si falla la creación, mostrar mensaje más específico
          console.error("Error al crear perfil:", createError);
          toast.error("Error: El perfil no existe y no se pudo crear. Contacta al administrador.");
          return;
        }
      }

      // Actualizar perfil existente
      const r = await fetch(`/api/proxy/users/profiles/${user.profile.id}/`, {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(preferences),
      });

      if (r.ok) {
        toast.success("Preferencias guardadas correctamente");
        // Actualizar localStorage
        localStorage.setItem("notificaciones_sonido", preferences.notificaciones_sonido ? "true" : "false");
        localStorage.setItem("notificaciones_push", preferences.notificaciones_push ? "true" : "false");
      } else {
        throw new Error("Error al guardar");
      }
    } catch (error) {
      console.error("Error al guardar preferencias:", error);
      toast.error("Error al guardar preferencias: " + (error instanceof Error ? error.message : "Error desconocido"));
    } finally {
      setSaving(false);
    }
  };

  // Solicitar permiso para notificaciones push
  const solicitarPermisoPush = async () => {
    if ("Notification" in window && Notification.permission === "default") {
      const permission = await Notification.requestPermission();
      setPushPermission(permission);
      if (permission === "granted") {
        toast.success("Permiso para notificaciones push concedido");
        setPreferences({ ...preferences, notificaciones_push: true });
      } else {
        toast.error("Permiso para notificaciones push denegado");
      }
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="text-center">Cargando preferencias...</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Preferencias de Notificaciones
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Configura cómo deseas recibir notificaciones del sistema
        </p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-6">
        {/* Notificaciones por Email */}
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              Notificaciones por Email
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Recibir notificaciones importantes por correo electrónico
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={preferences.notificaciones_email}
              onChange={(e) =>
                setPreferences({ ...preferences, notificaciones_email: e.target.checked })
              }
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
          </label>
        </div>

        {/* Sonido de Notificaciones */}
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              Sonido de Notificaciones
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Reproducir sonido al recibir nuevas notificaciones
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={preferences.notificaciones_sonido}
              onChange={(e) =>
                setPreferences({ ...preferences, notificaciones_sonido: e.target.checked })
              }
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
          </label>
        </div>

        {/* Notificaciones Push */}
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              Notificaciones Push del Navegador
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Recibir notificaciones incluso cuando la aplicación está cerrada
            </p>
            {pushPermission === "denied" && (
              <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                Permiso denegado. Por favor, habilítalo en la configuración del navegador.
              </p>
            )}
          </div>
          <div className="flex items-center gap-2">
            {pushPermission === "default" && (
              <button
                onClick={solicitarPermisoPush}
                className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Solicitar Permiso
              </button>
            )}
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={preferences.notificaciones_push && pushPermission === "granted"}
                disabled={pushPermission !== "granted"}
                onChange={(e) =>
                  setPreferences({ ...preferences, notificaciones_push: e.target.checked })
                }
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600 peer-disabled:opacity-50"></div>
            </label>
          </div>
        </div>

        {/* Botones */}
        <div className="flex gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={guardar}
            disabled={saving}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ backgroundColor: "#003DA5" }}
          >
            {saving ? "Guardando..." : "Guardar Preferencias"}
          </button>
          <button
            onClick={() => router.back()}
            className="px-6 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 rounded-lg transition-colors font-medium"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
}

