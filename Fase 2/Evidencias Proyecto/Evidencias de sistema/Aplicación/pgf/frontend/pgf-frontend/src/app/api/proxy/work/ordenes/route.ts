import { NextRequest } from "next/server";
import { proxyFetch } from "../../utils";

/**
 * Proxy route para gestión de órdenes de trabajo.
 * 
 * GET /api/proxy/work/ordenes/ - Listar OTs
 * POST /api/proxy/work/ordenes/ - Crear OT
 */
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const queryString = searchParams.toString();
  const url = queryString ? `/work/ordenes/?${queryString}` : "/work/ordenes/";
  return proxyFetch(url);
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    return proxyFetch("/work/ordenes/", {
      method: "POST",
      body: JSON.stringify(body),
    });
  } catch (error) {
    console.error("Error parsing request body:", error);
    return proxyFetch("/work/ordenes/", {
      method: "POST",
      body: await request.text(),
    });
  }
}

