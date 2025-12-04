"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";
import RoleGuard from "@/components/RoleGuard";
import Link from "next/link";
import { ENDPOINTS } from "@/lib/constants";
import { withSession } from "@/lib/api.client";

/**
 * Vista de Timeline consolidado de una OT.
 * 
 * Muestra:
 * - Línea de tiempo completa con todos los eventos
 * - Cambios de estado
 * - Comentarios
 * - Evidencias
 * - Pausas
 * - Checklists
 * - Actores involucrados
 * 
 * Permisos:
 * - Todos los roles con acceso a workorders
 */
export default function TimelineOTPage() {
  const router = useRouter();
  const params = useParams();
  const otId = params.id as string;
  const toast = useToast();
  const { hasRole } = useAuth();

  const [timeline, setTimeline] = useState<any[]>([]);
  const [actores, setActores] = useState<any[]>([]);
  const [ot, setOt] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (otId) {
      cargarTimeline();
    }
  }, [otId]);

  const cargarTimeline = async () => {
    setLoading(true);
    try {
      // Cargar OT
      const otResponse = await fetch(ENDPOINTS.WORK_ORDER(otId), {
        method: "GET",
        ...withSession(),
      });

      if (otResponse.ok) {
        const otData = await otResponse.json();
        setOt(otData);
      }

      // Cargar timeline
      const timelineResponse = await fetch(ENDPOINTS.WORK_ORDERS_TIMELINE(otId), {
        method: "GET",
        ...withSession(),
      });

      if (timelineResponse.ok) {
        const timelineData = await timelineResponse.json();
        setTimeline(timelineData.timeline || []);
        setActores(timelineData.actores || []);
      } else {
        const text = await timelineResponse.text();
        let errorData;
        try {
          errorData = JSON.parse(text);
        } catch {
          errorData = { detail: text || "Error desconocido" };
        }
        toast.error(errorData.detail || "Error al cargar timeline");
      }
    } catch (error) {
      console.error("Error al cargar timeline:", error);
      toast.error("Error al cargar timeline de la OT");
    } finally {
      setLoading(false);
    }
  };

  const getTipoIcon = (tipo: string) => {
    switch (tipo) {
      case "creacion":
        return "📥";
      case "cambio_estado":
        return "🔄";
      case "comentario":
        return "💬";
      case "evidencia":
        return "📷";
      case "pausa":
        return "⏸️";
      case "checklist":
        return "✅";
      default:
        return "📌";
    }
  };

  const getTipoColor = (tipo: string) => {
    switch (tipo) {
      case "creacion":
        return "bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300";
      case "cambio_estado":
        return "bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300";
      case "comentario":
        return "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300";
      case "evidencia":
        return "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300";
      case "pausa":
        return "bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-300";
      case "checklist":
        return "bg-indigo-100 dark:bg-indigo-900/30 text-indigo-800 dark:text-indigo-300";
      default:
        return "bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300";
    }
  };

  if (loading) {
    return (
      <RoleGuard allow={["ADMIN", "SUPERVISOR", "MECANICO", "JEFE_TALLER", "CHOFER"]}>
        <div className="p-6 flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando timeline...</p>
          </div>
        </div>
      </RoleGuard>
    );
  }

  return (
    <RoleGuard allow={["ADMIN", "SUPERVISOR", "MECANICO", "JEFE_TALLER", "CHOFER"]}>
      <div className="p-6 max-w-5xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Timeline de la OT
          </h1>
          <Link
            href={`/workorders/${otId}`}
            className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
          >
            ← Volver a OT
          </Link>
        </div>

        {/* Información de la OT */}
        {ot && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  OT #{ot?.id ? ot.id.slice(0, 8) : otId?.slice(0, 8) || 'N/A'}
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {ot.vehiculo_patente || ot.vehiculo?.patente} - Estado: {ot.estado}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Actores */}
        {actores.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              Actores Involucrados
            </h2>
            <div className="flex flex-wrap gap-2">
              {actores.map((actor, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded-lg text-sm"
                >
                  {actor.nombre} ({actor.rol})
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Timeline */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-6 text-gray-900 dark:text-white">
            Línea de Tiempo Completa
          </h2>
          {timeline.length > 0 ? (
            <div className="space-y-4">
              {timeline.map((item, index) => (
                <div key={index} className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg ${getTipoColor(item.tipo)}`}>
                      {getTipoIcon(item.tipo)}
                    </div>
                    {index < timeline.length - 1 && (
                      <div className="w-0.5 h-full bg-gray-300 dark:bg-gray-600 mt-2"></div>
                    )}
                  </div>
                  <div className="flex-1 pb-6">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <p className="font-semibold text-gray-900 dark:text-white">
                          {item.accion}
                        </p>
                        {item.usuario && (
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            Por: {item.usuario.nombre} ({item.usuario.rol})
                          </p>
                        )}
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {new Date(item.fecha).toLocaleString()}
                      </p>
                    </div>
                    {item.detalle && (
                      <div className="mt-2 text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                        {item.tipo === "comentario" && (
                          <p>{item.detalle.contenido}</p>
                        )}
                        {item.tipo === "pausa" && (
                          <div>
                            <p><strong>Motivo:</strong> {item.detalle.motivo}</p>
                            {item.detalle.duracion_minutos && (
                              <p><strong>Duración:</strong> {item.detalle.duracion_minutos} minutos</p>
                            )}
                          </div>
                        )}
                        {item.tipo === "cambio_estado" && (
                          <p>Estado anterior: {item.detalle.estado_anterior || "N/A"}</p>
                        )}
                        {item.tipo === "evidencia" && (
                          <div>
                            <p><strong>Tipo:</strong> {item.detalle.tipo}</p>
                            {item.detalle.descripcion && (
                              <p><strong>Descripción:</strong> {item.detalle.descripcion}</p>
                            )}
                            {item.detalle.invalidado && (
                              <span className="text-red-600 dark:text-red-400">⚠️ Invalidada</span>
                            )}
                          </div>
                        )}
                        {item.tipo === "checklist" && (
                          <div>
                            <p><strong>Resultado:</strong> {item.detalle.resultado}</p>
                            {item.detalle.observaciones && (
                              <p><strong>Observaciones:</strong> {item.detalle.observaciones}</p>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 dark:text-gray-400">
              No hay eventos registrados en el timeline aún.
            </p>
          )}
        </div>
      </div>
    </RoleGuard>
  );
}

