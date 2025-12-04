import { NextRequest } from "next/server";
import { proxyFetch } from "../../../../utils";

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ id: string; action: string[] }> }
) {
  try {
    const { id, action } = await params;
    const actionPath = action.join("/");
    const body = await req.json().catch(() => ({}));
    
    return proxyFetch(`/inventory/solicitudes/${id}/${actionPath}/`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  } catch (error) {
    console.error("Error in /api/proxy/inventory/solicitudes/[id]/[...action]:", error);
    const { id, action } = await params;
    const actionPath = action.join("/");
    return proxyFetch(`/inventory/solicitudes/${id}/${actionPath}/`, {
      method: "POST",
      body: await req.text().catch(() => "{}"),
    });
  }
}

