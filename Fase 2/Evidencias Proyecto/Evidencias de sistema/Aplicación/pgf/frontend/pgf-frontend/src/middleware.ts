/**
 * Middleware de Next.js para protección de rutas.
 * 
 * Este middleware se ejecuta en cada request antes de que Next.js
 * procese la página. Se usa para:
 * - Proteger rutas que requieren autenticación
 * - Redirigir usuarios no autenticados al login
 * - Permitir acceso a rutas públicas
 * 
 * Funcionamiento:
 * 1. Verifica si la ruta es pública → permite acceso
 * 2. Verifica si la ruta es protegida → requiere token
 * 3. Si no hay token en ruta protegida → redirige a login
 * 4. Si hay token → permite acceso
 * 
 * Dependencias:
 * - next/server: NextRequest, NextResponse
 * 
 * Configuración:
 * - Se ejecuta según el matcher definido en config
 * - Se ejecuta en el edge runtime (rápido, sin Node.js completo)
 * 
 * Relaciones:
 * - Usado por: Todas las páginas de la aplicación
 * - Lee cookies: pgf_access (token JWT)
 * - Redirige a: /auth/login si no hay token
 */

import { NextResponse } from "next/server";  // Para crear respuestas HTTP
import type { NextRequest } from "next/server";  // Tipo para el request

/**
 * Rutas que requieren autenticación.
 * 
 * Si un usuario intenta acceder a estas rutas sin estar autenticado,
 * será redirigido al login.
 * 
 * Nota: Se usa startsWith() para que también proteja subrutas.
 * Ejemplo: "/users" protege "/users", "/users/123", "/users/create", etc.
 */
const protectedRoutes = [
  "/dashboard",   // Dashboards (ejecutivo, operativo)
  "/users",       // Gestión de usuarios
  "/vehicles",    // Gestión de vehículos
  "/workorders",  // Órdenes de trabajo
  "/profile",     // Perfil del usuario
  // Nota: /drivers, /scheduling, /emergencies, /reports también están protegidos
  // pero se controlan con RoleGuard en las páginas individuales
];

/**
 * Rutas públicas (no requieren autenticación).
 * 
 * Estas rutas son accesibles sin token. Incluyen:
 * - Login: para que los usuarios puedan autenticarse
 * - Reset password: para recuperar contraseña
 */
const publicRoutes = [
  "/auth/login",           // Página de login
  "/auth/reset-password", // Recuperación de contraseña
];

/**
 * Función principal del middleware.
 * 
 * Esta función se ejecuta en cada request que coincide con el matcher.
 * 
 * Flujo:
 * 1. Extrae el pathname de la URL
 * 2. Obtiene el token de las cookies
 * 3. Si es ruta de API → permite acceso (las API routes manejan su propia auth)
 * 4. Si es ruta pública → permite acceso
 * 5. Si es raíz "/" → permite acceso (tiene su propia lógica de redirección)
 * 6. Si es ruta protegida sin token → redirige a login con parámetro "next"
 * 7. Si es ruta protegida con token → permite acceso
 * 
 * Parámetros:
 * - request: Objeto NextRequest con información del request
 * 
 * Retorna:
 * - NextResponse.next(): Permite que la request continúe
 * - NextResponse.redirect(): Redirige a otra URL
 * 
 * Ejemplo de redirección:
 * - Usuario intenta acceder a /users sin token
 * - Se redirige a /auth/login?next=/users
 * - Después del login, puede redirigir de vuelta a /users
 */
export function middleware(request: NextRequest) {
  // Extraer el pathname de la URL (ej: "/users/123" → "/users/123")
  const { pathname } = request.nextUrl;
  
  // Obtener el token JWT de las cookies
  // Este token se establece en el login (apps/users/views.py LoginView)
  const token = request.cookies.get("pgf_access");

  /**
   * Permitir acceso a todas las rutas de API.
   * 
   * Las API routes manejan su propia autenticación:
   * - Verifican el token en cada endpoint
   * - Retornan 401 si no hay token o es inválido
   * 
   * No redirigimos aquí porque las API routes no son páginas HTML.
   */
  if (pathname.startsWith("/api")) {
    return NextResponse.next();
  }

  /**
   * Permitir acceso a rutas públicas.
   * 
   * Estas rutas deben ser accesibles sin autenticación para que
   * los usuarios puedan hacer login o recuperar contraseña.
   */
  if (publicRoutes.some(route => pathname.startsWith(route))) {
    return NextResponse.next();
  }

  /**
   * Permitir acceso a la raíz.
   * 
   * La ruta "/" tiene su propia lógica de redirección en app/page.tsx:
   * - Si hay usuario → redirige según su rol
   * - Si no hay usuario → redirige a /auth/login
   * 
   * No interferimos aquí para permitir esa lógica.
   */
  if (pathname === "/") {
    return NextResponse.next();
  }

  /**
   * Proteger rutas que requieren autenticación.
   * 
   * Si la ruta está en protectedRoutes y no hay token:
   * - Redirigir a /auth/login
   * - Agregar parámetro "next" con la ruta original
   * - Esto permite redirigir de vuelta después del login
   */
  if (protectedRoutes.some(route => pathname.startsWith(route))) {
    if (!token) {
      // Crear URL de login con parámetro "next"
      const loginUrl = new URL("/auth/login", request.url);
      loginUrl.searchParams.set("next", pathname);  // Guardar ruta original
      
      // Redirigir al login
      return NextResponse.redirect(loginUrl);
    }
  }

  /**
   * Si llegamos aquí, permitir acceso.
   * 
   * Esto cubre:
   * - Rutas protegidas con token válido
   * - Rutas que no están en protectedRoutes ni publicRoutes
   *   (se controlan con RoleGuard en las páginas individuales)
   */
  return NextResponse.next();
}

/**
 * Configuración del middleware.
 * 
 * Define qué rutas deben pasar por el middleware.
 * 
 * Matcher:
 * - "/((?!_next/static|_next/image|favicon.ico).*)"
 *   - Coincide con todas las rutas EXCEPTO:
 *   - _next/static: Archivos estáticos de Next.js
 *   - _next/image: Optimización de imágenes
 *   - favicon.ico: Favicon
 * 
 * Esto optimiza el rendimiento al no ejecutar el middleware
 * en requests de archivos estáticos.
 */
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes) - pero las manejamos dentro del middleware
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};
