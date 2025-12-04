"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import RoleGuard from "@/components/RoleGuard";
import { formatError, extractFieldErrors } from "@/lib/errorFormatter";
import { useAuth } from "@/store/auth";
import { invalidateCache } from "@/lib/dataRefresh";

export default function CreateScheduling() {
  const router = useRouter();
  const toast = useToast();
  const { user } = useAuth();
  const [form, setForm] = useState({
    vehiculo: "",
    fecha_programada: "",
    motivo: "",
    tipo_mantenimiento: "PREVENTIVO",
    zona: "",
    observaciones: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [vehiculos, setVehiculos] = useState<any[]>([]);

  useEffect(() => {
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
    loadVehicles();
  }, []);

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
    } else {
      const fecha = new Date(form.fecha_programada);
      if (fecha < new Date()) {
        newErrors.fecha_programada = "La fecha no puede ser en el pasado";
      }
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

      const r = await fetch("/api/proxy/scheduling/agendas/", {
        method: "POST",
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
        // Formatear error de manera amigable
        const friendlyError = formatError(data);
        toast.error(friendlyError);
        
        // Extraer errores por campo para mostrar en el formulario
        const fieldErrors = extractFieldErrors(data);
        if (Object.keys(fieldErrors).length > 0) {
          setErrors(fieldErrors);
        } else if (data.errors) {
          setErrors(data.errors);
        }
        
        // Si es un error de permisos, mostrar mensaje más específico
        if (r.status === 403 || friendlyError.toLowerCase().includes("permiso") || friendlyError.toLowerCase().includes("coordinador")) {
          if (user?.rol !== "COORDINADOR_ZONA") {
            toast.error("Solo los coordinadores de zona pueden agendar citas al taller. Si necesita agendar una cita, contacte a un coordinador de zona.");
          }
        }
        
        return;
      }

      toast.success("Programación creada correctamente");
      invalidateCache("SCHEDULING");
      router.refresh();
      router.push("/scheduling");
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al crear programación");
    } finally {
      setLoading(false);
    }
  };

  const fields = [
    { key: "motivo", label: "Motivo", type: "textarea", required: true },
    { key: "zona", label: "Zona", type: "text" },
    { key: "observaciones", label: "Observaciones", type: "textarea" },
  ];

  return (
    <RoleGuard allow={["ADMIN", "SUPERVISOR", "COORDINADOR_ZONA"]}>
      <div className="p-8 max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">Nueva Programación</h1>

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

          {fields.map((field) => (
            <div key={field.key}>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {field.label} {field.required && <span className="text-red-500">*</span>}
              </label>
              {field.type === "textarea" ? (
                <textarea
                  value={form[field.key as keyof typeof form] as string}
                  onChange={(e) => updateForm(field.key, e.target.value)}
                  rows={field.key === "motivo" ? 4 : 3}
                  className={`w-full px-3 py-2 border rounded-lg ${
                    errors[field.key] ? "border-red-500" : "border-gray-300 dark:border-gray-600"
                  } bg-white dark:bg-gray-700 text-gray-900 dark:text-white`}
                  required={field.required}
                />
              ) : (
                <input
                  type={field.type}
                  value={form[field.key as keyof typeof form] as string}
                  onChange={(e) => updateForm(field.key, e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg ${
                    errors[field.key] ? "border-red-500" : "border-gray-300 dark:border-gray-600"
                  } bg-white dark:bg-gray-700 text-gray-900 dark:text-white`}
                  required={field.required}
                />
              )}
              {errors[field.key] && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors[field.key]}</p>
              )}
            </div>
          ))}

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

