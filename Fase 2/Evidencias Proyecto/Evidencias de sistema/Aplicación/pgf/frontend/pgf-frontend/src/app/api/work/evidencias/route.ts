
import { NextRequest } from "next/server";
import { handleBackendResponse } from "../utils";

export async function GET(req: NextRequest) {
  try {
    const backend = process.env.NEXT_PUBLIC_API_BASE_URL || "http://api:8000";
    const token = req.cookies.get("pgf_access")?.value;
    const qs = new URL(req.url).searchParams.toString();

    const r = await fetch(`${backend}/api/v1/work/evidencias/?${qs}`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    return handleBackendResponse(r);
  } catch (error) {
    console.error("Error in /api/work/evidencias:", error);
    return Response.json(
      { detail: "Failed to fetch evidencias", error: String(error) },
      { status: 500 }
    );
  }
}
