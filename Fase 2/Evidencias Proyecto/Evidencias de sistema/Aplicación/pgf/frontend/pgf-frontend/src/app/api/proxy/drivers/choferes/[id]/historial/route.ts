import { NextRequest, NextResponse } from "next/server";
import { proxyFetch } from "../../../../utils";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  return proxyFetch(`/drivers/choferes/${id}/historial/`, {
    method: "GET",
  });
}

