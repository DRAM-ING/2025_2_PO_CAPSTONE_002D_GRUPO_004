import { NextRequest } from "next/server";
import { handleBackendResponse } from "../utils";

export async function GET(req: NextRequest) {
  try {
    const backend = process.env.NEXT_PUBLIC_API_BASE_URL || "http://api:8000";
    const token = req.cookies.get("pgf_access")?.value;

    const url = new URL(req.url);
    const qs = url.searchParams.toString();

    const r = await fetch(`${backend}/api/v1/work/ordenes/?${qs}`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    return handleBackendResponse(r);
  } catch (error) {
    console.error("Error in /api/work/ordenes:", error);
    return Response.json(
      { detail: "Failed to fetch ordenes", error: String(error) },
      { status: 500 }
    );
  }
}
