"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/store/auth";
import PepsiCoLogo from "@/components/PepsiCoLogo";
import PasswordInput from "@/components/PasswordInput";

export default function LoginPage() {
  const [username, setU] = useState("");
  const [password, setP] = useState("");
  const [loading, setL] = useState(false);
  const [error, setE] = useState<string | null>(null);
  const [rememberMe, setRememberMe] = useState(false);

  const router = useRouter();
  const sp = useSearchParams();
  const next = sp.get("next") || "/dashboard";
  const { setUser } = useAuth();

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setL(true);
    setE(null);

    try {
      // 🔥 Login normal
      const loginRes = await fetch("/api/auth/login", {
        method: "POST",
        credentials: "include",
        body: JSON.stringify({ username, password }),
        headers: { "Content-Type": "application/json" },
      });

      if (!loginRes.ok) {
        const errorData = await loginRes.json().catch(() => ({ detail: "Credenciales inválidas" }));
        throw new Error(errorData.detail || "Credenciales inválidas");
      }

      // 🔥 Cargar el usuario con el token httpOnly vía API
      const meRes = await fetch("/api/auth/me", {
        credentials: "include",
      });

      if (!meRes.ok) throw new Error("Error cargando perfil");

      const text = await meRes.text();
      if (!text || text.trim() === "") {
        throw new Error("Respuesta vacía del servidor");
      }

      let user;
      try {
        user = JSON.parse(text);
      } catch (e) {
        console.error("Invalid JSON response:", text);
        throw new Error("Error procesando respuesta del servidor");
      }

      setUser(user);

      // Redirigir según el rol del usuario
      if (["ADMIN", "SPONSOR", "EJECUTIVO"].includes(user.rol)) {
        router.replace("/dashboard/ejecutivo");
      } else if (user.rol === "SUPERVISOR" || user.rol === "JEFE_TALLER" || user.rol === "COORDINADOR_ZONA") {
        router.replace("/workorders");
      } else if (user.rol === "MECANICO") {
        router.replace("/workorders");
      } else if (user.rol === "GUARDIA") {
        router.replace("/vehicles");
      } else if (user.rol === "CHOFER") {
        router.replace("/vehicles");
      } else {
        // Rol desconocido, redirigir a vehicles por defecto
        router.replace("/vehicles");
      }

    } catch (err: any) {
      setE(err.message || "Error al iniciar sesión");
    } finally {
      setL(false);
    }
  };

  return (
    <div className="relative flex min-h-screen w-full flex-col items-center justify-center bg-[#f6f6f8] dark:bg-[#101622] p-4">
      <div className="w-full max-w-md">
        {/* Logo PepsiCo */}
        <div className="mb-8 flex justify-center">
          <PepsiCoLogo size="lg" variant="default" showText={false} className="h-16 w-auto" />
        </div>

        {/* Form Container */}
        <div className="w-full rounded-xl border border-gray-200/80 bg-white p-6 dark:border-gray-800 dark:bg-[#1C2433] sm:p-8 shadow-lg">
          {/* Header */}
          <div className="text-center">
            <h1 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-white sm:text-3xl">
              Bienvenido
            </h1>
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
              Inicia sesión para gestionar tu taller
            </p>
          </div>

          {/* Form */}
          <form onSubmit={onSubmit} className="mt-8 space-y-6" noValidate>
            {/* User Field */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="username">
                Usuario
              </label>
              <div className="relative mt-2">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-500 pointer-events-none">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </span>
                <input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  required
                  className="block w-full rounded-lg border border-gray-300 bg-gray-50 py-3 pl-10 pr-3 text-gray-900 placeholder:text-gray-400 focus:border-[#135bec] focus:ring-[#135bec] dark:border-gray-700 dark:bg-gray-800/50 dark:text-white dark:placeholder:text-gray-500 dark:focus:border-[#135bec] dark:focus:ring-[#135bec] sm:text-sm transition-colors"
                  placeholder="email@ejemplo.com o nombre de usuario"
                  value={username}
                  onChange={(e) => setU(e.target.value)}
                />
              </div>
            </div>

            {/* Password Field */}
            <PasswordInput
              id="password"
              label="Contraseña"
              value={password}
              onChange={(e) => setP(e.target.value)}
              placeholder="Introduce tu contraseña"
              required
              autoComplete="current-password"
            />

            {/* Remember Me & Forgot Password */}
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  className="h-4 w-4 rounded border-gray-300 text-[#135bec] focus:ring-[#135bec] dark:border-gray-600 dark:bg-gray-700 dark:ring-offset-gray-800"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-600 dark:text-gray-300">
                  Recordarme
                </label>
              </div>
              <div className="text-sm">
                <a
                  href="/auth/reset-password"
                  className="font-medium text-[#135bec] hover:text-[#135bec]/80 transition-colors"
                >
                  ¿Olvidaste tu contraseña?
                </a>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg p-3">
                <div className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <p className="text-red-600 dark:text-red-400 text-sm font-medium">{error}</p>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <div>
              <button
                type="submit"
                disabled={loading}
                className="flex w-full justify-center rounded-lg bg-[#135bec] px-4 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-[#135bec]/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#135bec] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>Iniciando sesión...</span>
                  </span>
                ) : (
                  "Iniciar Sesión"
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Footer Link */}
        <p className="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
          ¿No tienes cuenta?{" "}
          <a
            href="#"
            className="font-semibold leading-6 text-[#135bec] hover:text-[#135bec]/80 transition-colors"
            onClick={(e) => {
              e.preventDefault();
              // Aquí puedes agregar lógica para solicitar acceso
            }}
          >
            Solicitar Acceso
          </a>
        </p>
      </div>
    </div>
  );
}
