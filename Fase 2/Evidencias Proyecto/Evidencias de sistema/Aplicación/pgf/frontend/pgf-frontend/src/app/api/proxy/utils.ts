/**
 * Utilidades para proxy de API requests.
 * 
 * Este módulo proporciona funciones para hacer peticiones al backend Django
 * desde las API routes de Next.js, manejando autenticación, errores y
 * parsing de respuestas.
 * 
 * Funcionalidades:
 * - Proxy de requests al backend con autenticación JWT
 * - Manejo robusto de errores y respuestas vacías
 * - Soporte para Next.js 15 (duplex option)
 * - Parsing seguro de JSON
 * 
 * Dependencias:
 * - next/server: NextRequest, NextResponse, cookies
 * 
 * Uso:
 * - Importado en todas las API routes de proxy (ej: apps/api/proxy/reports/route.ts)
 * - Centraliza la lógica de comunicación con el backend
 */

import { NextRequest, NextResponse } from "next/server";  // Tipos de Next.js para API routes
import { cookies } from "next/headers";  // Función para acceder a cookies en server components

/**
 * URL base del backend API.
 * 
 * Se obtiene de la variable de entorno NEXT_PUBLIC_API_BASE_URL
 * o usa un valor por defecto para desarrollo local con Docker.
 * 
 * En producción, debe configurarse en .env:
 * NEXT_PUBLIC_API_BASE_URL=http://api.example.com/api/v1
 */
export const API_BASE =
  process.env.API_BASE ?? "http://api:8000/api/v1";

/**
 * Función principal para hacer proxy de requests al backend.
 * 
 * Esta función:
 * 1. Obtiene el token JWT de las cookies
 * 2. Construye la URL completa del endpoint
 * 3. Agrega headers de autenticación
 * 4. Maneja el caso especial de Next.js 15 (duplex option)
 * 5. Hace la petición al backend
 * 6. Parsea la respuesta de forma segura
 * 7. Retorna una NextResponse con el resultado
 * 
 * Parámetros:
 * - endpoint: Ruta relativa del endpoint (ej: "/users/", "/work/ordenes/")
 * - init: Opciones de fetch (method, body, headers adicionales, etc.)
 * 
 * Retorna:
 * - NextResponse con el JSON parseado o un error
 * 
 * Manejo de errores:
 * - Si no hay token: retorna 401 Unauthorized
 * - Si la respuesta está vacía: retorna objeto vacío o error según status
 * - Si no es JSON válido: retorna error con el texto crudo
 * - Si hay error del backend: retorna el error con el status code original
 * 
 * Ejemplo de uso:
 * ```typescript
 * // GET request
 * const response = await proxyFetch("/users/");
 * 
 * // POST request
 * const response = await proxyFetch("/users/", {
 *   method: "POST",
 *   body: JSON.stringify({ username: "test" })
 * });
 * ```
 */
export async function proxyFetch(
  endpoint: string,  // Ruta relativa del endpoint (ej: "/users/")
  init: RequestInit = {}  // Opciones de fetch (method, body, headers, etc.)
) {
  // Obtener el store de cookies de Next.js
  // En Next.js 15, cookies() debe llamarse dentro de async functions
  const cookieStore = await cookies();
  
  // Obtener el token JWT de la cookie "pgf_access"
  // Este token se establece en el login (apps/users/views.py LoginView)
  const token = cookieStore.get("pgf_access")?.value;

  // Si no hay token, retornar error 401
  // Esto puede pasar si:
  // - El usuario no está logueado
  // - La cookie expiró
  // - La cookie fue eliminada
  if (!token) {
    console.warn(`[proxyFetch] No token found for endpoint: ${endpoint}`);
    return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
  }

  // Construir la URL completa del endpoint
  // API_BASE ya incluye "/api/v1", endpoint es la ruta relativa
  // Asegurar que endpoint empiece con / si no lo hace
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${API_BASE}${normalizedEndpoint}`;
  
  // Log para debugging (solo en desarrollo)
  if (process.env.NODE_ENV === 'development') {
    console.log(`[proxyFetch] Requesting: ${url}`, { endpoint, normalizedEndpoint, API_BASE });
  }
  
  // Validar que la URL es válida
  try {
    new URL(url);
  } catch (error) {
    console.error(`[proxyFetch] Invalid URL constructed: ${url}`, error);
    return NextResponse.json(
      { detail: `Invalid endpoint URL: ${endpoint}` },
      { status: 500 }
    );
  }

  // Preparar opciones de fetch
  // Se combinan las opciones pasadas con las opciones por defecto
  const isFormData = init.body instanceof FormData;
  
  const fetchOptions: RequestInit = {
    ...init,  // Opciones pasadas por el llamador (method, body, etc.)
    headers: {
      // No establecer Content-Type para FormData (el navegador lo hace automáticamente con boundary)
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      Authorization: `Bearer ${token}`,     // Token JWT en header Authorization
      ...(init.headers ?? {}),             // Headers adicionales del llamador
    },
    cache: "no-store",  // No cachear respuestas (siempre obtener datos frescos)
  };

  /**
   * Manejo especial para Next.js 15.
   * 
   * Next.js 15 requiere la opción "duplex" cuando se envía un body
   * en requests POST, PUT o PATCH. Esto es un requisito del nuevo
   * sistema de streams de Next.js.
   * 
   * Sin esto, se obtiene el error:
   * "TypeError: RequestInit: duplex option is required when sending a body"
   */
  if (init.body && (init.method === "POST" || init.method === "PUT" || init.method === "PATCH")) {
    fetchOptions.duplex = "half";  // Requerido por Next.js 15 para requests con body
  }

  // Hacer la petición al backend
  const r = await fetch(url, fetchOptions);

  // Leer la respuesta como texto primero
  // Esto permite manejar respuestas vacías o no-JSON de forma segura
  const text = await r.text();

  /**
   * Manejo de respuestas vacías.
   * 
   * Algunos endpoints pueden retornar 204 No Content o respuestas vacías.
   * Necesitamos manejarlas antes de intentar parsear JSON.
   */
  if (!text || text.trim() === "") {
    // Si la respuesta está vacía pero el status no es exitoso, retornar error
    if (!r.ok) {
      return NextResponse.json(
        { detail: "Empty response from backend" },
        { status: r.status }
      );
    }
    // Si es exitosa y vacía, retornar objeto vacío
    // Esto es común en DELETE requests o algunos POST que no retornan datos
    return NextResponse.json({});
  }

  /**
   * Parsing seguro de JSON.
   * 
   * Intentamos parsear la respuesta como JSON.
   * Si falla (no es JSON válido), retornamos un error con el texto crudo.
   * 
   * Esto puede pasar si:
   * - El backend retorna HTML (error 500, página de error)
   * - El backend retorna texto plano
   * - Hay un error de red que retorna HTML de error
   */
  let json: any = null;
  try {
    json = JSON.parse(text);
  } catch {
    // Si no es JSON válido, retornar error con el texto crudo
    // Esto ayuda a debuggear qué está retornando el backend
    return NextResponse.json(
      { detail: "Invalid response from backend", raw: text },
      { status: r.status }
    );
  }

  /**
   * Manejo de errores del backend.
   * 
   * Si el status code no es exitoso (200-299), retornar el error
   * con el status code original del backend.
   * 
   * El backend Django REST Framework retorna errores en formato:
   * { "detail": "mensaje de error" }
   * o
   * { "field": ["error1", "error2"] } para errores de validación
   */
  if (!r.ok) {
    // Si json es null o no tiene detail, intentar extraer información útil
    if (!json || typeof json !== 'object') {
      return NextResponse.json(
        { 
          detail: `Backend error: ${r.status} ${r.statusText}`,
          status: r.status,
          statusText: r.statusText
        },
        { status: r.status }
      );
    }
    
    // Si json tiene detail o message, usarlo; si no, usar el objeto completo
    const errorDetail = json.detail || json.message || JSON.stringify(json);
    return NextResponse.json(
      { 
        detail: errorDetail,
        ...json  // Incluir toda la información del error del backend
      },
      { status: r.status }
    );
  }

  // Si todo está bien, retornar el JSON parseado
  return NextResponse.json(json);
}
