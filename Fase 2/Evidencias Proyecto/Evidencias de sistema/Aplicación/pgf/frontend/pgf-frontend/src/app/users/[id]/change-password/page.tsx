"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";
import RoleGuard from "@/components/RoleGuard";
import PasswordInput from "@/components/PasswordInput";

export default function AdminChangePasswordPage() {
  const params = useParams();
  const id = params?.id as string;
  const router = useRouter();
  const toast = useToast();
  const { hasRole } = useAuth();
  const [form, setForm] = useState({
    new_password: "",
    confirm_password: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const loadUser = async () => {
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
      }
    };

    if (id) loadUser();
  }, [id, router, toast]);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!form.new_password) {
      newErrors.new_password = "La nueva contraseña es requerida";
    } else if (form.new_password.length < 8) {
      newErrors.new_password = "La contraseña debe tener al menos 8 caracteres";
    }

    if (!form.confirm_password) {
      newErrors.confirm_password = "Confirma la nueva contraseña";
    } else if (form.new_password !== form.confirm_password) {
      newErrors.confirm_password = "Las contraseñas no coinciden";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      toast.error("Por favor corrige los errores en el formulario");
      return;
    }

    setLoading(true);

    try {
      const r = await fetch(`/api/proxy/users/${id}/change-password/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          new_password: form.new_password,
          confirm_password: form.confirm_password,
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
        toast.error(data.detail || "Error al cambiar la contraseña");
        return;
      }

      toast.success(data.message || "Contraseña actualizada correctamente");
      router.push(`/users/${id}`);
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al cambiar la contraseña");
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando...</p>
        </div>
      </div>
    );
  }

  return (
    <RoleGuard allow={["ADMIN", "SUPERVISOR"]}>
      <div className="max-w-2xl mx-auto">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Cambiar Contraseña de Usuario
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Usuario: {user.first_name} {user.last_name} ({user.username})
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <PasswordInput
                id="new_password"
                label="Nueva Contraseña *"
                value={form.new_password}
                onChange={(e) => {
                  setForm({ ...form, new_password: e.target.value });
                  if (errors.new_password) {
                    setErrors({ ...errors, new_password: "" });
                  }
                }}
                placeholder="Mínimo 8 caracteres"
                required
                autoComplete="new-password"
                error={errors.new_password}
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Mínimo 8 caracteres
              </p>
            </div>

            <PasswordInput
              id="confirm_password"
              label="Confirmar Nueva Contraseña *"
              value={form.confirm_password}
              onChange={(e) => {
                setForm({ ...form, confirm_password: e.target.value });
                if (errors.confirm_password) {
                  setErrors({ ...errors, confirm_password: "" });
                }
              }}
              placeholder="Repite la nueva contraseña"
              required
              autoComplete="new-password"
              error={errors.confirm_password}
            />

            <div className="flex gap-4 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg transition-colors"
              >
                {loading ? "Cambiando..." : "Cambiar Contraseña"}
              </button>
              <button
                type="button"
                onClick={() => router.push(`/users/${id}`)}
                className="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 rounded-lg transition-colors"
              >
                Cancelar
              </button>
            </div>
          </form>
        </div>
      </div>
    </RoleGuard>
  );
}

