"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import { validateRequired, validateEmail, validateMinLength } from "@/lib/validations";
import RoleGuard from "@/components/RoleGuard";
import { ALL_ROLES } from "@/lib/constants";
import PasswordInput from "@/components/PasswordInput";
import { invalidateCache } from "@/lib/dataRefresh";

export default function EditUser() {
  const params = useParams();
  const id = params?.id as string;
  const router = useRouter();
  const toast = useToast();

  const [form, setForm] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showPasswordField, setShowPasswordField] = useState(false);
  const [newPassword, setNewPassword] = useState("");

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
        setForm(data);
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

  const updateField = (key: string, value: string) => {
    setForm({ ...form, [key]: value });
    if (errors[key]) {
      setErrors({ ...errors, [key]: "" });
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    const firstNameError = validateRequired(form.first_name, "Nombre");
    if (firstNameError) newErrors.first_name = firstNameError;

    const lastNameError = validateRequired(form.last_name, "Apellido");
    if (lastNameError) newErrors.last_name = lastNameError;

    const emailError = validateRequired(form.email, "Email") || validateEmail(form.email);
    if (emailError) newErrors.email = emailError;

    if (form.rut) {
      const rutClean = form.rut.replace(/[.-]/g, "").toUpperCase();
      // Acepta 7-9 dígitos seguidos de un dígito verificador (0-9 o K)
      if (!/^\d{7,9}[0-9K]$/.test(rutClean)) {
        newErrors.rut = "RUT inválido. Debe ser sin puntos ni guión (ej: 123456789 o 12345678K)";
      }
    }

    const usernameError = validateRequired(form.username, "Usuario");
    if (usernameError) newErrors.username = usernameError;

    // Validar contraseña solo si se está cambiando
    if (showPasswordField && newPassword) {
      const passwordError = validateMinLength(newPassword, 8, "Contraseña");
      if (passwordError) newErrors.password = passwordError;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const save = async () => {
    if (!validateForm()) {
      toast.error("Por favor corrige los errores en el formulario");
      return;
    }

    setSaving(true);
    setErrors({});

    try {
      // Preparar datos para enviar
      const dataToSend = { ...form };
      
      // Si se está cambiando la contraseña, incluirla en el payload
      if (showPasswordField && newPassword) {
        dataToSend.password = newPassword;
      }

      const r = await fetch(`/api/proxy/users/${id}/`, {
        method: "PATCH",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(dataToSend),
      });

      const text = await r.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        data = { detail: text || "Error desconocido" };
      }

      if (!r.ok) {
        // Importar formateador de errores
        const { formatError, extractFieldErrors } = await import("@/lib/errorFormatter");
        
        // Formatear error de manera amigable
        const friendlyError = formatError(data);
        toast.error(friendlyError);
        
        // Extraer errores por campo
        const fieldErrors = extractFieldErrors(data);
        if (Object.keys(fieldErrors).length > 0) {
          setErrors(fieldErrors);
        } else if (data.errors) {
          setErrors(data.errors);
        }
        
        return;
      }

      toast.success("Usuario actualizado correctamente");
      invalidateCache("USERS");
      router.refresh();
      router.push("/users");
    } catch (e: any) {
      console.error("Error:", e);
      toast.error("Error al actualizar el usuario");
    } finally {
      setSaving(false);
    }
  };

  if (loading || !form) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando...</p>
        </div>
      </div>
    );
  }

  const fields = [
    { key: "first_name", label: "Nombre", type: "text" },
    { key: "last_name", label: "Apellido", type: "text" },
    { key: "username", label: "Usuario", type: "text" },
    { key: "email", label: "Email", type: "email" },
    { key: "rut", label: "RUT", type: "text" },
  ];

  return (
    <RoleGuard allow={["ADMIN", "SUPERVISOR"]}>
      <div className="p-6 max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">Editar Usuario</h1>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-6">
          {fields.map((field) => (
            <div key={field.key}>
              <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                {field.label} *
              </label>
              <input
                type={field.type}
                className={`input w-full ${errors[field.key] ? "border-red-500" : ""}`}
                value={form[field.key] || ""}
                onChange={(e) => {
                  if (field.key === "rut") {
                    let value = e.target.value.replace(/[^0-9kK]/gi, "").toUpperCase();
                    // Limitar a 10 caracteres máximo (9 dígitos + 1 verificador)
                    if (value.length > 10) value = value.slice(0, 10);
                    updateField(field.key, value);
                  } else {
                    updateField(field.key, e.target.value);
                  }
                }}
                maxLength={field.key === "rut" ? 10 : undefined}
              />
              {field.key === "rut" && (
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  Sin puntos ni guión (ej: 123456789)
                </p>
              )}
              {errors[field.key] && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors[field.key]}</p>
              )}
            </div>
          ))}

          <div>
            <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
              Rol *
            </label>
            <select
              className="input w-full"
              value={form.rol || ""}
              onChange={(e) => updateField("rol", e.target.value)}
            >
              {ALL_ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>

          {/* Campo de contraseña opcional para admin */}
          <div className="border-t pt-4 mt-4">
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Cambiar Contraseña
              </label>
              <button
                type="button"
                onClick={() => {
                  setShowPasswordField(!showPasswordField);
                  setNewPassword("");
                  if (errors.password) {
                    setErrors({ ...errors, password: "" });
                  }
                }}
                className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
              >
                {showPasswordField ? "Cancelar cambio" : "Cambiar contraseña"}
              </button>
            </div>
            {showPasswordField && (
              <div>
                <PasswordInput
                  id="new_password"
                  label="Nueva Contraseña"
                  value={newPassword}
                  onChange={(e) => {
                    setNewPassword(e.target.value);
                    if (errors.password) {
                      setErrors({ ...errors, password: "" });
                    }
                  }}
                  placeholder="Nueva contraseña (mínimo 8 caracteres)"
                  minLength={8}
                  autoComplete="new-password"
                  error={errors.password}
                />
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  Deja vacío si no deseas cambiar la contraseña. Mínimo 8 caracteres.
                </p>
              </div>
            )}
          </div>

          <div className="flex gap-4 pt-4">
            <button
              type="button"
              onClick={() => router.back()}
              className="flex-1 px-4 py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={save}
              disabled={saving}
              className="flex-1 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Guardando...
                </span>
              ) : (
                "Guardar Cambios"
              )}
            </button>
          </div>
        </div>
      </div>
    </RoleGuard>
  );
}

