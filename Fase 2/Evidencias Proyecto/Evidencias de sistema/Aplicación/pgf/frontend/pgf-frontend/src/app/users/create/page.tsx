"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import { validateRequired, validateEmail, validateMinLength, validatePassword } from "@/lib/validations";
import RoleGuard from "@/components/RoleGuard";
import { ALL_ROLES } from "@/lib/constants";
import PasswordInput from "@/components/PasswordInput";
import { invalidateCache } from "@/lib/dataRefresh";

export default function CreateUser() {
  const router = useRouter();
  const toast = useToast();
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    rut: "",
    password: "",
    username: "",
    rol: "MECANICO",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    const firstNameError = validateRequired(form.first_name, "Nombre");
    if (firstNameError) newErrors.first_name = firstNameError;

    const lastNameError = validateRequired(form.last_name, "Apellido");
    if (lastNameError) newErrors.last_name = lastNameError;

    const emailError = validateRequired(form.email, "Email") || validateEmail(form.email);
    if (emailError) newErrors.email = emailError;

    const rutError = validateRequired(form.rut, "RUT");
    if (rutError) newErrors.rut = rutError;
    else if (form.rut) {
      const rutClean = form.rut.replace(/[.-]/g, "").toUpperCase();
      // Acepta 7-9 dígitos seguidos de un dígito verificador (0-9 o K)
      if (!/^\d{7,9}[0-9K]$/.test(rutClean)) {
        newErrors.rut = "RUT inválido. Debe ser sin puntos ni guión (ej: 123456789 o 12345678K)";
      }
    }

    const usernameError = validateRequired(form.username, "Usuario");
    if (usernameError) newErrors.username = usernameError;

    const passwordError = validateRequired(form.password, "Contraseña");
    if (passwordError) {
      newErrors.password = passwordError;
    } else if (form.password) {
      // Validar complejidad de contraseña
      const passwordComplexityError = validatePassword(form.password);
      if (passwordComplexityError) {
        newErrors.password = passwordComplexityError;
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      toast.error("Por favor corrige los errores en el formulario");
      return;
    }

    setLoading(true);

    try {
      const r = await fetch("/api/proxy/users/", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
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
        }
        
        return;
      }

      toast.success("Usuario creado correctamente");
      invalidateCache("USERS");
      router.refresh();
      router.push("/users");
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al crear usuario");
    } finally {
      setLoading(false);
    }
  };

  const updateField = (key: string, value: string) => {
    setForm({ ...form, [key]: value });
    if (errors[key]) {
      setErrors({ ...errors, [key]: "" });
    }
  };

  return (
    <RoleGuard allow={["ADMIN", "SUPERVISOR"]}>
      <div className="p-6 max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Crear Usuario</h1>

        <form onSubmit={submit} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-6">
          <div>
            <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
              Nombre *
            </label>
            <input
              placeholder="Nombre"
              className={`input w-full ${errors.first_name ? "border-red-500" : ""}`}
              value={form.first_name}
              onChange={(e) => updateField("first_name", e.target.value)}
            />
            {errors.first_name && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.first_name}</p>
            )}
          </div>

          <div>
            <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
              Apellido *
            </label>
            <input
              placeholder="Apellido"
              className={`input w-full ${errors.last_name ? "border-red-500" : ""}`}
              value={form.last_name}
              onChange={(e) => updateField("last_name", e.target.value)}
            />
            {errors.last_name && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.last_name}</p>
            )}
          </div>

          <div>
            <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
              Usuario *
            </label>
            <input
              placeholder="Nombre de usuario"
              className={`input w-full ${errors.username ? "border-red-500" : ""}`}
              value={form.username}
              onChange={(e) => updateField("username", e.target.value)}
            />
            {errors.username && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.username}</p>
            )}
          </div>

          <div>
            <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
              Email *
            </label>
            <input
              type="email"
              placeholder="email@ejemplo.com"
              className={`input w-full ${errors.email ? "border-red-500" : ""}`}
              value={form.email}
              onChange={(e) => updateField("email", e.target.value)}
            />
            {errors.email && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.email}</p>
            )}
          </div>

          <div>
            <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
              RUT *
            </label>
            <input
              placeholder="123456789 (sin puntos ni guión)"
              className={`input w-full ${errors.rut ? "border-red-500" : ""}`}
              value={form.rut}
              onChange={(e) => {
                let value = e.target.value.replace(/[^0-9kK]/gi, "").toUpperCase();
                // Limitar a 10 caracteres máximo (9 dígitos + 1 verificador)
                if (value.length > 10) value = value.slice(0, 10);
                updateField("rut", value);
              }}
              maxLength={12}
            />
            {errors.rut && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.rut}</p>
            )}
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Sin puntos ni guión (ej: 123456789)
            </p>
          </div>

          <div>
            <PasswordInput
              id="password"
              label="Contraseña *"
              value={form.password}
              onChange={(e) => updateField("password", e.target.value)}
              placeholder="Mínimo 8 caracteres"
              required
              autoComplete="new-password"
              error={errors.password}
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              La contraseña debe tener: al menos 8 caracteres, una letra mayúscula, una letra minúscula, un número y un carácter especial (!@#$%^&*...)
            </p>
          </div>

          <div>
            <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
              Rol *
            </label>
            <select
              className="input w-full"
              value={form.rol}
              onChange={(e) => updateField("rol", e.target.value)}
            >
              {ALL_ROLES.map((rol) => (
                <option key={rol} value={rol}>
                  {rol}
                </option>
              ))}
            </select>
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
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Creando...
                </span>
              ) : (
                "Crear Usuario"
              )}
            </button>
          </div>
        </form>
      </div>
    </RoleGuard>
  );
}
