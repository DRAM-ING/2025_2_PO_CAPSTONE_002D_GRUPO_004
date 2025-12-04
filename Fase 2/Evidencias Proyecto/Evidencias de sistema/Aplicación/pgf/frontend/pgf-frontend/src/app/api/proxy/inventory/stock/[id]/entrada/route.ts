import { NextRequest } from "next/server";
import { proxyFetch } from "../../../utils";

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const body = await req.json();
    return proxyFetch(`/inventory/stock/${id}/entrada/`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  } catch (error) {
    console.error("Error parsing request body:", error);
    const { id } = await params;
    return proxyFetch(`/inventory/stock/${id}/entrada/`, {
      method: "POST",
      body: await req.text(),
    });
  }
}

