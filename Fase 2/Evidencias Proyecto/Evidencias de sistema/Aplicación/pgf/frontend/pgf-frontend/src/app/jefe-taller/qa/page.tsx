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
 * Vista de QA / Cierre para Jefe de Taller.
 * 
 * Muestra:
 * - Lista de OTs en estado EN_QA
 * - Evidencias subidas
 * - Checklist final
 * - Campo para resultado QA
 * - Botón para cerrar OT
 * 
 * Permisos:
 * - Solo JEFE_TALLER puede acceder
 */
export default function JefeTallerQAPage() {
  const router = useRouter();
  const toast = useToast();
  const { hasRole } = useAuth();

  const [otsQA, setOtsQA] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [otSeleccionada, setOtSeleccionada] = useState<any>(null);
  const [checklist, setChecklist] = useState({
    resultado: "OK",
    observaciones: "",
  });

  useEffect(() => {
    cargarOTs();
  }, []);

  const cargarOTs = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${ENDPOINTS.WORK_ORDERS}?estado=EN_QA`, {
        method: "GET",
        ...withSession(),
      });

      if (!response.ok) {
        throw new Error("Error al cargar OTs");
      }

      const data = await response.json();
      setOtsQA(data.results || data || []);
    } catch (error) {
      console.error("Error al cargar OTs:", error);
      toast.error("Error al cargar órdenes de trabajo");
    } finally {
      setLoading(false);
    }
  };

  const cargarOTDetalle = async (otId: string) => {
    try {
      const response = await fetch(`${ENDPOINTS.WORK_ORDERS}${otId}/`, {
        method: "GET",
        ...withSession(),
      });

      if (response.ok) {
        const data = await response.json();
        setOtSeleccionada(data);
        
        // Cargar checklist si existe
        if (data.checklists && data.checklists.length > 0) {
          const ultimoChecklist = data.checklists[data.checklists.length - 1];
          setChecklist({
            resultado: ultimoChecklist.resultado || "OK",
            observaciones: ultimoChecklist.observaciones || "",
          });
        }
      }
    } catch (error) {
      console.error("Error al cargar detalle:", error);
      toast.error("Error al cargar detalle de la OT");
    }
  };

  const handleAprobarQA = async (otId: string) => {
    try {
      // Crear o actualizar checklist
      const checklistResponse = await fetch(`${ENDPOINTS.WORK_ORDERS}${otId}/aprobar-qa/`, {
        method: "POST",
        ...withSession(),
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          resultado: checklist.resultado,
          observaciones: checklist.observaciones,
        }),
      });

      if (!checklistResponse.ok) {
        let errorMessage = "Error al aprobar QA";
        try {
          const error = await checklistResponse.json();
          errorMessage = error.detail || errorMessage;
        } catch {
          const errorText = await checklistResponse.text();
          errorMessage = errorText || errorMessage;
        }
        toast.error(errorMessage);
        return;
      }

      toast.success("QA aprobada. OT cerrada correctamente");
      setOtSeleccionada(null);
      await cargarOTs();
    } catch (error) {
      console.error("Error al aprobar QA:", error);
      toast.error("Error al aprobar QA");
    }
  };

  const handleRechazarQA = async (otId: string) => {
    try {
      const response = await fetch(`${ENDPOINTS.WORK_ORDERS}${otId}/rechazar-qa/`, {
        method: "POST",
        ...withSession(),
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          observaciones: checklist.observaciones,
        }),
      });

      if (!response.ok) {
        let errorMessage = "Error al rechazar QA";
        try {
          const error = await response.json();
          errorMessage = error.detail || errorMessage;
        } catch {
          const errorText = await response.text();
          errorMessage = errorText || errorMessage;
        }
        toast.error(errorMessage);
        return;
      }

      toast.success("QA rechazada. OT devuelta a ejecución");
      setOtSeleccionada(null);
      await cargarOTs();
    } catch (error) {
      console.error("Error al rechazar QA:", error);
      toast.error("Error al rechazar QA");
    }
  };

  return (
    <RoleGuard allow={["JEFE_TALLER", "ADMIN"]}>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Control de Calidad (QA)
          </h1>
          <Link
            href="/jefe-taller/dashboard"
            className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
          >
            ← Volver
          </Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Lista de OTs en QA */}
          <div className="lg:col-span-1">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  OTs en QA ({otsQA.length})
                </h2>
              </div>
              {loading ? (
                <div className="p-6 text-center">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
                </div>
              ) : otsQA.length === 0 ? (
                <div className="p-6 text-center text-gray-500 dark:text-gray-400">
                  No hay OTs en QA.
                </div>
              ) : (
                <div className="divide-y divide-gray-200 dark:divide-gray-700">
                  {otsQA.map((ot) => (
                    <button
                      key={ot.id}
                      onClick={() => cargarOTDetalle(ot.id)}
                      className={`w-full p-4 text-left hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors ${
                        otSeleccionada?.id === ot.id ? "bg-blue-50 dark:bg-blue-900/20" : ""
                      }`}
                    >
                      <div className="font-medium text-gray-900 dark:text-white">
                        OT #{ot.id.slice(0, 8)}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        {ot.vehiculo_patente || ot.vehiculo?.patente}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Detalle de OT Seleccionada */}
          <div className="lg:col-span-2">
            {otSeleccionada ? (
              <div className="space-y-6">
                {/* Información General */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
                    Información de la OT
                  </h2>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-sm text-gray-600 dark:text-gray-400">Vehículo:</span>
                      <p className="text-lg font-semibold text-gray-900 dark:text-white">
                        {otSeleccionada.vehiculo_patente || otSeleccionada.vehiculo?.patente}
                      </p>
                    </div>
                    <div>
                      <span className="text-sm text-gray-600 dark:text-gray-400">Mecánico:</span>
                      <p className="text-lg text-gray-900 dark:text-white">
                        {otSeleccionada.mecanico_nombre || "N/A"}
                      </p>
                    </div>
                    {otSeleccionada.motivo && (
                      <div className="col-span-2">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Motivo:</span>
                        <p className="text-sm text-gray-900 dark:text-white mt-1">
                          {otSeleccionada.motivo}
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Evidencias */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
                    Evidencias Subidas
                  </h2>
                  {otSeleccionada.evidencias && otSeleccionada.evidencias.length > 0 ? (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {otSeleccionada.evidencias.map((evidencia: any) => (
                        <div key={evidencia.id} className="border border-gray-200 dark:border-gray-600 rounded-lg p-2">
                          {evidencia.tipo === "FOTO" ? (
                            <img
                              src={evidencia.url}
                              alt={evidencia.descripcion}
                              className="w-full h-32 object-cover rounded"
                            />
                          ) : (
                            <div className="w-full h-32 bg-gray-100 dark:bg-gray-700 rounded flex items-center justify-center">
                              <span className="text-gray-500 dark:text-gray-400">{evidencia.tipo}</span>
                            </div>
                          )}
                          <p className="text-xs text-gray-600 dark:text-gray-400 mt-2 truncate">
                            {evidencia.descripcion || "Sin descripción"}
                          </p>
                          {evidencia.invalidado && (
                            <span className="text-xs text-red-600 dark:text-red-400">Invalidada</span>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 dark:text-gray-400">No hay evidencias subidas.</p>
                  )}
                </div>

                {/* Checklist Final */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
                    Checklist Final
                  </h2>
                  <div className="space-y-4">
                    <div>
                      <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                        Resultado QA
                      </label>
                      <select
                        value={checklist.resultado}
                        onChange={(e) => setChecklist({ ...checklist, resultado: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      >
                        <option value="OK">OK - Aprobado</option>
                        <option value="NO_OK">NO_OK - Requiere Corrección</option>
                      </select>
                    </div>
                    <div>
                      <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                        Observaciones
                      </label>
                      <textarea
                        value={checklist.observaciones}
                        onChange={(e) => setChecklist({ ...checklist, observaciones: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        rows={4}
                        placeholder="Observaciones sobre la calidad del trabajo..."
                      />
                    </div>
                    <div className="flex gap-3">
                      <button
                        onClick={() => handleAprobarQA(otSeleccionada.id)}
                        className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors font-medium"
                      >
                        Aprobar y Cerrar OT
                      </button>
                      <button
                        onClick={() => handleRechazarQA(otSeleccionada.id)}
                        className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors font-medium"
                      >
                        Rechazar (Retrabajo)
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 text-center">
                <p className="text-gray-500 dark:text-gray-400">
                  Selecciona una OT de la lista para ver los detalles y realizar QA.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </RoleGuard>
  );
}

