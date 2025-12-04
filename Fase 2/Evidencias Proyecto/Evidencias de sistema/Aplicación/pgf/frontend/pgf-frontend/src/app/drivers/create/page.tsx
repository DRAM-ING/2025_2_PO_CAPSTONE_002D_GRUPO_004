"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import RoleGuard from "@/components/RoleGuard";
import { invalidateCache } from "@/lib/dataRefresh";

export default function CreateDriver() {
  const router = useRouter();
  const toast = useToast();
  const [form, setForm] = useState({
    nombre_completo: "",
    rut: "",
    telefono: "",
    email: "",
    zona: "",
    sucursal: "",
    vehiculo_asignado: "",
    km_mensual_promedio: "",
    activo: true,
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

    if (!form.nombre_completo.trim()) {
      newErrors.nombre_completo = "El nombre completo es requerido";
    }

    if (!form.rut.trim()) {
      newErrors.rut = "El RUT es requerido";
    } else {
      const rutClean = form.rut.replace(/[.-]/g, "").toUpperCase();
      if (!/^\d{7,9}[0-9K]$/.test(rutClean)) {
        newErrors.rut = "RUT inválido. Debe ser sin puntos ni guión (ej: 123456789 o 12345678K)";
      }
    }

    if (form.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      newErrors.email = "Email inválido";
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
      const payload: any = {
        ...form,
        vehiculo_asignado: form.vehiculo_asignado || null,
        km_mensual_promedio: form.km_mensual_promedio ? Number(form.km_mensual_promedio) : null,
      };

      const r = await fetch("/api/proxy/drivers/", {
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
        toast.error(data.detail || "Error al crear chofer");
        if (data.errors) {
          setErrors(data.errors);
        }
        return;
      }

      toast.success("Chofer creado correctamente");
      router.push("/drivers");
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al crear chofer");
    } finally {
      setLoading(false);
    }
  };

  const fields = [
    { key: "nombre_completo", label: "Nombre Completo", type: "text", required: true },
    { key: "rut", label: "RUT", type: "text", required: true, maxLength: 12 },
    { key: "telefono", label: "Teléfono", type: "text" },
    { key: "email", label: "Email", type: "email" },
    { key: "zona", label: "Zona", type: "text" },
    { key: "sucursal", label: "Sucursal", type: "text" },
    { key: "km_mensual_promedio", label: "KM Mensual Promedio", type: "number" },
  ];

  return (
    <RoleGuard allow={["ADMIN", "SUPERVISOR", "JEFE_TALLER"]}>
      <div className="p-8 max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">Nuevo Chofer</h1>

        <form onSubmit={submit} className="space-y-6 bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          {fields.map((field) => (
            <div key={field.key}>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {field.label} {field.required && <span className="text-red-500">*</span>}
              </label>
              {field.key === "rut" ? (
                <input
                  type="text"
                  value={form[field.key as keyof typeof form] as string}
                  onChange={(e) => {
                    let value = e.target.value.replace(/[^0-9kK]/gi, "").toUpperCase();
                    if (value.length > 10) value = value.slice(0, 10);
                    updateForm(field.key, value);
                  }}
                  maxLength={12}
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

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Vehículo Asignado
            </label>
            <select
              value={form.vehiculo_asignado}
              onChange={(e) => updateForm("vehiculo_asignado", e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="">Sin asignar</option>
              {vehiculos.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.patente} - {v.marca} {v.modelo}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="activo"
              checked={form.activo}
              onChange={(e) => updateForm("activo", e.target.checked)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="activo" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Activo
            </label>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium disabled:opacity-50"
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

