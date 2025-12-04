import { NextRequest } from "next/server";
import { proxyFetch } from "../../../../utils";

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  return proxyFetch(`/work/evidencias/${id}/invalidar/`, {
    method: "POST",
    body: await req.text(),
  });
}

