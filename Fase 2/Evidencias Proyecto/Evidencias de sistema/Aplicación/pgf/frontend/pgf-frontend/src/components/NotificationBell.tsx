"use client";

import { useEffect, useState, useRef } from "react";
import { BellIcon } from "@heroicons/react/24/outline";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import { NotificationWebSocket } from "@/lib/websocket";

/**
 * Componente de notificaciones con badge y dropdown.
 * 
 * Características:
 * - Badge con contador de notificaciones no leídas
 * - Dropdown con lista de notificaciones
 * - Marcar como leída al hacer clic
 * - Actualización automática cada 30 segundos
 * - Sonido de notificación para nuevas
 * - Navegación a OT relacionada
 */
export default function NotificationBell() {
  const [notificaciones, setNotificaciones] = useState<any[]>([]);
  const [noLeidas, setNoLeidas] = useState(0);
  const [abierto, setAbierto] = useState(false);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const toast = useToast();
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const wsRef = useRef<NotificationWebSocket | null>(null);

  // Cargar notificaciones
  const cargarNotificaciones = async () => {
    try {
      const r = await fetch("/api/proxy/notifications/no-leidas/", {
        credentials: "include",
      });
      if (r.ok) {
        const text = await r.text();
        if (text && text.trim()) {
          const data = JSON.parse(text);
          setNotificaciones(data);
          setNoLeidas(data.length);
        }
      }
    } catch (error) {
      console.error("Error al cargar notificaciones:", error);
    }
  };

  // Cargar contador
  const cargarContador = async () => {
    try {
      const r = await fetch("/api/proxy/notifications/contador/", {
        credentials: "include",
      });
      if (r.ok) {
        const text = await r.text();
        if (text && text.trim()) {
          const data = JSON.parse(text);
          const nuevoContador = data.no_leidas || 0;
          
          // Si hay nuevas notificaciones, reproducir sonido (si está habilitado)
          if (nuevoContador > noLeidas && noLeidas > 0) {
            // Verificar preferencias de sonido
            const sonidoHabilitado = localStorage.getItem("notificaciones_sonido") !== "false";
            if (sonidoHabilitado) {
              reproducirSonido();
            }
            toast.info("Tienes nuevas notificaciones");
            
            // Mostrar notificación push si está habilitada
            if ("Notification" in window && Notification.permission === "granted") {
              const pushHabilitado = localStorage.getItem("notificaciones_push") === "true";
              if (pushHabilitado) {
                new Notification("Nueva notificación", {
                  body: "Tienes nuevas notificaciones",
                  icon: "/favicon.ico",
                  badge: "/favicon.ico",
                });
              }
            }
          }
          
          setNoLeidas(nuevoContador);
        }
      }
    } catch (error) {
      // Solo loguear errores en modo desarrollo para no saturar la consola
      if (process.env.NODE_ENV === "development") {
        console.error("Error al cargar contador:", error);
      }
      // No mostrar error al usuario, es normal si el servidor no está disponible
    }
  };

  // Reproducir sonido de notificación usando Web Audio API
  const reproducirSonido = () => {
    try {
      // Intentar usar Web Audio API para generar sonido
      const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
      if (AudioContext) {
        const audioContext = new AudioContext();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800; // Frecuencia del tono
        oscillator.type = "sine";
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.3);
      }
    } catch (error) {
      // Si falla, no hacer nada (sonido opcional)
      console.debug("No se pudo reproducir sonido de notificación:", error);
    }
  };

  // Marcar como leída
  const marcarLeida = async (id: string) => {
    try {
      const r = await fetch(`/api/proxy/notifications/${id}/marcar-leida/`, {
        method: "POST",
        credentials: "include",
      });
      if (r.ok) {
        // Actualizar estado local inmediatamente
        setNotificaciones((prev) => 
          prev.map((n: any) => 
            n.id === id ? { ...n, estado: "LEIDA", status: "LEIDA" } : n
          )
        );
        setNoLeidas((prev) => Math.max(0, prev - 1));
        // Recargar para sincronizar
        await cargarNotificaciones();
        await cargarContador();
      }
    } catch (error) {
      console.error("Error al marcar como leída:", error);
    }
  };

  // Manejar clic en notificación
  const handleClickNotificacion = async (notif: any) => {
    await marcarLeida(notif.id);
    
    // Navegar a OT si existe
    if (notif.ot_id) {
      router.push(`/workorders/${notif.ot_id}`);
    }
    
    setAbierto(false);
  };

  // Cerrar dropdown al hacer clic fuera
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setAbierto(false);
      }
    };

    if (abierto) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [abierto]);

  // Solicitar permiso para notificaciones push al montar
  useEffect(() => {
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission().then((permission) => {
        if (permission === "granted") {
          console.log("Permiso para notificaciones push concedido");
        }
      });
    }
  }, []);

  // Cargar preferencias del usuario
  useEffect(() => {
    const cargarPreferencias = async () => {
      try {
        const r = await fetch("/api/proxy/users/me/", { credentials: "include" });
        if (r.ok) {
          const text = await r.text();
          if (text && text.trim()) {
            const user = JSON.parse(text);
            if (user.profile) {
              localStorage.setItem("notificaciones_sonido", user.profile.notificaciones_sonido ? "true" : "false");
              localStorage.setItem("notificaciones_push", user.profile.notificaciones_push ? "true" : "false");
            }
          }
        }
      } catch (error) {
        console.error("Error al cargar preferencias:", error);
      }
    };
    cargarPreferencias();
  }, []);

  // Conectar WebSocket para notificaciones en tiempo real
  useEffect(() => {
    const getToken = async () => {
      try {
        // La cookie pgf_access está marcada como HttpOnly, por lo que no es accesible desde JavaScript
        // Necesitamos obtener el token a través de un endpoint del servidor
        // que puede leer las cookies HttpOnly
        const response = await fetch("/api/auth/token", { 
          credentials: "include",
          method: "GET",
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.token) {
            return data.token;
          }
        }
        
        return null;
      } catch (error) {
        console.debug("Error al obtener token para WebSocket:", error);
        return null;
      }
    };

    const ws = new NotificationWebSocket(getToken);
    wsRef.current = ws;

    // Conectar
    ws.connect();

    // Suscribirse a notificaciones
    const unsubscribe = ws.on("notification", (notification: any) => {
      // Nueva notificación recibida en tiempo real
      console.log("Nueva notificación recibida:", notification);
      
      // Actualizar contador
      setNoLeidas((prev) => prev + 1);
      
      // Agregar a la lista si el dropdown está abierto
      if (abierto) {
        setNotificaciones((prev) => [notification, ...prev]);
      }
      
      // Reproducir sonido si está habilitado
      const sonidoHabilitado = localStorage.getItem("notificaciones_sonido") !== "false";
      if (sonidoHabilitado) {
        reproducirSonido();
      }
      
      // Mostrar toast
      toast.info(notification.titulo || "Nueva notificación");
      
      // Mostrar notificación push si está habilitada
      if ("Notification" in window && Notification.permission === "granted") {
        const pushHabilitado = localStorage.getItem("notificaciones_push") === "true";
        if (pushHabilitado) {
          new Notification(notification.titulo || "Nueva notificación", {
            body: notification.mensaje || notification.message || "",
            icon: "/favicon.ico",
            badge: "/favicon.ico",
          });
        }
      }
    });

    // Cleanup al desmontar
    return () => {
      unsubscribe();
      ws.disconnect();
    };
  }, [abierto, toast]);

  // Cargar notificaciones al montar
  useEffect(() => {
    cargarNotificaciones();
    cargarContador();
  }, []);

  // Actualizar cada 30 segundos
  useEffect(() => {
    const interval = setInterval(() => {
      cargarContador();
      if (abierto) {
        cargarNotificaciones();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [abierto]);

  // Formatear fecha
  const formatFecha = (fechaStr: string) => {
    if (!fechaStr) return "";
    try {
      const fecha = new Date(fechaStr);
      const ahora = new Date();
      const diffMs = ahora.getTime() - fecha.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) return "Ahora";
      if (diffMins < 60) return `Hace ${diffMins} min`;
      if (diffHours < 24) return `Hace ${diffHours} h`;
      if (diffDays < 7) return `Hace ${diffDays} d`;
      return fecha.toLocaleDateString("es-CL", { day: "numeric", month: "short" });
    } catch {
      return fechaStr;
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => {
          setAbierto(!abierto);
          if (!abierto) {
            cargarNotificaciones();
          }
        }}
        className="relative p-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
      >
        <BellIcon className="w-6 h-6" />
        {noLeidas > 0 && (
          <span className="absolute top-0 right-0 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
            {noLeidas > 9 ? "9+" : noLeidas}
          </span>
        )}
      </button>

      {abierto && (
        <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 z-50 max-h-96 overflow-y-auto">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <h3 className="font-semibold text-gray-900 dark:text-white">Notificaciones</h3>
            {noLeidas > 0 && (
              <button
                onClick={async () => {
                  try {
                    setLoading(true);
                    const response = await fetch("/api/proxy/notifications/marcar-todas-leidas/", {
                      method: "POST",
                      credentials: "include",
                    });
                    
                    if (response.ok) {
                      // Limpiar notificaciones no leídas del estado local
                      setNotificaciones([]);
                      setNoLeidas(0);
                      // Recargar para asegurar sincronización
                      await cargarNotificaciones();
                      await cargarContador();
                    } else {
                      console.error("Error al marcar todas como leídas:", response.status);
                      toast.error("Error al marcar notificaciones como leídas");
                    }
                  } catch (error) {
                    console.error("Error:", error);
                    toast.error("Error al marcar notificaciones como leídas");
                  } finally {
                    setLoading(false);
                  }
                }}
                className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
              >
                Marcar todas como leídas
              </button>
            )}
          </div>

          {loading ? (
            <div className="p-4 text-center text-gray-500 dark:text-gray-400">
              Cargando...
            </div>
          ) : notificaciones.length === 0 ? (
            <div className="p-4 text-center text-gray-500 dark:text-gray-400">
              No hay notificaciones nuevas
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {notificaciones.map((notif) => (
                <div
                  key={notif.id}
                  onClick={() => handleClickNotificacion(notif)}
                  className={`p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                    (notif.estado === "NO_LEIDA" || notif.status === "NO_LEIDA") ? "bg-blue-50 dark:bg-blue-900/20" : ""
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="flex-1">
                      <p className="font-semibold text-sm text-gray-900 dark:text-white">
                        {notif.titulo || notif.tipo || "Notificación"}
                      </p>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                        {notif.mensaje || notif.message || ""}
                      </p>
                      {notif.ot_patente && (
                        <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                          OT: {notif.ot_patente}
                        </p>
                      )}
                      <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                        {formatFecha(notif.creada_en || notif.created_at)}
                      </p>
                    </div>
                    {(notif.estado === "NO_LEIDA" || notif.status === "NO_LEIDA") && (
                      <div className="w-2 h-2 bg-blue-600 rounded-full mt-1"></div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

