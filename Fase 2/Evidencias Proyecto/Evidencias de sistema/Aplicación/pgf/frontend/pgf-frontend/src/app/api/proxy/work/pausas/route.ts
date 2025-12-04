import { NextRequest, NextResponse } from "next/server";
import { proxyFetch } from "../../utils";

/**
 * Proxy route para listar y crear pausas.
 */
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const queryString = searchParams.toString();
  const url = queryString ? `/work/pausas/?${queryString}` : "/work/pausas/";
  return proxyFetch(url);
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  return proxyFetch("/work/pausas/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

