"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";

export default function SchedulingDetailPage() {
  const params = useParams();
  const id = params?.id as string;
  const router = useRouter();
  const toast = useToast();
  const { hasRole } = useAuth();
  const [agenda, setAgenda] = useState<any>(null);
  const [loading, setLoading] = useState(true);

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
        setAgenda(data);
      } catch (e) {
        console.error("Error:", e);
        toast.error("Error al cargar programación");
      } finally {
        setLoading(false);
      }
    };

    if (id) load();
  }, [id, router, toast]);

  const canEdit = hasRole(["ADMIN", "SUPERVISOR", "COORDINADOR_ZONA"]);

  const getEstadoColor = (estado: string) => {
    const colors: Record<string, string> = {
      PROGRAMADA: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
      CONFIRMADA: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
      EN_PROCESO: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
      COMPLETADA: "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200",
      CANCELADA: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
      REPROGRAMADA: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200",
    };
    return colors[estado] || "bg-gray-100 text-gray-800";
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="text-center">Cargando...</div>
      </div>
    );
  }

  if (!agenda) {
    return (
      <div className="p-6">
        <div className="text-center text-red-600">Programación no encontrada</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Programación - {agenda.vehiculo_patente || "N/A"}
        </h1>
        <div className="flex gap-2">
          {canEdit && (
            <Link
              href={`/scheduling/${id}/edit`}
              className="px-4 py-2 text-white rounded-lg transition-colors"
              style={{ backgroundColor: '#003DA5' }}
            >
              Editar
            </Link>
          )}
          <Link
            href="/scheduling"
            className="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 rounded-lg transition-colors"
          >
            Volver
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Información General</h2>
          <dl className="space-y-3">
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Vehículo</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white">{agenda.vehiculo_patente || "N/A"}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Fecha Programada</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                {agenda.fecha_programada ? new Date(agenda.fecha_programada).toLocaleString('es-CL') : "N/A"}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Tipo de Mantenimiento</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white">{agenda.tipo_mantenimiento || "N/A"}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Estado</dt>
              <dd className="mt-1">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getEstadoColor(agenda.estado)}`}>
                  {agenda.estado || "N/A"}
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Zona</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white">{agenda.zona || "N/A"}</dd>
            </div>
          </dl>
        </div>

        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Detalles</h2>
          <dl className="space-y-3">
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Motivo</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white whitespace-pre-wrap">
                {agenda.motivo || "N/A"}
              </dd>
            </div>
            {agenda.observaciones && (
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Observaciones</dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-white whitespace-pre-wrap">
                  {agenda.observaciones}
                </dd>
              </div>
            )}
            {agenda.ot_asociada && (
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">OT Asociada</dt>
                <dd className="mt-1">
                  <Link
                    href={`/workorders/${agenda.ot_asociada}`}
                    className="text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    Ver OT
                  </Link>
                </dd>
              </div>
            )}
          </dl>
        </div>
      </div>
    </div>
  );
}

