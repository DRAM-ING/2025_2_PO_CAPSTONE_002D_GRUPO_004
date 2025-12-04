"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ENDPOINTS } from "@/lib/constants";
import { withSession } from "@/lib/api.client";
import { useToast } from "@/components/ToastContainer";
import { invalidateCache } from "@/lib/dataRefresh";

export default function EditItem() {
  const params = useParams();
  const otId = params.id as string;
  const itemId = params.itemId as string;

  const router = useRouter();
  const toast = useToast();

  const [form, setForm] = useState<any>(null);
  const [repuestos, setRepuestos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    const load = async () => {
      try {
        // Cargar item
        const r = await fetch(`${ENDPOINTS.WORK_ITEMS}${itemId}/`, withSession());
        if (!r.ok) {
          toast.error("Error al cargar el ítem");
          router.push(`/workorders/${otId}/items`);
          return;
        }
        const j = await r.json();
        setForm(j);

        // Cargar repuestos
        const repuestosRes = await fetch("/api/proxy/inventory/repuestos/?activo=true", {
          credentials: "include",
        });
        if (repuestosRes.ok) {
          const repuestosData = await repuestosRes.json();
          setRepuestos(repuestosData.results || repuestosData || []);
        }
      } catch (error) {
        console.error("Error:", error);
        toast.error("Error al cargar el ítem");
        router.push(`/workorders/${otId}/items`);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [itemId, otId, router, toast]);

  const handleChange = (name: string, value: any) => {
    setForm((prev: any) => {
      const newForm = { ...prev, [name]: value };
      
      // Si se selecciona un repuesto, auto-completar descripción y costo
      if (name === "repuesto" && value) {
        const selectedRepuesto = repuestos.find((r) => r.id === value);
        if (selectedRepuesto) {
          newForm.descripcion = selectedRepuesto.nombre;
          newForm.costo_unitario = selectedRepuesto.precio_referencia || 0;
        }
      } else if (name === "tipo" && value !== "REPUESTO") {
        // Si cambia a SERVICIO, limpiar repuesto
        newForm.repuesto = null;
      }
      
      return newForm;
    });
    
    // Limpiar errores
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const save = async () => {
    setErrors({});
    setSaving(true);

    // Validación básica
    const newErrors: Record<string, string> = {};
    if (!form.descripcion?.trim()) {
      newErrors.descripcion = "La descripción es obligatoria";
    }
    if (form.cantidad <= 0) {
      newErrors.cantidad = "La cantidad debe ser mayor a 0";
    }
    if (form.costo_unitario < 0) {
      newErrors.costo_unitario = "El costo no puede ser negativo";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      toast.error("Por favor corrige los errores en el formulario");
      setSaving(false);
      return;
    }

    try {
      // Preparar datos para enviar
      const dataToSend: any = {
        tipo: form.tipo,
        descripcion: form.descripcion,
        cantidad: form.cantidad,
        costo_unitario: form.costo_unitario,
      };
      
      // Si es REPUESTO y tiene repuesto seleccionado, incluirlo
      if (form.tipo === "REPUESTO" && form.repuesto) {
        dataToSend.repuesto = form.repuesto;
      } else if (form.tipo === "REPUESTO" && !form.repuesto) {
        // Si es REPUESTO pero no tiene repuesto, limpiar el campo
        dataToSend.repuesto = null;
      }

      const r = await fetch(`${ENDPOINTS.WORK_ITEMS}${itemId}/`, {
        method: "PUT",
        ...withSession(),
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dataToSend),
      });

      const text = await r.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        data = { detail: text || "Error desconocido" };
      }

      if (!r.ok) {
        toast.error(data.detail || "Error al guardar el ítem");
        if (data.errors) {
          setErrors(data.errors);
        }
        return;
      }

      toast.success("Ítem actualizado correctamente");
      invalidateCache("WORKORDERS");
      router.refresh();
      router.push(`/workorders/${otId}/items`);
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al guardar el ítem");
    } finally {
      setSaving(false);
    }
  };

  if (loading || !form) {
    return (
      <div className="p-6 flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Editar Ítem</h1>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-4">
        <div>
          <label className="block mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Tipo *</label>
          <select
            value={form.tipo}
            onChange={(e) => handleChange("tipo", e.target.value)}
            className={`input w-full ${errors.tipo ? "border-red-500" : ""}`}
          >
            <option value="SERVICIO">Servicio (Mano de obra)</option>
            <option value="REPUESTO">Repuesto</option>
          </select>
          {errors.tipo && (
            <p className="mt-1 text-xs text-red-600 dark:text-red-400">{errors.tipo}</p>
          )}
        </div>

        {form.tipo === "REPUESTO" && (
          <div>
            <label className="block mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Repuesto</label>
            <select
              value={form.repuesto || ""}
              onChange={(e) => handleChange("repuesto", e.target.value)}
              className="input w-full"
            >
              <option value="">Seleccionar repuesto</option>
              {repuestos.map((repuesto) => (
                <option key={repuesto.id} value={repuesto.id}>
                  {repuesto.nombre} ({repuesto.codigo})
                </option>
              ))}
            </select>
          </div>
        )}

        <div>
          <label className="block mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Descripción *</label>
          <input
            value={form.descripcion}
            onChange={(e) => handleChange("descripcion", e.target.value)}
            className={`input w-full ${errors.descripcion ? "border-red-500" : ""}`}
            placeholder="Descripción del item..."
            disabled={form.tipo === "REPUESTO" && form.repuesto !== null}
          />
          {errors.descripcion && (
            <p className="mt-1 text-xs text-red-600 dark:text-red-400">{errors.descripcion}</p>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Cantidad *</label>
            <input
              type="number"
              min="1"
              value={form.cantidad}
              onChange={(e) => handleChange("cantidad", Number(e.target.value))}
              className={`input w-full ${errors.cantidad ? "border-red-500" : ""}`}
            />
            {errors.cantidad && (
              <p className="mt-1 text-xs text-red-600 dark:text-red-400">{errors.cantidad}</p>
            )}
          </div>

          <div>
            <label className="block mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">
              {form.tipo === "SERVICIO" ? "Costo por hora *" : "Costo unitario *"}
            </label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={form.costo_unitario}
              onChange={(e) => handleChange("costo_unitario", Number(e.target.value))}
              className={`input w-full ${errors.costo_unitario ? "border-red-500" : ""}`}
              disabled={form.tipo === "REPUESTO" && form.repuesto !== null}
            />
            {errors.costo_unitario && (
              <p className="mt-1 text-xs text-red-600 dark:text-red-400">{errors.costo_unitario}</p>
            )}
          </div>
        </div>

        {form.tipo === "SERVICIO" && (
          <p className="text-xs text-gray-500 dark:text-gray-400">
            El costo por hora se multiplicará por el tiempo de ejecución del mecánico.
          </p>
        )}
      </div>

      <div className="flex gap-4">
        <button
          type="button"
          onClick={() => router.back()}
          className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
        >
          Cancelar
        </button>
        <button
          onClick={save}
          disabled={saving}
          className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? "Guardando..." : "Guardar cambios"}
        </button>
      </div>
    </div>
  );
}
