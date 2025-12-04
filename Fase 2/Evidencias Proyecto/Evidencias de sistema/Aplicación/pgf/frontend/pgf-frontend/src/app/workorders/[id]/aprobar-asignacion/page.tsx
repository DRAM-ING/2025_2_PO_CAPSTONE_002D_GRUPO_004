"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import RoleGuard from "@/components/RoleGuard";
import { invalidateCache } from "@/lib/dataRefresh";

export default function AprobarAsignacionOT() {
  const params = useParams();
  const id = params?.id as string;
  const router = useRouter();
  const toast = useToast();
  const [mecanicoId, setMecanicoId] = useState("");
  const [prioridad, setPrioridad] = useState("MEDIA");
  const [loading, setLoading] = useState(false);
  const [ot, setOt] = useState<any>(null);
  const [mecanicos, setMecanicos] = useState<any[]>([]);

  useEffect(() => {
    const load = async () => {
      try {
        // Cargar OT
        const otRes = await fetch(`/api/proxy/work/ordenes/${id}/`, {
          credentials: "include",
        });
        
        if (!otRes.ok) {
          toast.error("Error al cargar OT");
          router.push(`/workorders/${id}`);
          return;
        }
        
        const otData = await otRes.json();
        setOt(otData);
        setPrioridad(otData.prioridad || "MEDIA");
        
        // Si ya tiene mecánico asignado, preseleccionarlo (para reasignación)
        if (otData.mecanico) {
          setMecanicoId(otData.mecanico);
        }

        // Cargar mecánicos
        const mecsRes = await fetch("/api/proxy/users/?rol=MECANICO", {
          credentials: "include",
        });
        
        if (mecsRes.ok) {
          const mecsData = await mecsRes.json();
          setMecanicos(mecsData.results || mecsData || []);
        }
      } catch (e) {
        console.error("Error:", e);
        toast.error("Error al cargar datos");
      }
    };

    if (id) load();
  }, [id, router, toast]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!mecanicoId) {
      toast.error("Debes seleccionar un mecánico");
      return;
    }

    setLoading(true);

    try {
      const r = await fetch(`/api/proxy/work/ordenes/${id}/aprobar-asignacion/`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mecanico_id: mecanicoId,
          prioridad: prioridad,
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
        toast.error(data.detail || "Error al aprobar asignación");
        return;
      }

      toast.success("Asignación aprobada correctamente");
      invalidateCache("WORKORDERS");
      router.refresh();
      router.push(`/workorders/${id}`);
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al aprobar asignación");
    } finally {
      setLoading(false);
    }
  };

  if (!ot) {
    return (
      <div className="p-8">
        <div className="text-center">Cargando...</div>
      </div>
    );
  }

  const esReasignacion = ot?.mecanico && ot.mecanico !== null;

  return (
    <RoleGuard allow={["JEFE_TALLER", "ADMIN"]}>
      <div className="p-8 max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">
          {esReasignacion ? "Reasignar Mecánico" : "Asignar Mecánico"} - OT #{id.slice(0, 8)}
        </h1>

        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">Información de la OT</h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            <strong>Vehículo:</strong> {ot.vehiculo?.patente || "N/A"}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            <strong>Estado:</strong> {ot.estado}
          </p>
          {esReasignacion && ot.mecanico_detalle && (
            <div className="mt-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
              <p className="text-sm font-medium text-yellow-800 dark:text-yellow-300">
                Mecánico actual: {ot.mecanico_detalle.nombre_completo || ot.mecanico_nombre}
              </p>
              <p className="text-xs text-yellow-600 dark:text-yellow-400 mt-1">
                Se reasignará a otro mecánico
              </p>
            </div>
          )}
          {ot.diagnostico && (
            <div className="mt-3">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Diagnóstico:</p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{ot.diagnostico}</p>
            </div>
          )}
        </div>

        <form onSubmit={submit} className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Mecánico <span className="text-red-500">*</span>
            </label>
            <select
              value={mecanicoId}
              onChange={(e) => setMecanicoId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              required
            >
              <option value="">Seleccionar mecánico...</option>
              {mecanicos.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.first_name} {m.last_name} ({m.username})
                  {ot?.mecanico === m.id ? " (Actual)" : ""}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Prioridad
            </label>
            <select
              value={prioridad}
              onChange={(e) => setPrioridad(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="CRITICA">Crítica</option>
              <option value="ALTA">Alta</option>
              <option value="MEDIA">Media</option>
              <option value="BAJA">Baja</option>
            </select>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 text-white rounded-lg transition-colors font-medium disabled:opacity-50"
              style={{ backgroundColor: '#003DA5' }}
            >
              {loading ? "Procesando..." : esReasignacion ? "Reasignar Mecánico" : "Asignar Mecánico"}
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

