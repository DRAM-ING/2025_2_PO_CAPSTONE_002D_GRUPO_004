"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import RoleGuard from "@/components/RoleGuard";
import { invalidateCache } from "@/lib/dataRefresh";

export default function RetrabajoOT() {
  const params = useParams();
  const id = params?.id as string;
  const router = useRouter();
  const toast = useToast();
  const [motivo, setMotivo] = useState("");
  const [loading, setLoading] = useState(false);
  const [ot, setOt] = useState<any>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const r = await fetch(`/api/proxy/work/ordenes/${id}/`, {
          credentials: "include",
        });
        
        if (!r.ok) {
          toast.error("Error al cargar OT");
          router.push(`/workorders/${id}`);
          return;
        }
        
        const data = await r.json();
        setOt(data);
      } catch (e) {
        console.error("Error:", e);
        toast.error("Error al cargar OT");
      }
    };

    if (id) load();
  }, [id, router, toast]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();

    setLoading(true);

    try {
      const r = await fetch(`/api/proxy/work/ordenes/${id}/retrabajo/`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          motivo: motivo || "Retrabajo por calidad",
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
        toast.error(data.detail || "Error al marcar como retrabajo");
        return;
      }

      toast.success("OT marcada como retrabajo correctamente");
      invalidateCache("WORKORDERS");
      router.refresh();
      router.push(`/workorders/${id}`);
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al marcar como retrabajo");
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

  return (
    <RoleGuard allow={["SUPERVISOR", "ADMIN", "JEFE_TALLER"]}>
      <div className="p-8 max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">
          Marcar como Retrabajo - OT #{id.slice(0, 8)}
        </h1>

        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-6">
          <p className="text-sm text-yellow-800 dark:text-yellow-200">
            <strong>⚠️ Atención:</strong> Al marcar esta OT como retrabajo, volverá al estado EN_EJECUCION para que el mecánico corrija los problemas detectados en QA.
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">Información de la OT</h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            <strong>Vehículo:</strong> {ot.vehiculo?.patente || "N/A"}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            <strong>Estado:</strong> {ot.estado}
          </p>
        </div>

        <form onSubmit={submit} className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Motivo del Retrabajo
            </label>
            <textarea
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              rows={5}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Describe el motivo del retrabajo (opcional, por defecto: 'Retrabajo por calidad')"
            />
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Si no especificas un motivo, se usará "Retrabajo por calidad" por defecto.
            </p>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg transition-colors font-medium disabled:opacity-50"
            >
              {loading ? "Procesando..." : "Marcar como Retrabajo"}
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

