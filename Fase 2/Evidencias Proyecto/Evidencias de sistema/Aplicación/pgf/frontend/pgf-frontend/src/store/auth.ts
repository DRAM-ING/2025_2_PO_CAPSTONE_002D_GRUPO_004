/**
 * Store de autenticación usando Zustand.
 * 
 * Este módulo gestiona el estado global de autenticación del usuario,
 * incluyendo información del usuario logueado, permisos y funciones de acceso.
 * 
 * Dependencias:
 * - zustand: Biblioteca de estado global ligera
 * - @/lib/constants: Constantes de roles y permisos (ROLE_ACCESS)
 * 
 * Uso:
 * - Importado en componentes que necesitan verificar autenticación
 * - Usado en middleware.ts para proteger rutas
 * - Usado en RoleGuard para control de acceso basado en roles
 */

"use client";  // Indica que este módulo solo se ejecuta en el cliente (Next.js)

import { create } from "zustand";  // Función para crear el store de Zustand
import { ROLE_ACCESS, Rol } from "@/lib/constants";  // Constantes de roles y permisos

/**
 * Tipo que define la estructura de la sesión de usuario.
 * 
 * Representa la información del usuario que está actualmente logueado.
 * Esta información se obtiene del endpoint /api/auth/me del backend.
 */
export type UserSession = {
  id: string;           // UUID del usuario
  username: string;     // Nombre de usuario (único)
  email?: string;       // Email del usuario (opcional)
  rol: Rol;            // Rol del usuario (ADMIN, SUPERVISOR, etc.)
};

/**
 * Tipo que define el estado y métodos del store de autenticación.
 * 
 * Zustand usa este tipo para tipar el store y sus métodos.
 */
type AuthState = {
  // Estado
  user: UserSession | null;  // Usuario actualmente logueado, null si no hay sesión
  
  // Métodos
  setUser: (u: UserSession | null) => void;  // Establece el usuario (login/logout)
  allowed: (section: string) => boolean;      // Verifica si el usuario tiene acceso a una sección
  hasRole: (roles: Rol | Rol[]) => boolean; // Verifica si el usuario tiene uno de los roles especificados
  isLogged: () => boolean;                  // Verifica si hay un usuario logueado
  refreshMe: () => Promise<void>;            // Actualiza la información del usuario desde el backend
};

/**
 * Store de autenticación creado con Zustand.
 * 
 * Zustand proporciona un store ligero y fácil de usar que:
 * - No requiere providers (como Redux)
 * - Permite suscripciones selectivas
 * - Funciona bien con React Server Components
 * 
 * El store se inicializa con valores por defecto y métodos que pueden
 * modificar el estado.
 */
export const useAuth = create<AuthState>((set, get) => ({
  /**
   * Estado inicial: no hay usuario logueado
   */
  user: null,

  /**
   * Establece el usuario en el store.
   * 
   * Se usa cuando:
   * - El usuario hace login (se establece el usuario)
   * - El usuario hace logout (se establece null)
   * 
   * Parámetros:
   * - u: Usuario a establecer o null para logout
   */
  setUser: (u) => set({ user: u }),

  /**
   * Verifica si el usuario tiene acceso a una sección específica.
   * 
   * Consulta ROLE_ACCESS para determinar qué secciones puede ver
   * el usuario según su rol.
   * 
   * Parámetros:
   * - section: Nombre de la sección (ej: "dashboard", "users", "vehicles")
   * 
   * Retorna:
   * - true si el usuario tiene acceso
   * - false si no hay usuario o no tiene acceso
   * 
   * Ejemplo:
   * - allowed("dashboard") -> true si el rol del usuario incluye "dashboard"
   * 
   * Uso:
   * - Usado en Sidebar para mostrar/ocultar items del menú
   * - Usado en componentes para condicionar renderizado
   */
  allowed: (section) => {
    const user = get().user;  // Obtener usuario actual del store
    if (!user) return false;  // Si no hay usuario, no tiene acceso
    
    // Consultar ROLE_ACCESS para el rol del usuario
    // ROLE_ACCESS[user.rol] es un array de secciones permitidas
    // includes(section) verifica si la sección está en el array
    // ?? false: si ROLE_ACCESS[user.rol] es undefined, retorna false
    return ROLE_ACCESS[user.rol]?.includes(section) ?? false;
  },

  /**
   * Verifica si el usuario tiene uno de los roles especificados.
   * 
   * Útil para control de acceso granular donde se necesita
   * verificar roles específicos en lugar de secciones.
   * 
   * Parámetros:
   * - roles: Un rol o array de roles a verificar
   * 
   * Retorna:
   * - true si el usuario tiene uno de los roles
   * - false si no hay usuario o no tiene ninguno de los roles
   * 
   * Ejemplo:
   * - hasRole("ADMIN") -> true si el usuario es ADMIN
   * - hasRole(["ADMIN", "SUPERVISOR"]) -> true si el usuario es ADMIN o SUPERVISOR
   * 
   * Uso:
   * - Usado en RoleGuard para proteger componentes
   * - Usado en componentes para mostrar/ocultar botones según rol
   */
  hasRole: (roles) => {
    // Convertir a array si es un solo rol
    const rlist = Array.isArray(roles) ? roles : [roles];
    
    // Obtener usuario actual
    const u = get().user;
    
    // Verificar que hay usuario y que su rol está en la lista
    // !!u convierte a boolean (true si existe, false si es null)
    // includes(u.rol) verifica si el rol del usuario está en la lista
    return !!u && rlist.includes(u.rol);
  },

  /**
   * Verifica si hay un usuario logueado.
   * 
   * Retorna:
   * - true si hay un usuario en el store
   * - false si user es null
   * 
   * Uso:
   * - Usado para verificar autenticación antes de acceder a rutas protegidas
   * - Usado en middleware para redirigir a login si no hay sesión
   */
  isLogged: () => {
    const u = get().user;
    return !!u;  // !! convierte a boolean: true si hay usuario, false si es null
  },

  /**
   * Actualiza la información del usuario desde el backend.
   * 
   * Hace una petición al endpoint /api/auth/me para obtener
   * la información actualizada del usuario logueado.
   * 
   * Se usa cuando:
   * - Se necesita refrescar la información del usuario
   * - Después de actualizar el perfil
   * - Para verificar que la sesión sigue activa
   * 
   * Si la petición falla (token inválido, expirado, etc.):
   * - Establece user a null (logout implícito)
   * 
   * Retorna:
   * - Promise<void> que se resuelve cuando termina la actualización
   * 
   * Uso:
   * - Llamado desde dashboard/page.tsx para cargar usuario inicial
   * - Llamado después de operaciones que modifican el usuario
   */
  refreshMe: async () => {
    try {
      // Hacer petición al endpoint /me
      // credentials: "include" envía las cookies (tokens JWT)
      const res = await fetch("/api/auth/me", { credentials: "include" });
      
      // Si la respuesta no es exitosa, lanzar error
      if (!res.ok) throw new Error();
      
      // Parsear respuesta JSON
      const data = await res.json();
      
      // Actualizar el usuario en el store
      set({ user: data });
    } catch {
      // Si hay error (token inválido, red caída, etc.):
      // Establecer user a null para forzar logout
      set({ user: null });
    }
  },
}));
