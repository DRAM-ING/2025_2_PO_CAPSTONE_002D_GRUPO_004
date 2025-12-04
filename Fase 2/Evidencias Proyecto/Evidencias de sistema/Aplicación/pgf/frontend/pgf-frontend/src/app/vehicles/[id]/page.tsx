"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";

export default function VehicleDetail() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;
  const toast = useToast();
  const { hasRole } = useAuth();
  const [vehicle, setVehicle] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      // Validar que el ID existe y no es undefined
      if (!id || id === "undefined" || id.trim() === "") {
        toast.error("ID de vehículo no válido");
        router.push("/vehicles");
        return;
      }

      try {
        const r = await fetch(`/api/proxy/vehicles/${id}/`, {
          credentials: "include",
        });

        if (!r.ok) {
          if (r.status === 404) {
            toast.error("Vehículo no encontrado");
          } else {
            toast.error("Error al cargar el vehículo");
          }
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
        setVehicle(data);
      } catch (e) {
        console.error("Error:", e);
        toast.error("Error al cargar el vehículo");
        router.push("/vehicles");
      } finally {
        setLoading(false);
      }
    };

    if (id) load();
  }, [id, router, toast]);

  const canEdit = hasRole(["ADMIN", "SUPERVISOR"]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando...</p>
        </div>
      </div>
    );
  }

  if (!vehicle) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Vehículo no encontrado</h1>
        <Link href="/vehicles" className="text-blue-600 dark:text-blue-400 hover:underline mt-4 inline-block">
          Volver a vehículos
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Vehículo {vehicle.patente}
        </h1>
        {canEdit && (
          <div className="flex gap-3">
            <Link
              href={`/vehicles/${vehicle.id}/edit`}
              className="px-4 py-2 text-white rounded-lg transition-colors font-medium"
              style={{ backgroundColor: '#003DA5' }}
            >
              Editar
            </Link>
            <Link
              href={`/vehicles/${vehicle.id}/delete`}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors font-medium"
            >
              Eliminar
            </Link>
          </div>
        )}
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Patente
            </label>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">{vehicle.patente}</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Estado
            </label>
            <span className={`inline-block px-3 py-1 rounded text-sm font-medium ${
              vehicle.estado === "ACTIVO"
                ? "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400"
                : "bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300"
            }`}>
              {vehicle.estado || "ACTIVO"}
            </span>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Marca
            </label>
            <p className="text-lg text-gray-900 dark:text-white">{vehicle.marca}</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Modelo
            </label>
            <p className="text-lg text-gray-900 dark:text-white">{vehicle.modelo}</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Año
            </label>
            <p className="text-lg text-gray-900 dark:text-white">{vehicle.anio}</p>
          </div>
        </div>

        <div className="pt-4 border-t border-gray-200 dark:border-gray-700 flex gap-4">
          <Link
            href={`/vehicles/${vehicle.id}/historial`}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors font-medium"
          >
            Ver Historial Completo
          </Link>
          <Link
            href="/vehicles"
            className="text-blue-600 dark:text-blue-400 hover:underline self-center"
          >
            ← Volver a vehículos
          </Link>
        </div>
      </div>
    </div>
  );
}
