import { cookies } from "next/headers";
import { NextResponse } from "next/server";

/**
 * Endpoint para obtener el token de acceso para WebSocket.
 * 
 * Este endpoint lee la cookie HttpOnly "pgf_access" del servidor
 * y la devuelve al cliente para que pueda usarla en el WebSocket.
 * 
 * Esto es necesario porque las cookies HttpOnly no son accesibles
 * desde JavaScript en el navegador.
 */
export async function GET() {
  try {
    const cookieStore = await cookies();
    const token = cookieStore.get("pgf_access")?.value;

    if (!token) {
      return NextResponse.json(
        { error: "No token found" },
        { status: 401 }
      );
    }

    return NextResponse.json({ token });
  } catch (error) {
    console.error("Error in /api/auth/token:", error);
    return NextResponse.json(
      { error: "Failed to get token" },
      { status: 500 }
    );
  }
}

