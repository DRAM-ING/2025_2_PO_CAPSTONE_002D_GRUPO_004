"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useToast } from "@/components/ToastContainer";

export default function VehicleHistory() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;
  const toast = useToast();
  const [historial, setHistorial] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const r = await fetch(`/api/proxy/vehicles/${id}/historial/`, {
          credentials: "include",
        });

        if (!r.ok) {
          toast.error("Error al cargar el historial");
          router.push(`/vehicles/${id}`);
          return;
        }

        const text = await r.text();
        if (!text || text.trim() === "") {
          toast.error("No hay historial disponible");
          router.push(`/vehicles/${id}`);
          return;
        }

        const data = JSON.parse(text);
        setHistorial(data);
      } catch (e) {
        console.error("Error:", e);
        toast.error("Error al cargar el historial");
        router.push(`/vehicles/${id}`);
      } finally {
        setLoading(false);
      }
    };

    if (id) load();
  }, [id, router, toast]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando historial...</p>
        </div>
      </div>
    );
  }

  if (!historial) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Historial no encontrado</h1>
        <Link href={`/vehicles/${id}`} className="text-blue-600 dark:text-blue-400 hover:underline mt-4 inline-block">
          Volver al vehículo
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Historial - {historial.vehiculo?.patente}
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            {historial.vehiculo?.marca} {historial.vehiculo?.modelo} ({historial.vehiculo?.anio})
          </p>
        </div>
        <Link
          href={`/vehicles/${id}`}
          className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
        >
          ← Volver
        </Link>
      </div>

      {/* Resumen */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">Total Órdenes</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{historial.total_ordenes || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">Repuestos Utilizados</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{historial.total_repuestos || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">Ingresos al Taller</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{historial.total_ingresos || 0}</p>
        </div>
      </div>

      {/* Órdenes de Trabajo */}
      <section className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Órdenes de Trabajo</h2>
        {historial.ordenes_trabajo?.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400">No hay órdenes de trabajo registradas.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="bg-gray-100 dark:bg-gray-700">
                  <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">ID</th>
                  <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Estado</th>
                  <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Tipo</th>
                  <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Prioridad</th>
                  <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Responsable</th>
                  <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Apertura</th>
                  <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Cierre</th>
                  <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {historial.ordenes_trabajo?.map((ot: any) => (
                  <tr key={ot.id} className="border-t border-gray-200 dark:border-gray-700">
                    <td className="p-3 text-gray-900 dark:text-white">#{ot.id.substring(0, 8)}</td>
                    <td className="p-3">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        ot.estado === "ABIERTA" ? "bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-400" :
                        ot.estado === "EN_EJECUCION" ? "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-400" :
                        ot.estado === "EN_PAUSA" ? "bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-400" :
                        ot.estado === "EN_QA" ? "bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-400" :
                        "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400"
                      }`}>
                        {ot.estado}
                      </span>
                    </td>
                    <td className="p-3 text-gray-700 dark:text-gray-300">{ot.tipo || "N/A"}</td>
                    <td className="p-3 text-gray-700 dark:text-gray-300">{ot.prioridad || "N/A"}</td>
                    <td className="p-3 text-gray-700 dark:text-gray-300">{ot.responsable || "Sin responsable"}</td>
                    <td className="p-3 text-gray-700 dark:text-gray-300">
                      {(() => {
                        const fechaApertura = ot.apertura || ot.fecha_apertura;
                        if (!fechaApertura) return "N/A";
                        try {
                          const fecha = new Date(fechaApertura);
                          if (isNaN(fecha.getTime())) return "N/A";
                          return fecha.toLocaleDateString('es-CL', {
                            year: 'numeric',
                            month: '2-digit',
                            day: '2-digit',
                            hour: '2-digit',
                            minute: '2-digit'
                          });
                        } catch (e) {
                          return "N/A";
                        }
                      })()}
                    </td>
                    <td className="p-3 text-gray-700 dark:text-gray-300">
                      {ot.cierre ? new Date(ot.cierre).toLocaleDateString() : "-"}
                    </td>
                    <td className="p-3">
                      <Link
                        href={`/workorders/${ot.id}`}
                        className="text-blue-600 dark:text-blue-400 hover:underline"
                      >
                        Ver
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Historial de Repuestos */}
      {historial.historial_repuestos && historial.historial_repuestos.length > 0 && (
        <section className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Historial de Repuestos</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="bg-gray-100 dark:bg-gray-700">
                  <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Código</th>
                  <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Nombre</th>
                  <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Cantidad</th>
                  <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Costo Unit.</th>
                  <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">Fecha Uso</th>
                  <th className="p-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">OT</th>
                </tr>
              </thead>
              <tbody>
                {historial.historial_repuestos.map((r: any, idx: number) => (
                  <tr key={idx} className="border-t border-gray-200 dark:border-gray-700">
                    <td className="p-3 text-gray-900 dark:text-white">{r.repuesto_codigo}</td>
                    <td className="p-3 text-gray-700 dark:text-gray-300">{r.repuesto_nombre}</td>
                    <td className="p-3 text-gray-700 dark:text-gray-300">{r.cantidad}</td>
                    <td className="p-3 text-gray-700 dark:text-gray-300">
                      {r.costo_unitario ? `$${parseFloat(r.costo_unitario).toLocaleString()}` : "N/A"}
                    </td>
                    <td className="p-3 text-gray-700 dark:text-gray-300">
                      {new Date(r.fecha_uso).toLocaleDateString()}
                    </td>
                    <td className="p-3">
                      {r.ot_id ? (
                        <Link
                          href={`/workorders/${r.ot_id}`}
                          className="text-blue-600 dark:text-blue-400 hover:underline"
                        >
                          Ver OT
                        </Link>
                      ) : (
                        "-"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Ingresos al Taller */}
      {historial.ingresos && historial.ingresos.length > 0 && (
        <section className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Ingresos al Taller</h2>
          <div className="space-y-4">
            {historial.ingresos.map((ingreso: any) => (
              <div key={ingreso.id} className="border dark:border-gray-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-white">
                      {new Date(ingreso.fecha_ingreso).toLocaleString()}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Registrado por: {ingreso.guardia}
                    </p>
                  </div>
                  {ingreso.kilometraje && (
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {ingreso.kilometraje.toLocaleString()} km
                    </span>
                  )}
                </div>
                {ingreso.observaciones && (
                  <p className="text-sm text-gray-700 dark:text-gray-300 mt-2">{ingreso.observaciones}</p>
                )}
                {ingreso.ot_id && (
                  <div className="mt-3">
                    <Link
                      href={`/workorders/${ingreso.ot_id}`}
                      className="inline-flex items-center px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm font-medium"
                    >
                      Ver OT #{ingreso.ot_id.substring(0, 8)}
                      {ingreso.ot_estado && (
                        <span className="ml-2 px-2 py-0.5 bg-blue-700 rounded text-xs">
                          {ingreso.ot_estado}
                        </span>
                      )}
                    </Link>
                  </div>
                )}
                {ingreso.evidencias && ingreso.evidencias.length > 0 && (
                  <div className="mt-3">
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Evidencias:</p>
                    <div className="flex flex-wrap gap-2">
                      {ingreso.evidencias.map((ev: any, idx: number) => (
                        <a
                          key={idx}
                          href={ev.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 dark:text-blue-400 hover:underline text-sm"
                        >
                          {ev.descripcion || ev.tipo}
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

