import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    // Manejar el caso de body vacío o inválido
    let body;
    try {
      body = await req.json();
    } catch (e) {
      return NextResponse.json(
        { detail: "Invalid request body. Expected JSON with username and password." },
        { status: 400 }
      );
    }

    const { username, password } = body || {};

    if (!username || !password) {
      return NextResponse.json(
        { detail: "Username and password are required." },
        { status: 400 }
      );
    }

    const backend = process.env.NEXT_PUBLIC_API_BASE_URL || "http://api:8000";

    const r = await fetch(`${backend}/api/v1/auth/login/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
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

    // --- Validación ---
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
      // Logging para debugging
      console.error("Login failed:", {
        status: r.status,
        statusText: r.statusText,
        data: data,
        text: text.substring(0, 200) // Primeros 200 caracteres
      });
      
      // Retornar mensaje de error más descriptivo
      const errorMessage = data.detail || data.message || data.error || "Error al iniciar sesión";
      return NextResponse.json({ detail: errorMessage }, { status: r.status || 401 });
    }

    // Validate required fields
    if (!data.access) {
      return NextResponse.json(
        { detail: "No access token in response" },
        { status: 500 }
      );
    }

    // --- Crear respuesta final ---
    const res = NextResponse.json({
      ok: true,
      user: data.user,
    });

    // --- SETEAR COOKIES CORRECTAS ---
    // Estas claves **deben coincidir** con lo que lee el proxy
    res.cookies.set("pgf_access", data.access, {
      httpOnly: true,
      sameSite: "lax",
      secure: false, // Importante: en localhost → false
      path: "/",
      maxAge: 60 * 60, // 1 hora
    });

    if (data.refresh) {
      res.cookies.set("pgf_refresh", data.refresh, {
        httpOnly: true,
        sameSite: "lax",
        secure: false, // Importante: evitar problemas en local
        path: "/",
        maxAge: 60 * 60 * 24 * 7, // 7 días
      });
    }

    return res;
  } catch (error) {
    console.error("Error in /api/auth/login:", error);
    return NextResponse.json(
      { detail: "Failed to login", error: String(error) },
      { status: 500 }
    );
  }
}
