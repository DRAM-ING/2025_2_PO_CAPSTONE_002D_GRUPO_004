import { NextRequest } from "next/server";
import { proxyFetch } from "../../utils";

/**
 * Proxy route para marcar todas las notificaciones como leídas.
 * 
 * POST /api/proxy/notifications/marcar-todas-leidas/
 */
export async function POST(request: NextRequest) {
  try {
    return proxyFetch("/notifications/marcar-todas-leidas/", {
      method: "POST",
    });
  } catch (error) {
    console.error("Error en proxy de marcar todas como leídas:", error);
    return Response.json(
      { detail: `Error al marcar notificaciones: ${error instanceof Error ? error.message : "Error desconocido"}` },
      { status: 500 }
    );
  }
}

