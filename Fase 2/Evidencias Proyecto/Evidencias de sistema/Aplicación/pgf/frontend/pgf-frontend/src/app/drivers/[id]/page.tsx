"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";

export default function DriverDetailPage() {
  const params = useParams();
  const id = params?.id as string;
  const router = useRouter();
  const toast = useToast();
  const { hasRole } = useAuth();
  const [driver, setDriver] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [vehiculos, setVehiculos] = useState<any[]>([]);
  const [asignando, setAsignando] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const r = await fetch(`/api/proxy/drivers/${id}`, {
          credentials: "include",
        });
        
        if (!r.ok) {
          toast.error("Error al cargar chofer");
          router.push("/drivers");
          return;
        }
        
        const data = await r.json();
        setDriver(data);
      } catch (e) {
        console.error("Error:", e);
        toast.error("Error al cargar chofer");
      } finally {
        setLoading(false);
      }
    };

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

    if (id) {
      load();
      loadVehicles();
    }
  }, [id, router, toast]);

  const handleAsignarVehiculo = async (vehiculoId: string) => {
    if (!vehiculoId) {
      toast.error("Selecciona un vehículo");
      return;
    }

    setAsignando(true);
    try {
      const r = await fetch(`/api/proxy/drivers/${id}/asignar-vehiculo`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ vehiculo_id: vehiculoId }),
      });

      if (!r.ok) {
        const error = await r.json().catch(() => ({ detail: "Error al asignar vehículo" }));
        toast.error(error.detail || "Error al asignar vehículo");
        return;
      }

      const data = await r.json();
      setDriver(data);
      toast.success("Vehículo asignado correctamente");
    } catch (e) {
      console.error("Error:", e);
      toast.error("Error al asignar vehículo");
    } finally {
      setAsignando(false);
    }
  };

  const canEdit = hasRole(["ADMIN", "SUPERVISOR", "JEFE_TALLER"]);

  if (loading) {
    return (
      <div className="p-6">
        <div className="text-center">Cargando...</div>
      </div>
    );
  }

  if (!driver) {
    return (
      <div className="p-6">
        <div className="text-center text-red-600">Chofer no encontrado</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Chofer: {driver.nombre_completo || driver.user?.first_name || "N/A"}
        </h1>
        <div className="flex gap-2">
          {canEdit && (
            <Link
              href={`/drivers/${id}/edit`}
              className="px-4 py-2 text-white rounded-lg transition-colors"
              style={{ backgroundColor: '#003DA5' }}
            >
              Editar
            </Link>
          )}
          <Link
            href="/drivers"
            className="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 rounded-lg transition-colors"
          >
            Volver
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Información Personal</h2>
          <dl className="space-y-3">
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Nombre Completo</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white">{driver.nombre_completo || "N/A"}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">RUT</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white">{driver.rut || "N/A"}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Teléfono</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white">{driver.telefono || "N/A"}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Email</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white">{driver.email || "N/A"}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Zona</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white">{driver.zona || "N/A"}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Sucursal</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white">{driver.sucursal || "N/A"}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">KM Mensual Promedio</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-white">{driver.km_mensual_promedio || "N/A"}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Estado</dt>
              <dd className="mt-1">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  driver.activo 
                    ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" 
                    : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                }`}>
                  {driver.activo ? "Activo" : "Inactivo"}
                </span>
              </dd>
            </div>
          </dl>
        </div>

        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Vehículo Asignado</h2>
          {driver.vehiculo_asignado ? (
            <div className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Patente</dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-white">{driver.vehiculo_patente || driver.vehiculo_asignado?.patente || "N/A"}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Marca/Modelo</dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                  {driver.vehiculo_asignado?.marca || ""} {driver.vehiculo_asignado?.modelo || ""}
                </dd>
              </div>
              {canEdit && (
                <Link
                  href={`/vehicles/${driver.vehiculo_asignado?.id}`}
                  className="inline-block mt-2 px-3 py-1 text-sm text-white rounded transition-colors"
                  style={{ backgroundColor: '#003DA5' }}
                >
                  Ver Vehículo
                </Link>
              )}
            </div>
          ) : (
            <p className="text-gray-500 dark:text-gray-400">Sin vehículo asignado</p>
          )}

          {canEdit && (
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Asignar Vehículo
              </label>
              <select
                onChange={(e) => {
                  if (e.target.value) {
                    handleAsignarVehiculo(e.target.value);
                  }
                }}
                disabled={asignando}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">Seleccionar vehículo...</option>
                {vehiculos.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.patente} - {v.marca} {v.modelo}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

