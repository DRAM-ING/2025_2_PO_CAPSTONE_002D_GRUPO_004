import { NextRequest } from "next/server";
import { proxyFetch } from "../../../utils";

/**
 * Proxy route para gestión de evidencias individuales.
 * 
 * GET /api/proxy/work/evidencias/[id]/ - Ver evidencia
 * PUT /api/proxy/work/evidencias/[id]/ - Editar evidencia
 * PATCH /api/proxy/work/evidencias/[id]/ - Editar evidencia (parcial)
 * DELETE /api/proxy/work/evidencias/[id]/ - Eliminar evidencia
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  return proxyFetch(`/work/evidencias/${id}/`);
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  try {
    const body = await request.json();
    return proxyFetch(`/work/evidencias/${id}/`, {
      method: "PUT",
      body: JSON.stringify(body),
    });
  } catch (error) {
    console.error("Error parsing request body:", error);
    return proxyFetch(`/work/evidencias/${id}/`, {
      method: "PUT",
      body: await request.text(),
    });
  }
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  try {
    const body = await request.json();
    return proxyFetch(`/work/evidencias/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  } catch (error) {
    console.error("Error parsing request body:", error);
    return proxyFetch(`/work/evidencias/${id}/`, {
      method: "PATCH",
      body: await request.text(),
    });
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  return proxyFetch(`/work/evidencias/${id}/`, {
    method: "DELETE",
  });
}

