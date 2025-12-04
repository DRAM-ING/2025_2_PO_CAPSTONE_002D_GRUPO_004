"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";
import PasswordInput from "@/components/PasswordInput";

export default function ChangePasswordPage() {
  const router = useRouter();
  const toast = useToast();
  const { user } = useAuth();
  const [form, setForm] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!form.current_password) {
      newErrors.current_password = "La contraseña actual es requerida";
    }

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
      const r = await fetch("/api/proxy/auth/change-password/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          current_password: form.current_password,
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

      toast.success("Contraseña actualizada correctamente");
      setForm({
        current_password: "",
        new_password: "",
        confirm_password: "",
      });
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al cambiar la contraseña");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          Cambiar Contraseña
        </h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <PasswordInput
            id="current_password"
            label="Contraseña Actual *"
            value={form.current_password}
            onChange={(e) => {
              setForm({ ...form, current_password: e.target.value });
              if (errors.current_password) {
                setErrors({ ...errors, current_password: "" });
              }
            }}
            placeholder="Ingresa tu contraseña actual"
            required
            autoComplete="current-password"
            error={errors.current_password}
          />

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
              onClick={() => router.back()}
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 rounded-lg transition-colors"
            >
              Cancelar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

