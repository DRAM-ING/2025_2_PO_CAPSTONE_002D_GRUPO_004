import { proxyFetch } from "../../../../utils";
import { NextRequest } from "next/server";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const formData = await request.formData();
  return proxyFetch(`/vehicles/${id}/ingreso/evidencias/`, {
    method: "POST",
    body: formData,
  });
}

