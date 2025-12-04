"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import RoleGuard from "@/components/RoleGuard";
import { invalidateCache } from "@/lib/dataRefresh";

export default function DiagnosticoOT() {
  const params = useParams();
  const id = params?.id as string;
  const router = useRouter();
  const toast = useToast();
  const [diagnostico, setDiagnostico] = useState("");
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
        setDiagnostico(data.diagnostico || "");
      } catch (e) {
        console.error("Error:", e);
        toast.error("Error al cargar OT");
      }
    };

    if (id) load();
  }, [id, router, toast]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!diagnostico.trim()) {
      toast.error("El diagnóstico es requerido");
      return;
    }

    setLoading(true);

    try {
      const r = await fetch(`/api/proxy/work/ordenes/${id}/diagnostico/`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ diagnostico }),
      });

      const text = await r.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        data = { detail: text || "Error desconocido" };
      }

      if (!r.ok) {
        toast.error(data.detail || "Error al registrar diagnóstico");
        return;
      }

      toast.success("Diagnóstico registrado correctamente");
      invalidateCache("WORKORDERS");
      router.refresh();
      router.push(`/workorders/${id}`);
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al registrar diagnóstico");
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
    <RoleGuard allow={["JEFE_TALLER", "ADMIN"]}>
      <div className="p-8 max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">
          Registrar Diagnóstico - OT #{id.slice(0, 8)}
        </h1>

        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">Información de la OT</h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            <strong>Vehículo:</strong> {ot.vehiculo?.patente || "N/A"}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            <strong>Estado:</strong> {ot.estado}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            <strong>Motivo:</strong> {ot.motivo || "N/A"}
          </p>
        </div>

        <form onSubmit={submit} className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Diagnóstico <span className="text-red-500">*</span>
            </label>
            <textarea
              value={diagnostico}
              onChange={(e) => setDiagnostico(e.target.value)}
              rows={10}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Describe el diagnóstico realizado..."
              required
            />
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Describe detalladamente el diagnóstico realizado sobre el vehículo.
            </p>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 text-white rounded-lg transition-colors font-medium disabled:opacity-50"
              style={{ backgroundColor: '#003DA5' }}
            >
              {loading ? "Guardando..." : "Registrar Diagnóstico"}
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

