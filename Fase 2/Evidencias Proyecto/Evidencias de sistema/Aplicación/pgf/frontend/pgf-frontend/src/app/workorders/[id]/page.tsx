"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import WorkOrderDetailClient from "./WorkOrderDetailClient";
import { ENDPOINTS } from "@/lib/constants";
import { withSession } from "@/lib/api.client";
import { useDataRefresh } from "@/lib/dataRefresh";

// =============================
// Vista principal (Client Component)
// =============================
export default function WorkOrderDetail() {
  const params = useParams();
  const router = useRouter();
  const toast = useToast();
  const id = params?.id as string;
  const [ot, setOt] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const cargarOT = async () => {
    if (!id) {
      toast.error("ID de OT no válido");
      router.push("/workorders");
      return;
    }

    setLoading(true);
    try {
      const url = ENDPOINTS.WORK_ORDER(id);
      const response = await fetch(url, {
        method: "GET",
        ...withSession(),
      });

      if (!response.ok) {
        if (response.status === 404) {
          toast.error("Orden de trabajo no encontrada");
        } else if (response.status === 403) {
          toast.error("No tiene permisos para ver esta orden de trabajo");
        } else {
          const errorText = await response.text().catch(() => "Error desconocido");
          let errorMessage = "Error al cargar la orden de trabajo";
          try {
            const errorData = JSON.parse(errorText);
            errorMessage = errorData.detail || errorMessage;
          } catch {
            errorMessage = errorText || errorMessage;
          }
          toast.error(errorMessage);
        }
        router.push("/workorders");
        return;
      }

      const data = await response.json();
      setOt(data);
    } catch (error) {
      console.error("Error al cargar OT:", error);
      toast.error("Error al cargar la orden de trabajo");
      router.push("/workorders");
    } finally {
      setLoading(false);
    }
  };

  // Cargar OT al montar y cuando cambia el ID
  useEffect(() => {
    if (id) {
      cargarOT();
    }
  }, [id]);

  // Escuchar eventos de refresh de datos
  useDataRefresh("WORKORDERS", cargarOT);

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando orden de trabajo...</p>
        </div>
      </div>
    );
  }

  if (!ot) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          No se encontró la Orden de Trabajo
        </h1>
        <button
          onClick={() => router.push("/workorders")}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
        >
          Volver a Órdenes de Trabajo
        </button>
      </div>
    );
  }

  return <WorkOrderDetailClient ot={ot} id={id} />;
}
