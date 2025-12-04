import { NextRequest } from "next/server";
import { handleBackendResponse } from "../../../utils";

export async function POST(req: NextRequest, context: any) {
  try {
    const backend = process.env.NEXT_PUBLIC_API_BASE_URL || "http://api:8000";
    const token = req.cookies.get("pgf_access")?.value;

    const { id, accion } = context.params;

    const r = await fetch(`${backend}/api/v1/work/aprobaciones/${id}/${accion}/`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });

    return handleBackendResponse(r);
  } catch (error) {
    console.error("Error in /api/work/aprobaciones/[id]/[accion]:", error);
    return Response.json(
      { detail: "Failed to execute aprobacion action", error: String(error) },
      { status: 500 }
    );
  }
}
