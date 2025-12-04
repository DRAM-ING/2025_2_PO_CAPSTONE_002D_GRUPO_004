"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";

export default function UserDetail() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;
  const toast = useToast();
  const { hasRole } = useAuth();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const r = await fetch(`/api/proxy/users/${id}/`, {
          credentials: "include",
        });

        if (!r.ok) {
          toast.error("Error al cargar el usuario");
          router.push("/users");
          return;
        }

        const text = await r.text();
        if (!text || text.trim() === "") {
          toast.error("Usuario no encontrado");
          router.push("/users");
          return;
        }

        const data = JSON.parse(text);
        setUser(data);
      } catch (e) {
        console.error("Error:", e);
        toast.error("Error al cargar el usuario");
        router.push("/users");
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

  if (!user) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Usuario no encontrado</h1>
        <Link href="/users" className="text-blue-600 dark:text-blue-400 hover:underline mt-4 inline-block">
          Volver a usuarios
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          {user.first_name} {user.last_name}
        </h1>
        {canEdit && (
          <div className="flex gap-3">
            <Link
              href={`/users/${user.id}/edit`}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
            >
              Editar
            </Link>
            {!user.is_permanent && (
              <Link
                href={`/users/${user.id}/delete`}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors font-medium"
              >
                Eliminar
              </Link>
            )}
            {user.is_permanent && (
              <span className="px-4 py-2 bg-gray-400 text-white rounded-lg cursor-not-allowed font-medium" title="Este usuario es permanente y no se puede eliminar">
                Eliminar (Permanente)
              </span>
            )}
          </div>
        )}
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Nombre completo
            </label>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              {user.first_name} {user.last_name}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Rol
            </label>
            <span className="inline-block px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded text-sm font-medium">
              {user.rol}
            </span>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Usuario
            </label>
            <p className="text-lg text-gray-900 dark:text-white">{user.username}</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Email
            </label>
            <p className="text-lg text-gray-900 dark:text-white">{user.email}</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              RUT
            </label>
            <p className="text-lg text-gray-900 dark:text-white">{user.rut || "-"}</p>
          </div>

          {user.date_joined && (
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                Fecha de registro
              </label>
              <p className="text-lg text-gray-900 dark:text-white">
                {new Date(user.date_joined).toLocaleDateString()}
              </p>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Estado
            </label>
            <span className={`inline-block px-3 py-1 rounded text-sm font-medium ${
              user.is_active
                ? "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400"
                : "bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-400"
            }`}>
              {user.is_active ? "Activo" : "Inactivo"}
            </span>
          </div>

          {user.is_permanent && (
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                Tipo de Usuario
              </label>
              <span className="inline-block px-3 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-400 rounded text-sm font-medium">
                Usuario Permanente
              </span>
            </div>
          )}
        </div>

        <div className="pt-4 border-t border-gray-200 dark:border-gray-700 flex justify-between items-center">
          <Link
            href="/users"
            className="text-blue-600 dark:text-blue-400 hover:underline"
          >
            ← Volver a usuarios
          </Link>
          
          {canEdit && (
            <div className="flex gap-2">
              <Link
                href={`/users/${id}/change-password`}
                className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg transition-colors text-sm"
              >
                Cambiar Contraseña
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

