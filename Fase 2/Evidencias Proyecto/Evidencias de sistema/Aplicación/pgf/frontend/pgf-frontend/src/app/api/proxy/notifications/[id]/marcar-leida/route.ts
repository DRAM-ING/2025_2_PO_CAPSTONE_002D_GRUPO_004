import { NextRequest } from "next/server";
import { proxyFetch } from "../../../utils";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  return proxyFetch(`/notifications/${id}/marcar-leida/`, {
    method: "POST",
  });
}

