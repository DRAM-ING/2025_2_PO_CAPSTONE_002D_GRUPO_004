/**
 * Hook para escuchar actualizaciones en tiempo real por WebSocket.
 * 
 * Este hook se suscribe a actualizaciones de datos (OTs, vehículos, etc.)
 * y permite ejecutar callbacks cuando ocurren cambios.
 */

import { useEffect, useRef } from "react";
import { NotificationWebSocket } from "@/lib/websocket";

interface UseRealtimeUpdateOptions {
  /**
   * Tipo de entidad a escuchar (workorder, vehicle, assignment, etc.)
   * Si es undefined, escucha todos los tipos
   */
  entityType?: string;
  
  /**
   * ID de la entidad específica a escuchar
   * Si es undefined, escucha todas las entidades del tipo
   */
  entityId?: string;
  
  /**
   * Callback que se ejecuta cuando hay una actualización
   */
  onUpdate?: (data: {
    entity_type: string;
    entity_id: string;
    action: string;
    data: any;
  }) => void;
  
  /**
   * Si es true, recarga la página automáticamente cuando hay actualizaciones
   */
  autoRefresh?: boolean;
}

/**
 * Hook para escuchar actualizaciones en tiempo real.
 * 
 * Ejemplo de uso:
 * ```tsx
 * useRealtimeUpdate({
 *   entityType: "workorder",
 *   entityId: otId,
 *   onUpdate: (update) => {
 *     console.log("OT actualizada:", update);
 *     // Recargar datos de la OT
 *   }
 * });
 * ```
 */
export function useRealtimeUpdate(options: UseRealtimeUpdateOptions = {}) {
  const { entityType, entityId, onUpdate, autoRefresh = false } = options;
  const wsRef = useRef<NotificationWebSocket | null>(null);
  const unsubscribeRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    // Función para obtener el token
    const getToken = async (): Promise<string | null> => {
      try {
        const response = await fetch("/api/auth/token", {
          credentials: "include",
        });
        
        if (response.ok) {
          const data = await response.json();
          return data.token || null;
        }
        
        return null;
      } catch (error) {
        console.debug("Error al obtener token para WebSocket:", error);
        return null;
      }
    };

    // Crear instancia de WebSocket
    const ws = new NotificationWebSocket(getToken);
    wsRef.current = ws;

    // Conectar
    ws.connect();

    // Suscribirse a actualizaciones
    const unsubscribe = ws.on("data_update", (update: any) => {
      // Filtrar por tipo de entidad si se especifica
      if (entityType && update.entity_type !== entityType) {
        return;
      }

      // Filtrar por ID de entidad si se especifica
      if (entityId && update.entity_id !== entityId) {
        return;
      }

      // Ejecutar callback si existe
      if (onUpdate) {
        onUpdate(update);
      }

      // Recargar página si está habilitado
      if (autoRefresh) {
        window.location.reload();
      }
    });

    unsubscribeRef.current = unsubscribe;

    // Cleanup al desmontar
    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
      }
      if (wsRef.current) {
        wsRef.current.disconnect();
      }
    };
  }, [entityType, entityId, onUpdate, autoRefresh]);
}

