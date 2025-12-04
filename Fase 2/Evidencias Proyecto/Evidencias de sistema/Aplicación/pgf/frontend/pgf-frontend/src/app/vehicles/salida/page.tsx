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
 * Página para que el Guardia registre la salida de vehículos del taller.
 * 
 * Esta página permite:
 * - Ver lista de vehículos ingresados hoy
 * - Registrar salida de un vehículo
 * - Validar que todas las OTs estén cerradas
 * - Generar comprobante de salida
 * 
 * Permisos:
 * - Solo GUARDIA puede acceder
 */
export default function SalidaVehiculoPage() {
  const router = useRouter();
  const toast = useToast();
  const { hasRole } = useAuth();

  const [ingresos, setIngresos] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingList, setLoadingList] = useState(true);
  const [selectedIngreso, setSelectedIngreso] = useState<string | null>(null);
  const [form, setForm] = useState({
    observaciones_salida: "",
    kilometraje_salida: "",
  });

  const canAccess = hasRole(["GUARDIA", "ADMIN", "JEFE_TALLER"]);

  useEffect(() => {
    if (canAccess) {
      cargarIngresos();
    }
  }, [canAccess]);

  const cargarIngresos = async () => {
    setLoadingList(true);
    try {
      // Usar el nuevo endpoint que devuelve vehículos con OT cerradas (no solo del día)
      const response = await fetch(ENDPOINTS.VEHICLES_PENDIENTES_SALIDA, {
        method: "GET",
        ...withSession(),
      });

      if (!response.ok) {
        // Solo lanzar error para errores críticos (500+)
        if (response.status >= 500) {
          throw new Error("Error al cargar ingresos");
        }
        // Para 404 y otros, simplemente retornar array vacío sin mostrar alerta
        console.warn(`Respuesta HTTP ${response.status} - sin ingresos disponibles`);
        setIngresos([]);
        setLoadingList(false);
        return;
      }

      const data = await response.json();
      // El endpoint ya devuelve solo los pendientes con OT cerradas
      setIngresos(data.ingresos || []);
    } catch (error) {
      // Solo mostrar alerta para errores críticos
      if (error instanceof Error && error.message.includes("Error al cargar")) {
        console.error("Error crítico al cargar ingresos:", error);
        toast.error("Error al cargar la lista de ingresos");
      } else {
        console.warn("Sin ingresos disponibles o error menor:", error);
      }
    } finally {
      setLoadingList(false);
    }
  };

  const handleChange = (field: string, value: any) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleRegistrarSalida = async (ingresoId: string) => {
    setLoading(true);

    try {
      const response = await fetch(ENDPOINTS.VEHICLES_SALIDA, {
        method: "POST",
        ...withSession(),
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ingreso_id: ingresoId,
          observaciones_salida: form.observaciones_salida.trim() || "",
          kilometraje_salida: form.kilometraje_salida && form.kilometraje_salida.trim() 
            ? parseInt(form.kilometraje_salida) 
            : null,
        }),
      });

      const text = await response.text();
      
      // Si la respuesta está vacía pero el status es exitoso, considerar éxito
      if (response.ok && (!text || text.trim() === "" || text.trim() === "{}")) {
        toast.success("Salida registrada correctamente");
        setForm({
          observaciones_salida: "",
          kilometraje_salida: "",
        });
        setSelectedIngreso(null);
        await cargarIngresos();
        setLoading(false);
        return;
      }

      // Intentar parsear como JSON
      let data: any = {};
      try {
        if (text && text.trim() && text.trim() !== "{}") {
          data = JSON.parse(text);
        } else if (text && text.trim() === "{}") {
          // Si es un objeto vacío, puede ser una respuesta exitosa
          data = {};
        }
      } catch (e) {
        // Si no es JSON válido, puede ser HTML (página de error) o texto plano
        data = { 
          detail: text || "Error desconocido",
          raw: text.substring(0, 200), // Primeros 200 caracteres para debugging
          parseError: String(e)
        };
      }

      // Si la respuesta es exitosa y tiene datos, actualizar
      if (response.ok) {
        if (data && (data.id || Object.keys(data).length > 0)) {
          toast.success("Salida registrada correctamente");
          setForm({
            observaciones_salida: "",
            kilometraje_salida: "",
          });
          setSelectedIngreso(null);
          await cargarIngresos();
          setLoading(false);
          return;
        } else if (Object.keys(data).length === 0) {
          // Respuesta exitosa pero vacía, considerar éxito
          toast.success("Salida registrada correctamente");
          setForm({
            observaciones_salida: "",
            kilometraje_salida: "",
          });
          setSelectedIngreso(null);
          await cargarIngresos();
          setLoading(false);
          return;
        }
      }

      if (!response.ok) {
        // Construir mensaje de error más informativo
        let errorMessage = "Error al registrar salida";
        
        // Si data está vacío pero hay texto, intentar parsear de nuevo
        if (Object.keys(data).length === 0 && text && text.trim()) {
          try {
            const parsed = JSON.parse(text);
            if (parsed && typeof parsed === 'object') {
              data = parsed;
            }
          } catch {
            // Si no se puede parsear, usar el texto como mensaje
            data = { detail: text.substring(0, 200) };
          }
        }
        
        if (data.detail) {
          errorMessage = data.detail;
          // Si hay detalle de OTs activas, agregarlo al mensaje
          if (data.detalle) {
            errorMessage += ` - ${data.detalle}`;
          }
        } else if (data.message) {
          errorMessage = data.message;
        } else if (data.raw) {
          errorMessage = data.raw;
        } else if (text && text.trim()) {
          errorMessage = text.substring(0, 100);
        } else if (response.status === 403) {
          errorMessage = "No tiene permisos para registrar salidas";
        } else if (response.status === 400) {
          errorMessage = "Solicitud inválida. Verifique los datos.";
        } else if (response.status === 404) {
          errorMessage = "Ingreso no encontrado";
        } else if (response.status === 500) {
          errorMessage = "Error interno del servidor";
        } else {
          errorMessage = `Error ${response.status}: ${response.statusText || "Error desconocido"}`;
        }
        
        toast.error(errorMessage);
        
        // Log para debugging
        console.error("Error al registrar salida:", {
          status: response.status,
          statusText: response.statusText,
          url: ENDPOINTS.VEHICLES_SALIDA,
          data: data,
          text: text ? text.substring(0, 500) : "(vacío)",
          isEmpty: Object.keys(data).length === 0,
          responseType: response.headers.get("content-type"),
        });
        setLoading(false);
        return;
      }

      toast.success("Salida registrada correctamente");
      
      // Limpiar formulario
      setForm({
        observaciones_salida: "",
        kilometraje_salida: "",
      });
      setSelectedIngreso(null);

      // Recargar lista
      await cargarIngresos();
    } catch (error) {
      console.error("Error al registrar salida:", error);
      toast.error("Error al registrar la salida del vehículo");
    } finally {
      setLoading(false);
    }
  };

  if (!canAccess) {
    return (
      <RoleGuard allow={["GUARDIA", "ADMIN", "JEFE_TALLER"]}>
        <div></div>
      </RoleGuard>
    );
  }

  return (
    <RoleGuard allow={["GUARDIA", "ADMIN", "JEFE_TALLER"]}>
      <div className="p-6 max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Registrar Salida de Vehículo
          </h1>
          <div className="flex gap-2">
            <Link
              href="/vehicles/ingreso"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
            >
              Registrar Ingreso
            </Link>
            <Link
              href="/vehicles/ingresos-hoy"
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
            >
              Ver Lista del Día
            </Link>
            <Link
              href="/vehicles"
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
            >
              ← Volver
            </Link>
          </div>
        </div>

        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-6">
          <p className="text-sm text-yellow-800 dark:text-yellow-300">
            <strong>Importante:</strong> Solo se puede registrar la salida de vehículos que tienen 
            todas sus OTs cerradas. Verifique el estado de las OTs antes de registrar la salida.
          </p>
        </div>

        {/* Lista de Ingresos Pendientes */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Vehículos Pendientes de Salida (OT Cerradas)
            </h2>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              Se muestran todos los vehículos con todas sus OTs cerradas o anuladas, listos para salir del taller.
            </p>
          </div>

          {loadingList ? (
            <div className="p-6 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando ingresos...</p>
            </div>
          ) : ingresos.length === 0 ? (
            <div className="p-6 text-center text-gray-500 dark:text-gray-400">
              No hay vehículos pendientes de salida. Todos los vehículos con OT cerradas ya han salido o aún tienen OTs activas.
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {ingresos.map((ingreso) => (
                <div
                  key={ingreso.id}
                  className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-4 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {ingreso.vehiculo_detalle?.patente || ingreso.vehiculo?.patente || ingreso.vehiculo_patente || "N/A"}
                        </h3>
                        <span className="px-2 py-1 text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded">
                          Ingreso: {new Date(ingreso.fecha_ingreso).toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600 dark:text-gray-400">
                        <div>
                          <span className="font-medium">Marca:</span> {ingreso.vehiculo_detalle?.marca_nombre || ingreso.vehiculo?.marca_nombre || ingreso.vehiculo?.marca?.nombre || "N/A"}
                        </div>
                        <div>
                          <span className="font-medium">Modelo:</span> {ingreso.vehiculo_detalle?.modelo || ingreso.vehiculo?.modelo || "N/A"}
                        </div>
                        <div>
                          <span className="font-medium">Tipo:</span> {ingreso.vehiculo_detalle?.tipo || ingreso.vehiculo?.tipo || "N/A"}
                        </div>
                        <div>
                          <span className="font-medium">Año:</span> {ingreso.vehiculo_detalle?.anio || ingreso.vehiculo?.anio || "N/A"}
                        </div>
                        <div>
                          <span className="font-medium">Kilometraje Ingreso:</span> {ingreso.kilometraje || "N/A"}
                        </div>
                        <div>
                          <span className="font-medium">Guardia Ingreso:</span> {ingreso.guardia_detalle?.nombre_completo || ingreso.guardia_nombre || ingreso.guardia?.username || "N/A"}
                        </div>
                        <div>
                          <span className="font-medium">Fecha Ingreso:</span> {new Date(ingreso.fecha_ingreso).toLocaleDateString()}
                        </div>
                      </div>
                      {ingreso.observaciones && (
                        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                          <span className="font-medium">Observaciones:</span> {ingreso.observaciones}
                        </p>
                      )}
                    </div>
                    <div className="ml-4">
                      <button
                        onClick={() => setSelectedIngreso(selectedIngreso === ingreso.id ? null : ingreso.id)}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
                      >
                        {selectedIngreso === ingreso.id ? "Cancelar" : "Registrar Salida"}
                      </button>
                    </div>
                  </div>

                  {/* Formulario de Salida (expandible) */}
                  {selectedIngreso === ingreso.id && (
                    <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600">
                      <h4 className="font-semibold text-gray-900 dark:text-white mb-4">
                        Información de Salida
                      </h4>
                      <div className="space-y-4">
                        <div>
                          <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                            Observaciones de Salida
                          </label>
                          <textarea
                            value={form.observaciones_salida}
                            onChange={(e) => handleChange("observaciones_salida", e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            rows={3}
                            placeholder="Observaciones sobre la salida del vehículo..."
                          />
                        </div>
                        <div>
                          <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                            Kilometraje de Salida
                          </label>
                          <input
                            type="number"
                            value={form.kilometraje_salida}
                            onChange={(e) => handleChange("kilometraje_salida", e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            placeholder="50000"
                            min="0"
                          />
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleRegistrarSalida(ingreso.id)}
                            disabled={loading}
                            className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {loading ? "Registrando..." : "Confirmar Salida"}
                          </button>
                          <button
                            onClick={() => {
                              setSelectedIngreso(null);
                              setForm({ observaciones_salida: "", kilometraje_salida: "" });
                            }}
                            className="px-4 py-2 bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors font-medium"
                          >
                            Cancelar
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </RoleGuard>
  );
}

