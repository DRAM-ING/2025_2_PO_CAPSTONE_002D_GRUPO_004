import { NextRequest, NextResponse } from "next/server";
import { proxyFetch } from "../../../../utils";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const body = await request.json();
  return proxyFetch(`/work/ordenes/${id}/aprobar-asignacion/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

