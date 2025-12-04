import { NextRequest } from "next/server";
import { proxyFetch } from "../../utils";

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const queryString = searchParams.toString();
    const endpoint = queryString ? `/vehicles/ingresos-historial/?${queryString}` : "/vehicles/ingresos-historial/";
    
    return proxyFetch(endpoint, {
      method: "GET",
    });
  } catch (error) {
    console.error("Error en proxy de ingresos-historial:", error);
    return Response.json(
      { detail: `Error al obtener historial de ingresos: ${error instanceof Error ? error.message : "Error desconocido"}` },
      { status: 500 }
    );
  }
}

