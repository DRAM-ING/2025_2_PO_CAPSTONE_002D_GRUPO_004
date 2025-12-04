import { NextRequest } from "next/server";
import { proxyFetch } from "../../../../utils";

/**
 * Proxy route para reanudar una pausa.
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  return proxyFetch(`/work/pausas/${id}/reanudar/`, {
    method: "POST",
  });
}

