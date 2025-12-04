"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import { validateVehicle, normalizarPatente } from "@/lib/validations";
import { useAuth } from "@/store/auth";
import { handleApiError, getRoleHomePage } from "@/lib/permissions";
import { invalidateCache } from "@/lib/dataRefresh";

interface Marca {
  id: number;
  nombre: string;
  activa: boolean;
}

export default function EditVehicle() {
  const router = useRouter();
  const params = useParams();
  const id = params?.id as string;
  const toast = useToast();
  const { hasRole, user } = useAuth();
  
  // Verificar permisos: ADMIN, JEFE_TALLER, COORDINADOR_ZONA pueden editar
  const canEdit = hasRole(["ADMIN", "JEFE_TALLER", "COORDINADOR_ZONA"]);

  const [form, setForm] = useState<any>(null);
  const [marcas, setMarcas] = useState<Marca[]>([]);
  const [loadingMarcas, setLoadingMarcas] = useState(true);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    const load = async () => {
      try {
        const r = await fetch(`/api/proxy/vehicles/${id}/`, {
          credentials: "include",
        });
        
        if (!r.ok) {
          toast.error("Error al cargar el vehículo");
          router.push("/vehicles");
          return;
        }
        
        const text = await r.text();
        if (!text || text.trim() === "") {
          toast.error("Vehículo no encontrado");
          router.push("/vehicles");
          return;
        }
        
        const data = JSON.parse(text);
        setForm({ 
          ...data, 
          marca: data.marca || (data.marca_id || ""), // Usar marca_id si existe, sino marca
          anio: String(data.anio || ""),
          estado: data.estado || "ACTIVO", // Asegurar que el estado tenga un valor por defecto
          tipo: data.tipo || "" // Asegurar que el tipo esté presente
        });
      } catch (e) {
        console.error("Error:", e);
        toast.error("Error al cargar el vehículo");
        router.push("/vehicles");
      } finally {
        setLoading(false);
      }
    };
    
    if (id && canEdit) load();
    else if (!canEdit) {
      toast.error("Permisos insuficientes. No tiene acceso para editar vehículos.");
      setTimeout(() => {
        router.push(getRoleHomePage(user?.rol));
      }, 2000);
    }
  }, [id, router, toast, canEdit, user?.rol]);

  useEffect(() => {
    const cargarMarcas = async () => {
      try {
        setLoadingMarcas(true);
        const r = await fetch("/api/proxy/vehicles/marcas", {
          credentials: "include",
        });
        if (r.ok) {
          const text = await r.text();
          if (!text || text.trim() === "") {
            console.warn("Respuesta vacía al cargar marcas");
            setMarcas([]);
            return;
          }
          const data = JSON.parse(text);
          // Manejar tanto array directo como objeto con results
          const marcasData = Array.isArray(data) ? data : (data.results || data || []);
          setMarcas(marcasData);
          if (marcasData.length === 0) {
            console.warn("No se encontraron marcas activas");
          }
        } else {
          console.error("Error al cargar marcas:", r.status, r.statusText);
          toast.error("Error al cargar marcas");
        }
      } catch (error) {
        console.error("Error al cargar marcas:", error);
        toast.error("Error al cargar marcas");
      } finally {
        setLoadingMarcas(false);
      }
    };
    cargarMarcas();
  }, []); // toast es estable de Zustand, no necesita estar en dependencias

  const update = (k: string, v: string) => {
    // Normalizar patente automáticamente mientras el usuario escribe
    if (k === "patente") {
      // Permitir escribir con guiones, pero normalizar al formato estándar
      // Convertir a mayúsculas y permitir guiones temporalmente
      const valorNormalizado = v.toUpperCase().replace(/\s/g, "");
      setForm({ ...form, [k]: valorNormalizado });
    } else {
      setForm({ ...form, [k]: v });
    }
    if (errors[k]) {
      setErrors({ ...errors, [k]: "" });
    }
  };

  async function save() {
    // Validar formulario
    const validation = validateVehicle(form);
    if (!validation.isValid) {
      setErrors(validation.errors);
      toast.error("Por favor corrige los errores en el formulario");
      return;
    }

    setSaving(true);
    setErrors({});

    try {
      const r = await fetch(`/api/proxy/vehicles/${id}/`, {
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...form,
          patente: normalizarPatente(form.patente) || form.patente.replace(/-/g, "").toUpperCase(), // Normalizar antes de enviar
          marca: Number(form.marca), // Enviar el ID de la marca
          anio: Number(form.anio),
          tipo: form.tipo || undefined,
        }),
      });

      const text = await r.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        data = { detail: text || "Error desconocido" };
      }

      if (!r.ok) {
        if (r.status === 403) {
          toast.error("Permisos insuficientes. No tiene acceso para editar vehículos.");
          setTimeout(() => {
            router.push(getRoleHomePage(user?.rol));
          }, 2000);
          return;
        }
        handleApiError({ status: r.status, detail: data.detail }, router, toast, user?.rol);
        if (data.errors) {
          setErrors(data.errors);
        }
        return;
      }

      toast.success("Vehículo actualizado correctamente");
      invalidateCache("VEHICLES");
      router.refresh();
      router.push("/vehicles");
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al actualizar el vehículo");
    } finally {
      setSaving(false);
    }
  }

  if (loading || !form) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando...</p>
        </div>
      </div>
    );
  }

  const estados = [
    { value: "ACTIVO", label: "Activo" },
    { value: "EN_ESPERA", label: "En Espera" },
    { value: "EN_MANTENIMIENTO", label: "En Mantenimiento" },
    { value: "BAJA", label: "Baja" },
  ];

  const tipos = [
    { value: "", label: "Seleccione un tipo (opcional)" },
    { value: "ELECTRICO", label: "Eléctrico" },
    { value: "DIESEL", label: "Diésel" },
    { value: "UTILITARIO", label: "Utilitario" },
    { value: "REPARTO", label: "Reparto" },
    { value: "VENTAS", label: "Ventas" },
    { value: "RESPALDO", label: "Respaldo" },
  ];

  const fields = [
    { key: "patente", label: "Patente", placeholder: "ABC123 o ABC-123", type: "text" },
    { key: "modelo", label: "Modelo", placeholder: "Ej: Corolla", type: "text" },
    { key: "anio", label: "Año", placeholder: "Ej: 2020", type: "number" },
  ];

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">Editar Vehículo</h1>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-6">
        {/* Campo Patente */}
        <div>
          <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
            Patente *
          </label>
          <input
            type="text"
            placeholder="ABC123 o ABC-123"
            className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white dark:border-gray-600 transition-all ${
              errors.patente ? "border-red-500" : "border-gray-300"
            }`}
            value={(form as any).patente || ""}
            onChange={(e) => update("patente", e.target.value)}
          />
          {errors.patente && (
            <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.patente}</p>
          )}
        </div>

        {/* Campo Marca - Select */}
        <div>
          <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
            Marca *
          </label>
          <select
            className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white dark:border-gray-600 transition-all ${
              errors.marca ? "border-red-500" : "border-gray-300"
            }`}
            value={(form as any).marca || ""}
            onChange={(e) => update("marca", e.target.value)}
            disabled={loadingMarcas}
          >
            <option value="">{loadingMarcas ? "Cargando marcas..." : "Seleccione una marca"}</option>
            {marcas.map((marca) => (
              <option key={marca.id} value={marca.id}>
                {marca.nombre}
              </option>
            ))}
          </select>
          {errors.marca && (
            <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.marca}</p>
          )}
        </div>

        {/* Resto de campos */}
        {fields.filter(f => f.key !== "patente").map((field) => (
          <div key={field.key}>
            <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
              {field.label} *
            </label>
            <input
              type={field.type}
              placeholder={field.placeholder}
              className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white dark:border-gray-600 transition-all ${
                errors[field.key] ? "border-red-500" : "border-gray-300"
              }`}
              value={(form as any)[field.key] || ""}
              onChange={(e) => update(field.key, e.target.value)}
            />
            {errors[field.key] && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors[field.key]}</p>
            )}
          </div>
        ))}

        {/* Campo Tipo de Vehículo */}
        <div>
          <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
            Tipo de Vehículo
          </label>
          <select
            className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white dark:border-gray-600 transition-all ${
              errors.tipo ? "border-red-500" : "border-gray-300"
            }`}
            value={(form as any).tipo || ""}
            onChange={(e) => update("tipo", e.target.value)}
          >
            {tipos.map((tipo) => (
              <option key={tipo.value} value={tipo.value}>
                {tipo.label}
              </option>
            ))}
          </select>
          {errors.tipo && (
            <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.tipo}</p>
          )}
        </div>

        {/* Campo de Estado */}
        <div>
          <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
            Estado *
          </label>
          <select
            className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white dark:border-gray-600 transition-all ${
              errors.estado ? "border-red-500" : "border-gray-300"
            }`}
            value={(form as any).estado || "ACTIVO"}
            onChange={(e) => update("estado", e.target.value)}
          >
            {estados.map((estado) => (
              <option key={estado.value} value={estado.value}>
                {estado.label}
              </option>
            ))}
          </select>
          {errors.estado && (
            <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.estado}</p>
          )}
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Estado actual del vehículo en el sistema
          </p>
        </div>

        <div className="flex gap-4 pt-4">
          <button
            type="button"
            onClick={() => router.back()}
            className="flex-1 px-4 py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={save}
            disabled={saving}
            className="flex-1 px-4 py-3 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ backgroundColor: '#003DA5' }}
          >
            {saving ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Guardando...
              </span>
            ) : (
              "Guardar Cambios"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
