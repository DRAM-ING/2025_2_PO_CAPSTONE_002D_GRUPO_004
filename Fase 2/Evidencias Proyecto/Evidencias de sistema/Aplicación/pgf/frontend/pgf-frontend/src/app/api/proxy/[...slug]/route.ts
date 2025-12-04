import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

const API_HOST = process.env.NEXT_PUBLIC_API_BASE_URL || "http://api:8000";
const API_BASE = `${API_HOST}/api/v1`;

export async function GET(req: NextRequest, ctx: any) {
  return handler(req, ctx);
}
export async function POST(req: NextRequest, ctx: any) {
  return handler(req, ctx);
}
export async function PUT(req: NextRequest, ctx: any) {
  return handler(req, ctx);
}
export async function PATCH(req: NextRequest, ctx: any) {
  return handler(req, ctx);
}
export async function DELETE(req: NextRequest, ctx: any) {
  return handler(req, ctx);
}

async function handler(req: NextRequest, ctx: any) {

  // Next.js 15: params es PROMESA
  const params = await ctx.params;

  // SIEMPRE forzar que exista "/"
  let slug = Array.isArray(params.slug) ? params.slug.join("/") : params.slug;
  if (!slug.endsWith("/")) slug += "/";

  // mantener ?query
  const search = req.nextUrl.search ?? "";

  // cookies httpOnly
  const cookieStore = await cookies();
  const access = cookieStore.get("pgf_access")?.value;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (access) {
    headers["Authorization"] = `Bearer ${access}`;
  }

  const url = `${API_BASE}/${slug}${search}`;

  const options: any = {
    method: req.method,
    headers,
  };

  if (["POST", "PUT", "PATCH"].includes(req.method)) {
    options.body = await req.text();
  }

  const backend = await fetch(url, options);

  const text = await backend.text();

  // Si el status es 204 (No Content), retornar sin body
  if (backend.status === 204) {
    return new NextResponse(null, { status: 204 });
  }

  // si backend devolvió HTML → NO parsear
  if (text.startsWith("<")) {
    return new NextResponse(text, { status: backend.status });
  }

  // Si no hay contenido, retornar respuesta vacía
  if (!text || text.trim() === "") {
    return new NextResponse(null, { status: backend.status });
  }

  try {
    return NextResponse.json(JSON.parse(text), { status: backend.status });
  } catch {
    return new NextResponse(text, { status: backend.status });
  }
}
