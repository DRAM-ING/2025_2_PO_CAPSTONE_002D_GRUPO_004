"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";
import RoleGuard from "@/components/RoleGuard";
import { ENDPOINTS } from "@/lib/constants";
import Link from "next/link";
import { invalidateCache } from "@/lib/dataRefresh";

export default function CreateSolicitudRepuesto() {
  const router = useRouter();
  const toast = useToast();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [repuestos, setRepuestos] = useState<any[]>([]);
  const [ots, setOts] = useState<any[]>([]);
  const [form, setForm] = useState({
    ot: "",
    repuesto: "",
    cantidad_solicitada: 1,
    motivo: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    loadRepuestos();
    loadOTs();
  }, []);

  const loadRepuestos = async () => {
    try {
      const response = await fetch(ENDPOINTS.INVENTORY_REPUESTOS, {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        setRepuestos(Array.isArray(data) ? data : data.results || []);
      }
    } catch (error) {
      console.error("Error loading repuestos:", error);
    }
  };

  const loadOTs = async () => {
    try {
      // Para mecánicos, el backend filtra automáticamente por mecanico=user en get_queryset
      // No necesitamos enviar el parámetro mecanico, solo el estado
      if (user?.rol === "MECANICO") {
        // Cargar OTs en ejecución (el backend ya filtra por mecanico=user automáticamente)
        const params = new URLSearchParams();
        params.append("estado", "EN_EJECUCION");
        
        const url = `/api/proxy/work/ordenes/?${params.toString()}`;
        const response = await fetch(url, {
          credentials: "include",
        });
        
        if (response.ok) {
          const data = await response.json();
          const ots = Array.isArray(data) ? data : data.results || [];
          setOts(ots);
          console.log(`✅ Cargadas ${ots.length} OTs para mecánico`);
        } else {
          console.error("Error loading OTs:", response.status, response.statusText);
          const errorText = await response.text().catch(() => "");
          console.error("Error response:", errorText);
          toast.error("Error al cargar órdenes de trabajo");
        }
      } else {
        // Para otros roles, cargar OTs activas (múltiples estados)
        const estados = ["ABIERTA", "EN_DIAGNOSTICO", "EN_EJECUCION", "EN_PAUSA"];
        let allOts: any[] = [];
        const existingIds = new Set<string>();
        
        // Cargar OTs de cada estado y combinar
        for (const estado of estados) {
          const params = new URLSearchParams();
          params.append("estado", estado);
          const url = `/api/proxy/work/ordenes/?${params.toString()}`;
          
          try {
            const response = await fetch(url, { credentials: "include" });
            if (response.ok) {
              const data = await response.json();
              const ots = Array.isArray(data) ? data : data.results || [];
              // Agregar solo OTs que no estén ya en la lista
              ots.forEach((ot: any) => {
                if (!existingIds.has(ot.id)) {
                  allOts.push(ot);
                  existingIds.add(ot.id);
                }
              });
            }
          } catch (err) {
            console.error(`Error cargando OTs con estado ${estado}:`, err);
          }
        }
        
        setOts(allOts);
        console.log(`✅ Cargadas ${allOts.length} OTs activas para ${user?.rol}`);
      }
    } catch (error) {
      console.error("Error loading OTs:", error);
      toast.error("Error al cargar órdenes de trabajo");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrors({});

    try {
      // Validaciones
      if (!form.ot) {
        setErrors({ ot: "La OT es obligatoria" });
        toast.error("Por favor selecciona una OT");
        setLoading(false);
        return;
      }

      if (!form.repuesto) {
        setErrors({ repuesto: "El repuesto es obligatorio" });
        toast.error("Por favor selecciona un repuesto");
        setLoading(false);
        return;
      }

      if (form.cantidad_solicitada < 1) {
        setErrors({ cantidad_solicitada: "La cantidad debe ser mayor a 0" });
        toast.error("La cantidad debe ser mayor a 0");
        setLoading(false);
        return;
      }

      const response = await fetch(ENDPOINTS.INVENTORY_SOLICITUDES, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(form),
      });

      const text = await response.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        data = { detail: text || "Error desconocido" };
      }

      if (!response.ok) {
        if (data.errors) {
          setErrors(data.errors);
        }
        toast.error(data.detail || "Error al crear solicitud");
        setLoading(false);
        return;
      }

      toast.success("Solicitud creada correctamente");
      invalidateCache("INVENTORY");
      router.refresh();
      router.push("/inventory/solicitudes");
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al crear solicitud");
    } finally {
      setLoading(false);
    }
  };

  return (
    <RoleGuard allowedRoles={["MECANICO", "JEFE_TALLER", "ADMIN"]}>
      <div className="p-6 max-w-3xl mx-auto">
        <div className="mb-6">
          <Link
            href="/inventory/solicitudes"
            className="text-blue-600 dark:text-blue-400 hover:underline mb-4 inline-block"
          >
            ← Volver a Solicitudes
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Nueva Solicitud de Repuesto
          </h1>
        </div>

        <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Orden de Trabajo <span className="text-red-500">*</span>
            </label>
            <select
              value={form.ot}
              onChange={(e) => setForm({ ...form, ot: e.target.value })}
              className={`w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
                errors.ot ? "border-red-500" : "border-gray-300 dark:border-gray-600"
              }`}
              required
            >
              <option value="">Seleccionar OT...</option>
              {ots.map((ot) => (
                <option key={ot.id} value={ot.id}>
                  OT #{ot.id.substring(0, 8)} - {ot.vehiculo_patente || "Sin vehículo"} - {ot.estado}
                </option>
              ))}
            </select>
            {errors.ot && <p className="mt-1 text-sm text-red-500">{errors.ot}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Repuesto <span className="text-red-500">*</span>
            </label>
            <select
              value={form.repuesto}
              onChange={(e) => setForm({ ...form, repuesto: e.target.value })}
              className={`w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
                errors.repuesto ? "border-red-500" : "border-gray-300 dark:border-gray-600"
              }`}
              required
            >
              <option value="">Seleccionar repuesto...</option>
              {repuestos
                .filter((r) => r.activo !== false)
                .map((repuesto) => (
                  <option key={repuesto.id} value={repuesto.id}>
                    {repuesto.codigo} - {repuesto.nombre}
                  </option>
                ))}
            </select>
            {errors.repuesto && <p className="mt-1 text-sm text-red-500">{errors.repuesto}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Cantidad Solicitada <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              min="1"
              value={form.cantidad_solicitada}
              onChange={(e) => setForm({ ...form, cantidad_solicitada: parseInt(e.target.value) || 1 })}
              className={`w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
                errors.cantidad_solicitada ? "border-red-500" : "border-gray-300 dark:border-gray-600"
              }`}
              required
            />
            {errors.cantidad_solicitada && (
              <p className="mt-1 text-sm text-red-500">{errors.cantidad_solicitada}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Motivo (Opcional)
            </label>
            <textarea
              value={form.motivo}
              onChange={(e) => setForm({ ...form, motivo: e.target.value })}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Describe el motivo de la solicitud..."
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium disabled:opacity-50"
            >
              {loading ? "Creando..." : "Crear Solicitud"}
            </button>
            <Link
              href="/inventory/solicitudes"
              className="px-6 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 rounded-lg transition-colors font-medium"
            >
              Cancelar
            </Link>
          </div>
        </form>
      </div>
    </RoleGuard>
  );
}

