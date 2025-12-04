"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import RoleGuard from "@/components/RoleGuard";
import { invalidateCache } from "@/lib/dataRefresh";

export default function EditScheduling() {
  const params = useParams();
  const id = params?.id as string;
  const router = useRouter();
  const toast = useToast();
  const [form, setForm] = useState({
    vehiculo: "",
    fecha_programada: "",
    motivo: "",
    tipo_mantenimiento: "PREVENTIVO",
    zona: "",
    observaciones: "",
    estado: "PROGRAMADA",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [vehiculos, setVehiculos] = useState<any[]>([]);

  useEffect(() => {
    const load = async () => {
      try {
        const r = await fetch(`/api/proxy/scheduling/agendas/${id}/`, {
          credentials: "include",
        });
        
        if (!r.ok) {
          toast.error("Error al cargar programación");
          router.push("/scheduling");
          return;
        }
        
        const data = await r.json();
        // Formatear fecha para input datetime-local
        const fecha = data.fecha_programada ? new Date(data.fecha_programada).toISOString().slice(0, 16) : "";
        
        setForm({
          vehiculo: data.vehiculo?.id || "",
          fecha_programada: fecha,
          motivo: data.motivo || "",
          tipo_mantenimiento: data.tipo_mantenimiento || "PREVENTIVO",
          zona: data.zona || "",
          observaciones: data.observaciones || "",
          estado: data.estado || "PROGRAMADA",
        });
      } catch (e) {
        console.error("Error:", e);
        toast.error("Error al cargar programación");
      } finally {
        setLoadingData(false);
      }
    };

    const loadVehicles = async () => {
      try {
        const r = await fetch("/api/proxy/vehicles/", { credentials: "include" });
        if (r.ok) {
          const data = await r.json();
          setVehiculos(data.results || data || []);
        }
      } catch (error) {
        console.error("Error cargando vehículos:", error);
      }
    };

    if (id) {
      load();
      loadVehicles();
    }
  }, [id, router, toast]);

  const updateForm = (k: string, v: any) => {
    setForm({ ...form, [k]: v });
    if (errors[k]) {
      setErrors({ ...errors, [k]: "" });
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!form.vehiculo) {
      newErrors.vehiculo = "El vehículo es requerido";
    }

    if (!form.fecha_programada) {
      newErrors.fecha_programada = "La fecha programada es requerida";
    }

    if (!form.motivo.trim()) {
      newErrors.motivo = "El motivo es requerido";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      toast.error("Por favor corrige los errores en el formulario");
      return;
    }

    setLoading(true);

    try {
      const payload = {
        ...form,
        fecha_programada: form.fecha_programada,
      };

      const r = await fetch(`/api/proxy/scheduling/agendas/${id}/`, {
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const text = await r.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        data = { detail: text || "Error desconocido" };
      }

      if (!r.ok) {
        toast.error(data.detail || "Error al actualizar programación");
        if (data.errors) {
          setErrors(data.errors);
        }
        return;
      }

      toast.success("Programación actualizada correctamente");
      router.push(`/scheduling/${id}`);
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al actualizar programación");
    } finally {
      setLoading(false);
    }
  };

  if (loadingData) {
    return (
      <div className="p-8 max-w-3xl mx-auto">
        <div className="text-center">Cargando...</div>
      </div>
    );
  }

  return (
    <RoleGuard allow={["ADMIN", "SUPERVISOR", "COORDINADOR_ZONA"]}>
      <div className="p-8 max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">Editar Programación</h1>

        <form onSubmit={submit} className="space-y-6 bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Vehículo <span className="text-red-500">*</span>
            </label>
            <select
              value={form.vehiculo}
              onChange={(e) => updateForm("vehiculo", e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg ${
                errors.vehiculo ? "border-red-500" : "border-gray-300 dark:border-gray-600"
              } bg-white dark:bg-gray-700 text-gray-900 dark:text-white`}
              required
            >
              <option value="">Seleccionar vehículo...</option>
              {vehiculos.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.patente} - {v.marca} {v.modelo}
                </option>
              ))}
            </select>
            {errors.vehiculo && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.vehiculo}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Fecha y Hora Programada <span className="text-red-500">*</span>
            </label>
            <input
              type="datetime-local"
              value={form.fecha_programada}
              onChange={(e) => updateForm("fecha_programada", e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg ${
                errors.fecha_programada ? "border-red-500" : "border-gray-300 dark:border-gray-600"
              } bg-white dark:bg-gray-700 text-gray-900 dark:text-white`}
              required
            />
            {errors.fecha_programada && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.fecha_programada}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Tipo de Mantenimiento
            </label>
            <select
              value={form.tipo_mantenimiento}
              onChange={(e) => updateForm("tipo_mantenimiento", e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="PREVENTIVO">Preventivo</option>
              <option value="CORRECTIVO">Correctivo</option>
              <option value="INSPECCION">Inspección</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Estado
            </label>
            <select
              value={form.estado}
              onChange={(e) => updateForm("estado", e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="PROGRAMADA">Programada</option>
              <option value="CONFIRMADA">Confirmada</option>
              <option value="EN_PROCESO">En Proceso</option>
              <option value="COMPLETADA">Completada</option>
              <option value="CANCELADA">Cancelada</option>
              <option value="REPROGRAMADA">Reprogramada</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Motivo <span className="text-red-500">*</span>
            </label>
            <textarea
              value={form.motivo}
              onChange={(e) => updateForm("motivo", e.target.value)}
              rows={4}
              className={`w-full px-3 py-2 border rounded-lg ${
                errors.motivo ? "border-red-500" : "border-gray-300 dark:border-gray-600"
              } bg-white dark:bg-gray-700 text-gray-900 dark:text-white`}
              required
            />
            {errors.motivo && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.motivo}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Zona
            </label>
            <input
              type="text"
              value={form.zona}
              onChange={(e) => updateForm("zona", e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Observaciones
            </label>
            <textarea
              value={form.observaciones}
              onChange={(e) => updateForm("observaciones", e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 text-white rounded-lg transition-colors font-medium disabled:opacity-50"
              style={{ backgroundColor: '#003DA5' }}
            >
              {loading ? "Guardando..." : "Guardar"}
            </button>
            <button
              type="button"
              onClick={() => router.back()}
              className="px-6 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 rounded-lg transition-colors"
            >
              Cancelar
            </button>
          </div>
        </form>
      </div>
    </RoleGuard>
  );
}

