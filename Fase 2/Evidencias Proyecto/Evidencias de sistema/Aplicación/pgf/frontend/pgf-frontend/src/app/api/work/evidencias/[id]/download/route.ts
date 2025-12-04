import { NextRequest, NextResponse } from "next/server";
import { handleBackendResponse } from "../utils";

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const backend = process.env.NEXT_PUBLIC_API_BASE_URL || "http://api:8000";
    const token = req.cookies.get("pgf_access")?.value;

    const r = await fetch(`${backend}/api/v1/work/evidencias/${id}/download/`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    return handleBackendResponse(r);
  } catch (error) {
    console.error("Error in /api/work/evidencias/[id]/download:", error);
    return NextResponse.json(
      { detail: "Failed to get download URL", error: String(error) },
      { status: 500 }
    );
  }
}

