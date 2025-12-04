import { NextRequest } from "next/server";
import { handleBackendResponse } from "../utils";

export async function POST(req: NextRequest) {
  try {
    const backend = process.env.NEXT_PUBLIC_API_BASE_URL || "http://api:8000";
    const token = req.cookies.get("pgf_access")?.value;
    const body = await req.json();

    const r = await fetch(`${backend}/api/v1/work/items/`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    return handleBackendResponse(r);
  } catch (error) {
    console.error("Error in /api/work/items/create:", error);
    return Response.json(
      { detail: "Failed to create item", error: String(error) },
      { status: 500 }
    );
  }
}
