import { NextRequest } from "next/server";
import { proxyFetch } from "../../utils";

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const patente = searchParams.get("patente");
    const endpoint = patente
      ? `/vehicles/ingresos-hoy/?patente=${encodeURIComponent(patente)}`
      : "/vehicles/ingresos-hoy/";
    return proxyFetch(endpoint, {
      method: "GET",
    });
  } catch (error) {
    console.error("Error en proxy de ingresos-hoy:", error);
    return Response.json(
      { detail: `Error al obtener ingresos del día: ${error instanceof Error ? error.message : "Error desconocido"}` },
      { status: 500 }
    );
  }
}

