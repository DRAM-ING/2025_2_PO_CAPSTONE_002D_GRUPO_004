import { NextRequest } from "next/server";
import { proxyFetch } from "../../../../utils";

/**
 * Proxy route para cerrar una orden de trabajo.
 * 
 * POST /api/proxy/work/ordenes/{id}/cerrar/ - Cerrar una OT
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const body = await request.json();
  return proxyFetch(`/work/ordenes/${id}/cerrar/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

