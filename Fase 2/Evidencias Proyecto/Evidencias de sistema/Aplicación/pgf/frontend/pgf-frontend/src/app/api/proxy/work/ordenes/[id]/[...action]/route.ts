import { NextRequest } from "next/server";
import { proxyFetch } from "../../../../utils";

/**
 * Proxy route dinámico para acciones de cambio de estado en OTs.
 * 
 * Maneja endpoints como:
 * - POST /api/proxy/work/ordenes/[id]/en-ejecucion/
 * - POST /api/proxy/work/ordenes/[id]/en-pausa/
 * - POST /api/proxy/work/ordenes/[id]/en-qa/
 * - POST /api/proxy/work/ordenes/[id]/reanudar/
 * - POST /api/proxy/work/ordenes/[id]/cerrar/
 * - etc.
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string; action: string[] }> }
) {
  const { id, action } = await params;
  // Construir el path de la acción (ej: "en-ejecucion" o ["esperando", "repuestos"])
  const actionPath = action.join("/");
  
  // Construir el endpoint completo
  const endpoint = `/work/ordenes/${id}/${actionPath}/`;
  
  // Intentar obtener el body si existe (algunas acciones pueden necesitarlo)
  let body = null;
  try {
    const text = await request.text();
    if (text && text.trim()) {
      body = JSON.parse(text);
    }
  } catch {
    // Si no hay body o no es JSON válido, enviar sin body
    body = null;
  }
  
  // Construir opciones para proxyFetch
  const options: any = {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  };
  
  // Solo agregar body si existe
  if (body !== null) {
    options.body = JSON.stringify(body);
  }
  
  return proxyFetch(endpoint, options);
}

