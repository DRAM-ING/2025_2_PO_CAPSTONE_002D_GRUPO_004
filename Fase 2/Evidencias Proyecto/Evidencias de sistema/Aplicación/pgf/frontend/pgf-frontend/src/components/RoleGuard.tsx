/**
 * Componente RoleGuard - Control de acceso basado en roles.
 * 
 * Este componente protege contenido basándose en:
 * 1. Autenticación: el usuario debe estar logueado
 * 2. Autorización: el usuario debe tener uno de los roles permitidos
 * 
 * Funcionamiento:
 * - Si el usuario no está logueado → redirige a /auth/login
 * - Si el usuario no tiene el rol requerido → redirige a redirectTo
 * - Si el usuario tiene el rol requerido → muestra el contenido
 * 
 * Dependencias:
 * - next/navigation: useRouter para redirecciones
 * - @/store/auth: useAuth para verificar autenticación y roles
 * - @/lib/constants: Rol para tipado
 * 
 * Uso:
 * ```tsx
 * <RoleGuard allow={["ADMIN", "SUPERVISOR"]}>
 *   <AdminPanel />
 * </RoleGuard>
 * ```
 * 
 * Relaciones:
 * - Usado en: Páginas que requieren roles específicos
 * - Depende de: useAuth store para estado de autenticación
 * - Complementa: middleware.ts (protección a nivel de ruta)
 */

"use client";  // Componente de cliente (usa hooks de React)

import { useEffect, useState } from "react";  // Hooks de React
import { useRouter } from "next/navigation";  // Hook para navegación programática
import { useAuth } from "@/store/auth";  // Store de autenticación
import type { Rol } from "@/lib/constants";  // Tipo de rol

/**
 * Props del componente RoleGuard.
 */
interface RoleGuardProps {
  /**
   * Array de roles que tienen acceso al contenido.
   * 
   * Si el usuario tiene CUALQUIERA de estos roles, puede ver el contenido.
   * Si el array está vacío, solo se requiere autenticación (cualquier rol).
   * 
   * Ejemplo:
   * - allow={["ADMIN"]} → Solo ADMIN puede ver
   * - allow={["ADMIN", "SUPERVISOR"]} → ADMIN o SUPERVISOR pueden ver
   * - allow={[]} → Cualquier usuario autenticado puede ver
   */
  allow: Rol[];
  
  /**
   * Contenido a mostrar si el usuario tiene acceso.
   * 
   * Puede ser cualquier elemento React (componente, texto, etc.)
   */
  children: React.ReactNode;
  
  /**
   * Ruta a la que redirigir si el usuario no tiene el rol requerido.
   * 
   * Por defecto: "/dashboard"
   * 
   * Ejemplo:
   * - redirectTo="/vehicles" → Redirige a vehículos si no tiene acceso
   */
  redirectTo?: string;
}

/**
 * Componente RoleGuard.
 * 
 * Protege contenido basándose en autenticación y roles.
 * 
 * Estados:
 * - ready: Indica si la verificación de permisos está completa
 * - loading: Indica si se está verificando la autenticación
 * 
 * Flujo:
 * 1. Al montar, verifica si hay usuario en el store
 * 2. Si no hay usuario, intenta refrescar desde el backend
 * 3. Si no está logueado → redirige a login
 * 4. Si está logueado pero no tiene el rol → redirige a redirectTo
 * 5. Si tiene el rol → muestra el contenido
 */
export default function RoleGuard({
  allow = [],  // Por defecto, array vacío (solo requiere autenticación)
  children,    // Contenido a proteger
  redirectTo = "/dashboard",  // Ruta por defecto para redirección
}: RoleGuardProps) {
  // Hook de navegación para redirecciones programáticas
  const router = useRouter();
  
  // Obtener estado y métodos del store de autenticación
  const { 
    user,        // Usuario actual (null si no está logueado)
    isLogged,    // Función que verifica si hay usuario logueado
    hasRole,     // Función que verifica si el usuario tiene un rol
    refreshMe    // Función para actualizar usuario desde el backend
  } = useAuth();
  
  // Estado: indica si el componente está listo para mostrar contenido
  // Se establece en true solo después de verificar permisos exitosamente
  const [ready, setReady] = useState(false);
  
  // Estado: indica si se está cargando/verificando
  // Se usa para mostrar un spinner mientras se verifica
  const [loading, setLoading] = useState(true);

  /**
   * Efecto que se ejecuta al montar el componente.
   * 
   * Verifica autenticación y permisos antes de mostrar el contenido.
   * 
   * Flujo:
   * 1. Marca como loading
   * 2. Si no hay usuario en el store, intenta refrescar desde el backend
   * 3. Verifica si el usuario está logueado
   * 4. Si hay roles requeridos, verifica que el usuario tenga uno
   * 5. Si todo está bien, marca como ready
   */
  useEffect(() => {
    // Función async inmediatamente invocada (IIFE)
    // Permite usar await dentro de useEffect
    (async () => {
      setLoading(true);  // Iniciar carga
      
      /**
       * Refrescar usuario solo si no está en memoria.
       * 
       * Si el usuario ya está en el store (de una sesión anterior),
       * no necesitamos hacer una petición al backend.
       * Esto optimiza el rendimiento y reduce carga en el servidor.
       */
      if (!user) {
        await refreshMe();  // Obtener usuario desde /api/auth/me
      }

      /**
       * Verificar autenticación.
       * 
       * Si el usuario no está logueado (después de refreshMe),
       * redirigir al login.
       */
      if (!isLogged()) {
        router.replace("/auth/login");  // Redirigir (replace no deja historial)
        return;  // Salir, no continuar con la verificación
      }

      /**
       * Verificar roles si se especificaron.
       * 
       * Si allow.length > 0, significa que se requiere un rol específico.
       * Si el usuario no tiene ninguno de los roles permitidos, redirigir.
       */
      if (allow.length && !hasRole(allow)) {
        // El usuario no tiene el rol requerido
        router.replace(redirectTo);  // Redirigir a la ruta especificada
        return;  // Salir, no mostrar el contenido
      }

      /**
       * Si llegamos aquí, el usuario tiene acceso.
       * 
       * Marcar como ready para mostrar el contenido.
       */
      setReady(true);
      setLoading(false);  // Finalizar carga
    })();

    // eslint-disable-next-line react-hooks/exhaustive-deps
    // Nota: Deshabilitamos la regla de exhaustive-deps porque solo queremos
    // ejecutar este efecto una vez al montar, no cuando cambian las dependencias.
  }, []);  // Array vacío = solo ejecutar al montar

  /**
   * Mostrar spinner mientras se verifica.
   * 
   * Se muestra si:
   * - loading es true (aún verificando)
   * - ready es false (aún no se verificó o no tiene acceso)
   * 
   * Esto proporciona feedback visual al usuario mientras
   * se verifica la autenticación y permisos.
   */
  if (loading || !ready) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          {/* Spinner de carga */}
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
          {/* Mensaje informativo */}
          <p className="mt-4 text-gray-600 dark:text-gray-400">Verificando permisos...</p>
        </div>
      </div>
    );
  }

  /**
   * Si llegamos aquí, el usuario tiene acceso.
   * 
   * Renderizar el contenido protegido.
   * 
   * Usamos Fragment (<></>) para no agregar un elemento DOM extra.
   */
  return <>{children}</>;
}
