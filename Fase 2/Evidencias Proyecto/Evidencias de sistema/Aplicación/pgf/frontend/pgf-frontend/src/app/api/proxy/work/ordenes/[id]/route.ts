import { NextRequest } from "next/server";
import { proxyFetch } from "../../../utils";

/**
 * Proxy route para operaciones CRUD en una OT específica.
 * 
 * GET /api/proxy/work/ordenes/[id]/ - Obtener OT
 * PUT /api/proxy/work/ordenes/[id]/ - Actualizar OT completa
 * PATCH /api/proxy/work/ordenes/[id]/ - Actualizar OT parcial
 * DELETE /api/proxy/work/ordenes/[id]/ - Eliminar OT
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  return proxyFetch(`/work/ordenes/${id}/`);
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  try {
    const body = await request.json();
    return proxyFetch(`/work/ordenes/${id}/`, {
      method: "PUT",
      body: JSON.stringify(body),
    });
  } catch (error) {
    console.error("Error parsing request body:", error);
    return proxyFetch(`/work/ordenes/${id}/`, {
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
    return proxyFetch(`/work/ordenes/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  } catch (error) {
    console.error("Error parsing request body:", error);
    return proxyFetch(`/work/ordenes/${id}/`, {
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
  return proxyFetch(`/work/ordenes/${id}/`, {
    method: "DELETE",
  });
}

