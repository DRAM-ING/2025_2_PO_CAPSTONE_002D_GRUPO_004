"use client";

import { useAuth } from "@/store/auth";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import { invalidateCache } from "@/lib/dataRefresh";
import { useRealtimeUpdate } from "@/hooks/useRealtimeUpdate";
import EvidenceThumbnail from "@/components/EvidenceThumbnail";

interface WorkOrderDetailClientProps {
  ot: any;
  id: string;
}

export default function WorkOrderDetailClient({ ot, id }: WorkOrderDetailClientProps) {
  const router = useRouter();
  const toast = useToast();
  const { hasRole, user } = useAuth();

  // Escuchar actualizaciones en tiempo real de esta OT
  useRealtimeUpdate({
    entityType: "workorder",
    entityId: id,
    onUpdate: (update) => {
      // Mostrar notificación de actualización
      if (update.action === "updated") {
        toast.info("La OT ha sido actualizada");
        // Invalidar cache y refrescar
        invalidateCache("WORKORDERS");
        router.refresh();
      } else if (update.action === "assigned") {
        toast.success("Se ha asignado un mecánico a esta OT");
        invalidateCache("WORKORDERS");
        router.refresh();
      }
    }
  });

  // Permisos según nueva especificación
  const isJefeTaller = hasRole(["JEFE_TALLER"]);
  const isMecanico = hasRole(["MECANICO"]);
  const isAdmin = hasRole(["ADMIN"]);
  const canEdit = isJefeTaller || isAdmin;
  const canChangeState = isMecanico || isJefeTaller;
  const canClose = isJefeTaller;
  const canAssign = isJefeTaller || isAdmin;
  // Roles autorizados para subir evidencias
  const canUploadEvidence = hasRole(["MECANICO", "SUPERVISOR", "ADMIN", "GUARDIA", "JEFE_TALLER"]);

  // Acciones de cambio de estado
  const handleStateChange = async (action: string) => {
    try {
      const response = await fetch(`/api/proxy/work/ordenes/${id}/${action}/`, {
        method: "POST",
        credentials: "include",
      });

      if (response.ok) {
        toast.success("Estado actualizado correctamente");
        // Invalidar cache y refrescar datos
        invalidateCache("WORKORDERS");
        router.refresh();
        // Recargar la página para obtener datos actualizados
        window.location.reload();
      } else {
        const text = await response.text();
        let errorData;
        try {
          errorData = JSON.parse(text);
        } catch {
          errorData = { detail: text || "Error desconocido" };
        }
        toast.error(errorData.detail || "Error al cambiar estado");
      }
    } catch (error) {
      console.error("Error al cambiar estado:", error);
      toast.error("Error al cambiar estado");
    }
  };

  // Seguridad
  const evidencias = ot.evidencias ?? [];
  const comentarios = ot.comentarios ?? [];
  const items = ot.items ?? [];

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Orden de Trabajo #{id}</h1>
        <div className="flex gap-3">
          <Link
            href={`/workorders/${id}/timeline`}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors font-medium"
          >
            Timeline
          </Link>
          <Link
            href={`/workorders/${id}/comentarios`}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors font-medium"
          >
            Comentarios
          </Link>
          {canEdit && (
            <Link
              href={`/workorders/${id}/edit`}
              className="px-4 py-2 text-white rounded-lg transition-colors font-medium"
              style={{ backgroundColor: '#003DA5' }}
            >
              Editar
            </Link>
          )}
          {ot.estado === "ABIERTA" && isAdmin && (
            <Link
              href={`/workorders/${id}/delete`}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors font-medium"
            >
              Eliminar
            </Link>
          )}
        </div>
      </div>

      {/* === Estado y botones === */}
      <section className="p-6 bg-white dark:bg-gray-800 shadow rounded-lg space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold mb-2 text-gray-900 dark:text-white">Estado Actual</h2>
            <span className={`inline-block px-3 py-1 rounded text-sm font-medium ${
              ot.estado === "ABIERTA" ? "bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-400" :
              ot.estado === "EN_DIAGNOSTICO" ? "bg-indigo-100 dark:bg-indigo-900/30 text-indigo-800 dark:text-indigo-400" :
              ot.estado === "EN_EJECUCION" ? "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-400" :
              ot.estado === "EN_PAUSA" ? "bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-400" :
              ot.estado === "EN_QA" ? "bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-400" :
              ot.estado === "RETRABAJO" ? "bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-400" :
              ot.estado === "CERRADA" ? "bg-gray-100 dark:bg-gray-900/30 text-gray-800 dark:text-gray-400" :
              "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400"
            }`}>
              {ot.estado}
            </span>
          </div>
        </div>

        {/* Acciones según estado y rol */}
        <div className="flex flex-wrap gap-3 mt-4">
          {/* Diagnóstico: Solo JEFE_TALLER */}
          {ot.estado === "ABIERTA" && isJefeTaller && (
            <Link
              href={`/workorders/${id}/diagnostico`}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors font-medium"
            >
              Realizar Diagnóstico
            </Link>
          )}
          
          {/* Aprobar Asignación: Solo JEFE_TALLER */}
          {ot.estado === "EN_DIAGNOSTICO" && canAssign && (
            <Link
              href={`/workorders/${id}/aprobar-asignacion`}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors font-medium"
            >
              Aprobar Asignación
            </Link>
          )}

          {/* Cambiar a EN_EJECUCION: MECANICO o JEFE_TALLER */}
          {ot.estado === "ABIERTA" && canChangeState && (
            <button
              onClick={() => handleStateChange("en-ejecucion")}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
            >
              Iniciar Ejecución
            </button>
          )}

          {/* Cambiar a EN_PAUSA: MECANICO o JEFE_TALLER */}
          {ot.estado === "EN_EJECUCION" && canChangeState && (
            <button
              onClick={() => handleStateChange("en-pausa")}
              className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-colors font-medium"
            >
              Pausar
            </button>
          )}

          {/* Esperando Repuestos: MECANICO o JEFE_TALLER */}
          {ot.estado === "EN_EJECUCION" && canChangeState && (
            <button
              onClick={() => handleStateChange("esperando-repuestos")}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors font-medium"
            >
              Esperando Repuestos
            </button>
          )}

          {/* Cambiar a EN_QA: MECANICO o JEFE_TALLER */}
          {ot.estado === "EN_EJECUCION" && canChangeState && (
            <button
              onClick={() => handleStateChange("en-qa")}
              className="px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-white rounded-lg transition-colors font-medium"
            >
              Enviar a QA
            </button>
          )}

          {/* Reanudar desde EN_PAUSA: MECANICO o JEFE_TALLER */}
          {ot.estado === "EN_PAUSA" && canChangeState && (
            <button
              onClick={() => handleStateChange("en-ejecucion")}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors font-medium"
            >
              Reanudar Ejecución
            </button>
          )}

          {/* Marcar Retrabajo: Solo JEFE_TALLER */}
          {ot.estado === "EN_QA" && canClose && (
            <Link
              href={`/workorders/${id}/retrabajo`}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors font-medium"
            >
              Marcar como Retrabajo
            </Link>
          )}

          {/* Reabrir OT cerrada: Solo JEFE_TALLER */}
          {ot.estado === "CERRADA" && isJefeTaller && (
            <button
              onClick={() => handleStateChange("en-ejecucion")}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
            >
              Reabrir OT
            </button>
          )}

          {/* Cerrar OT: Solo JEFE_TALLER */}
          {ot.estado === "EN_QA" && canClose && (
            <button
              onClick={async () => {
                if (!confirm("¿Estás seguro de que deseas cerrar esta OT? Esta acción no se puede deshacer.")) {
                  return;
                }
                try {
                  const response = await fetch(`/api/proxy/work/ordenes/${id}/cerrar/`, {
                    method: "POST",
                    credentials: "include",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      fecha_cierre: new Date().toISOString(),
                      diagnostico_final: "OT cerrada desde el sistema",
                      estado_final: "CERRADA"
                    }),
                  });
                  
                  if (!response.ok) {
                    const text = await response.text();
                    let errorData;
                    try {
                      errorData = JSON.parse(text);
                    } catch {
                      errorData = { detail: text || "Error desconocido" };
                    }
                    toast.error(errorData.detail || "Error al cerrar la OT");
                    return;
                  }
                  
                  toast.success("OT cerrada correctamente");
                  router.refresh();
                  router.push(`/workorders/${id}`);
                } catch (error) {
                  console.error("Error al cerrar OT:", error);
                  toast.error("Error al cerrar la OT");
                }
              }}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors font-medium"
            >
              Cerrar OT
            </button>
          )}
        </div>
      </section>

      {/* Trazabilidad */}
      {ot.trazabilidad && (
        <section className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow space-y-4">
          <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">📋 Trazabilidad</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Fechas importantes */}
            {ot.trazabilidad.fechas_importantes && (
              <div>
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Fechas Importantes</h3>
                <div className="space-y-2 text-sm">
                  {ot.trazabilidad.fechas_importantes.apertura && (
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Apertura:</span>
                      <span className="text-gray-900 dark:text-white font-medium">
                        {(() => {
                          const fechaApertura = ot.trazabilidad.fechas_importantes.apertura;
                          if (!fechaApertura) return "N/A";
                          try {
                            const fecha = new Date(fechaApertura);
                            if (isNaN(fecha.getTime())) return "N/A";
                            return fecha.toLocaleString('es-CL');
                          } catch (e) {
                            return "N/A";
                          }
                        })()}
                      </span>
                    </div>
                  )}
                  {ot.trazabilidad.fechas_importantes.diagnostico && (
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Diagnóstico:</span>
                      <span className="text-gray-900 dark:text-white font-medium">
                        {new Date(ot.trazabilidad.fechas_importantes.diagnostico).toLocaleString('es-CL')}
                      </span>
                    </div>
                  )}
                  {ot.trazabilidad.fechas_importantes.asignacion_mecanico && (
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Asignación Mecánico:</span>
                      <span className="text-gray-900 dark:text-white font-medium">
                        {new Date(ot.trazabilidad.fechas_importantes.asignacion_mecanico).toLocaleString('es-CL')}
                      </span>
                    </div>
                  )}
                  {ot.trazabilidad.fechas_importantes.inicio_ejecucion && (
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Inicio Ejecución:</span>
                      <span className="text-gray-900 dark:text-white font-medium">
                        {new Date(ot.trazabilidad.fechas_importantes.inicio_ejecucion).toLocaleString('es-CL')}
                      </span>
                    </div>
                  )}
                  {ot.trazabilidad.fechas_importantes.cierre && (
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Cierre:</span>
                      <span className="text-gray-900 dark:text-white font-medium">
                        {new Date(ot.trazabilidad.fechas_importantes.cierre).toLocaleString('es-CL')}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Última acción */}
            {ot.trazabilidad.ultima_auditoria && (
              <div>
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Última Acción</h3>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Acción: </span>
                    <span className="text-gray-900 dark:text-white font-medium">
                      {ot.trazabilidad.ultima_auditoria.accion}
                    </span>
                  </div>
                  {ot.trazabilidad.ultima_auditoria.usuario && (
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Usuario: </span>
                      <span className="text-gray-900 dark:text-white font-medium">
                        {ot.trazabilidad.ultima_auditoria.usuario}
                        {ot.trazabilidad.ultima_auditoria.usuario_rol && (
                          <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
                            ({ot.trazabilidad.ultima_auditoria.usuario_rol})
                          </span>
                        )}
                      </span>
                    </div>
                  )}
                  {ot.trazabilidad.ultima_auditoria.fecha && (
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Fecha: </span>
                      <span className="text-gray-900 dark:text-white font-medium">
                        {new Date(ot.trazabilidad.ultima_auditoria.fecha).toLocaleString('es-CL')}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Historial reciente */}
          {ot.trazabilidad.auditorias_recientes && ot.trazabilidad.auditorias_recientes.length > 0 && (
            <div className="mt-4">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Historial Reciente</h3>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {ot.trazabilidad.auditorias_recientes.map((auditoria: any, idx: number) => (
                  <div key={idx} className="p-2 bg-gray-50 dark:bg-gray-700/50 rounded text-xs">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <span className="font-medium text-gray-900 dark:text-white">{auditoria.accion}</span>
                        {auditoria.usuario && (
                          <span className="ml-2 text-gray-600 dark:text-gray-400">
                            por {auditoria.usuario}
                            {auditoria.usuario_rol && (
                              <span className="ml-1 text-gray-500 dark:text-gray-500">({auditoria.usuario_rol})</span>
                            )}
                          </span>
                        )}
                      </div>
                      <span className="text-gray-500 dark:text-gray-400 ml-2">
                        {new Date(auditoria.fecha).toLocaleString('es-CL')}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      {/* Información general */}
      <section className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow space-y-4">
        <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Información General</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Tipo
            </label>
            <p className="text-lg text-gray-900 dark:text-white">{ot.tipo || "N/A"}</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Prioridad
            </label>
            <span className={`inline-block px-3 py-1 rounded text-sm font-medium ${
              ot.prioridad === "ALTA" ? "bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-400" :
              ot.prioridad === "MEDIA" ? "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-400" :
              "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400"
            }`}>
              {ot.prioridad || "MEDIA"}
            </span>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Supervisor
            </label>
            <p className="text-lg text-gray-900 dark:text-white">
              {ot.supervisor_detalle?.nombre_completo || ot.supervisor_nombre || (ot.supervisor
                ? `${ot.supervisor.first_name} ${ot.supervisor.last_name}`
                : "Sin supervisor")}
            </p>
            {ot.supervisor_detalle && (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {ot.supervisor_detalle.email} • {ot.supervisor_detalle.rol}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Jefe de Taller
            </label>
            <p className="text-lg text-gray-900 dark:text-white">
              {ot.jefe_taller_detalle?.nombre_completo || ot.jefe_taller_nombre || (ot.jefe_taller
                ? `${ot.jefe_taller.first_name} ${ot.jefe_taller.last_name}`
                : "Sin asignar")}
            </p>
            {ot.jefe_taller_detalle && (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {ot.jefe_taller_detalle.email} • {ot.jefe_taller_detalle.rol}
              </p>
            )}
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">
                Mecánico
              </label>
              {canAssign && ot.estado !== "CERRADA" && (
                <Link
                  href={`/workorders/${id}/aprobar-asignacion`}
                  className="text-sm px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
                >
                  {ot.mecanico ? "Reasignar" : "Asignar"}
                </Link>
              )}
            </div>
            <p className="text-lg text-gray-900 dark:text-white">
              {ot.mecanico_detalle?.nombre_completo || ot.mecanico_nombre || (ot.mecanico
                ? `${ot.mecanico.first_name} ${ot.mecanico.last_name}`
                : "Sin asignar")}
            </p>
            {ot.mecanico_detalle && (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {ot.mecanico_detalle.email} • {ot.mecanico_detalle.rol}
              </p>
            )}
          </div>

          {ot.responsable_detalle && (
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                Responsable
              </label>
              <p className="text-lg text-gray-900 dark:text-white">
                {ot.responsable_detalle.nombre_completo || ot.responsable_nombre || "Sin asignar"}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {ot.responsable_detalle.email} • {ot.responsable_detalle.rol}
              </p>
            </div>
          )}

          {ot.chofer_detalle && (
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                Chofer
              </label>
              <p className="text-lg text-gray-900 dark:text-white">
                {ot.chofer_detalle.nombre_completo || "Sin asignar"}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                RUT: {ot.chofer_detalle.rut}
                {ot.chofer_detalle.telefono && ` • Tel: ${ot.chofer_detalle.telefono}`}
              </p>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Apertura
            </label>
            <p className="text-lg text-gray-900 dark:text-white">
              {(() => {
                const fechaApertura = ot.apertura || ot.fecha_apertura;
                if (!fechaApertura) return "N/A";
                try {
                  const fecha = new Date(fechaApertura);
                  if (isNaN(fecha.getTime())) return "N/A";
                  return fecha.toLocaleString('es-CL');
                } catch (e) {
                  return "N/A";
                }
              })()}
            </p>
          </div>

          {ot.fecha_diagnostico && (
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                Fecha Diagnóstico
              </label>
              <p className="text-lg text-gray-900 dark:text-white">
                {new Date(ot.fecha_diagnostico).toLocaleString('es-CL')}
              </p>
            </div>
          )}

          {ot.fecha_asignacion_mecanico && (
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                Asignación Mecánico
              </label>
              <p className="text-lg text-gray-900 dark:text-white">
                {new Date(ot.fecha_asignacion_mecanico).toLocaleString('es-CL')}
              </p>
            </div>
          )}

          {ot.fecha_inicio_ejecucion && (
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                Inicio Ejecución
              </label>
              <p className="text-lg text-gray-900 dark:text-white">
                {new Date(ot.fecha_inicio_ejecucion).toLocaleString('es-CL')}
              </p>
            </div>
          )}

          {ot.cierre && (
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                Cierre
              </label>
              <p className="text-lg text-gray-900 dark:text-white">
                {new Date(ot.cierre).toLocaleString('es-CL')}
              </p>
            </div>
          )}

          {ot.ultima_modificacion && (
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                Última Modificación
              </label>
              <p className="text-sm text-gray-700 dark:text-gray-300">
                {new Date(ot.ultima_modificacion.fecha).toLocaleString('es-CL')} por {ot.ultima_modificacion.usuario}
                {ot.ultima_modificacion.usuario_rol && (
                  <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
                    ({ot.ultima_modificacion.usuario_rol})
                  </span>
                )}
              </p>
            </div>
          )}

          {ot.motivo && (
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                Motivo
              </label>
              <p className="text-lg text-gray-900 dark:text-white">{ot.motivo}</p>
            </div>
          )}

          {ot.diagnostico && (
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                Diagnóstico
              </label>
              <p className="text-lg text-gray-900 dark:text-white whitespace-pre-wrap">{ot.diagnostico}</p>
            </div>
          )}
        </div>
      </section>

      {/* Vehículo */}
      <section className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Vehículo</h2>
        {ot.vehiculo_detalle || ot.vehiculo ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                Patente
              </label>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {ot.vehiculo_detalle?.patente || ot.vehiculo?.patente || ot.vehiculo_patente || "N/A"}
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                Marca
              </label>
              <p className="text-lg text-gray-900 dark:text-white">
                {ot.vehiculo_detalle?.marca || ot.vehiculo?.marca || "N/A"}
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                Modelo
              </label>
              <p className="text-lg text-gray-900 dark:text-white">
                {ot.vehiculo_detalle?.modelo || ot.vehiculo?.modelo || "N/A"}
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                Año
              </label>
              <p className="text-lg text-gray-900 dark:text-white">
                {ot.vehiculo_detalle?.anio || ot.vehiculo?.anio || "N/A"}
              </p>
            </div>
            {ot.vehiculo_detalle?.tipo && (
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                  Tipo
                </label>
                <p className="text-lg text-gray-900 dark:text-white">
                  {ot.vehiculo_detalle.tipo}
                </p>
              </div>
            )}
            {ot.vehiculo_detalle?.estado && (
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                  Estado
                </label>
                <p className="text-lg text-gray-900 dark:text-white">
                  {ot.vehiculo_detalle.estado}
                </p>
              </div>
            )}
            {ot.vehiculo_detalle?.estado_operativo && (
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                  Estado Operativo
                </label>
                <p className="text-lg text-gray-900 dark:text-white">
                  {ot.vehiculo_detalle.estado_operativo}
                </p>
              </div>
            )}
            {ot.vehiculo_detalle?.kilometraje_actual !== undefined && ot.vehiculo_detalle?.kilometraje_actual !== null && (
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                  Kilometraje
                </label>
                <p className="text-lg text-gray-900 dark:text-white">
                  {ot.vehiculo_detalle.kilometraje_actual?.toLocaleString() || "N/A"} km
                </p>
              </div>
            )}
            {ot.vehiculo_detalle?.supervisor && (
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                  Supervisor del Vehículo
                </label>
                <p className="text-lg text-gray-900 dark:text-white">
                  {ot.vehiculo_detalle.supervisor.nombre_completo}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {ot.vehiculo_detalle.supervisor.email} • {ot.vehiculo_detalle.supervisor.rol}
                </p>
              </div>
            )}
          </div>
        ) : (
          <p className="text-gray-500 dark:text-gray-400">Sin vehículo asignado</p>
        )}
      </section>

      {/* Items */}
      <section className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Items</h2>
          {items.length > 0 && (
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Total: ${items.reduce((sum: number, i: any) => sum + (i.cantidad * i.costo_unitario), 0).toLocaleString()}
            </span>
          )}
        </div>

        {items.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400">No hay items registrados.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-100 dark:bg-gray-700">
                  <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Tipo</th>
                  <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Descripción</th>
                  <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Cantidad</th>
                  <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Costo Unit.</th>
                  <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Total</th>
                </tr>
              </thead>
              <tbody>
                {items.map((i: any) => (
                  <tr key={i.id} className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="p-3 text-gray-900 dark:text-white">{i.tipo}</td>
                    <td className="p-3 text-gray-700 dark:text-gray-300">{i.descripcion}</td>
                    <td className="p-3 text-gray-700 dark:text-gray-300">{i.cantidad}</td>
                    <td className="p-3 text-gray-700 dark:text-gray-300">${i.costo_unitario.toLocaleString()}</td>
                    <td className="p-3 font-semibold text-gray-900 dark:text-white">
                      ${(i.cantidad * i.costo_unitario).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Evidencias */}
      <section className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Evidencias</h2>
          <div className="flex gap-3">
            <Link
              href={`/workorders/${id}/evidences`}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors font-medium text-sm"
            >
              Ver todas las evidencias
            </Link>
            {canUploadEvidence && (
              <Link
                href={`/workorders/${id}/evidences/upload`}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium text-sm"
              >
                + Subir Evidencia
              </Link>
            )}
          </div>
        </div>

        {evidencias.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500 dark:text-gray-400 mb-4">No hay evidencias registradas.</p>
            {canUploadEvidence && (
              <Link
                href={`/workorders/${id}/evidences/upload`}
                className="inline-block px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
              >
                Subir Primera Evidencia
              </Link>
            )}
          </div>
        ) : (
          <>
            <div className="mb-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Total: {evidencias.length} {evidencias.length === 1 ? 'evidencia' : 'evidencias'}
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {evidencias.slice(0, 6).map((e: any) => (
                <div key={e.id} className="border dark:border-gray-700 rounded-lg overflow-hidden hover:shadow-lg transition-shadow">
                  <Link href={`/workorders/${id}/evidences`} className="block">
                    <div className="aspect-video bg-gray-100 dark:bg-gray-700 flex items-center justify-center overflow-hidden">
                      <EvidenceThumbnail
                        evidenciaId={e.id}
                        url={e.url}
                        alt={e.descripcion || e.tipo || "Evidencia"}
                        className="w-full h-full object-cover"
                        tipo={e.tipo}
                      />
                    </div>
                    <div className="p-3">
                      <p className="font-medium text-gray-900 dark:text-white text-sm">
                        {e.descripcion || e.tipo || "Evidencia"}
                      </p>
                      {e.tipo && (
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Tipo: {e.tipo}</p>
                      )}
                      {e.subido_en && (
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                          {new Date(e.subido_en).toLocaleDateString('es-CL')}
                        </p>
                      )}
                      {e.subido_por_nombre && (
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                          Por: {e.subido_por_nombre}
                        </p>
                      )}
                    </div>
                  </Link>
                </div>
              ))}
            </div>
            {evidencias.length > 6 && (
              <div className="mt-4 text-center">
                <Link
                  href={`/workorders/${id}/evidences`}
                  className="text-blue-600 dark:text-blue-400 hover:underline font-medium"
                >
                  Ver {evidencias.length - 6} evidencias más →
                </Link>
              </div>
            )}
          </>
        )}
      </section>

      {/* Comentarios */}
      <section className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Comentarios</h2>
          <Link
            href={`/workorders/${id}/comentarios`}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors font-medium text-sm"
          >
            Ver todos los comentarios
          </Link>
        </div>

        {comentarios.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500 dark:text-gray-400 mb-4">No hay comentarios registrados.</p>
            <Link
              href={`/workorders/${id}/comentarios`}
              className="inline-block px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors font-medium"
            >
              Agregar Primer Comentario
            </Link>
          </div>
        ) : (
          <>
            <div className="mb-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Total: {comentarios.length} {comentarios.length === 1 ? 'comentario' : 'comentarios'}
              </p>
            </div>
            <div className="space-y-4">
              {comentarios.slice(0, 5).map((c: any) => (
                <div key={c.id} className="border dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {c.usuario_nombre || c.usuario_username || "Usuario"}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {c.usuario_rol && `${c.usuario_rol} • `}
                        {c.creado_en && new Date(c.creado_en).toLocaleString('es-CL')}
                        {c.editado && " (editado)"}
                      </p>
                    </div>
                  </div>
                  <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{c.contenido}</p>
                  {c.respuestas && c.respuestas.length > 0 && (
                    <div className="mt-3 ml-4 pl-4 border-l-2 border-gray-300 dark:border-gray-600">
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                        {c.respuestas.length} {c.respuestas.length === 1 ? 'respuesta' : 'respuestas'}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
            {comentarios.length > 5 && (
              <div className="mt-4 text-center">
                <Link
                  href={`/workorders/${id}/comentarios`}
                  className="text-green-600 dark:text-green-400 hover:underline font-medium"
                >
                  Ver {comentarios.length - 5} comentarios más →
                </Link>
              </div>
            )}
          </>
        )}
      </section>

      <div className="pt-4">
        <Link
          href="/workorders"
          className="text-blue-600 dark:text-blue-400 hover:underline"
        >
          ← Volver a órdenes de trabajo
        </Link>
      </div>
    </div>
  );
}

