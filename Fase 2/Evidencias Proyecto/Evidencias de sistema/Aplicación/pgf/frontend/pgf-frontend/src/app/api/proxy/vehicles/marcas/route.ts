import { NextRequest } from "next/server";
import { proxyFetch } from "../../utils";

export async function GET(req: NextRequest) {
  try {
    const response = await proxyFetch("/vehicles/marcas/");
    return response;
  } catch (error) {
    console.error("Error en proxy de marcas:", error);
    return new Response(
      JSON.stringify({ detail: "Error al obtener marcas", error: String(error) }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
}

