import { NextRequest } from "next/server";
import { proxyFetch } from "../../utils";

/**
 * Proxy route para gestión de evidencias.
 * 
 * GET /api/proxy/work/evidencias/ - Listar evidencias
 * POST /api/proxy/work/evidencias/ - Crear evidencia
 */
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const queryString = searchParams.toString();
  const url = queryString ? `/work/evidencias/?${queryString}` : "/work/evidencias/";
  return proxyFetch(url);
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    return proxyFetch("/work/evidencias/", {
      method: "POST",
      body: JSON.stringify(body),
    });
  } catch (error) {
    console.error("Error parsing request body:", error);
    return proxyFetch("/work/evidencias/", {
      method: "POST",
      body: await request.text(),
    });
  }
}

