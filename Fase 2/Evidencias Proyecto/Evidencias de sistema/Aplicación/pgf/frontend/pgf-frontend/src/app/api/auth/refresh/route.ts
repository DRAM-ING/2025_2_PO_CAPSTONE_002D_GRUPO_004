import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const backend = process.env.NEXT_PUBLIC_API_BASE_URL || "http://api:8000";

    const r = await fetch(`${backend}/api/v1/auth/refresh/`, {
      method: "POST",
      credentials: "include",
    });

    const text = await r.text();

    // Handle empty responses
    if (!text || text.trim() === "") {
      return NextResponse.json(
        { detail: "Empty response from backend" },
        { status: r.status || 500 }
      );
    }

    // Check if response is JSON
    if (!text.trim().startsWith("{")) {
      return NextResponse.json(
        { detail: "Respuesta inválida del backend", raw: text },
        { status: r.status || 500 }
      );
    }

    let data;
    try {
      data = JSON.parse(text);
    } catch (e) {
      return NextResponse.json(
        { detail: "Invalid JSON response from backend", raw: text },
        { status: r.status || 500 }
      );
    }

    if (!r.ok) {
      return NextResponse.json(data, { status: r.status || 401 });
    }

    // Validate that we have an access token
    if (!data.access) {
      return NextResponse.json(
        { detail: "No access token in response" },
        { status: 500 }
      );
    }

    // Crear respuesta
    const res = NextResponse.json({ ok: true });

    // Guardar nuevo access token
    res.cookies.set("pgf_access", data.access, {
      httpOnly: true,
      sameSite: "lax",
      secure: false,
      path: "/",
      maxAge: 60 * 60,
    });

    return res;
  } catch (error) {
    console.error("Error in /api/auth/refresh:", error);
    return NextResponse.json(
      { detail: "Failed to refresh token", error: String(error) },
      { status: 500 }
    );
  }
}
