import { NextRequest } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const backend = process.env.NEXT_PUBLIC_API_BASE_URL || "http://api:8000";
    const token = req.cookies.get("pgf_access")?.value;

    if (!token) {
      return Response.json(
        { detail: "No autenticado. Por favor inicia sesión." },
        { status: 401 }
      );
    }

    const body = await req.json();

    const r = await fetch(`${backend}/api/v1/work/ordenes/`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    // Leer respuesta como texto primero para detectar HTML
    const text = await r.text();
    
    // Si la respuesta es HTML (error del servidor), retornar error JSON
    if (text.trim().startsWith("<!DOCTYPE") || text.trim().startsWith("<html")) {
      console.error("Backend retornó HTML en lugar de JSON:", text.substring(0, 200));
      return Response.json(
        { 
          detail: "Error del servidor. El backend retornó una página de error. Por favor contacta al administrador.",
          status: r.status 
        },
        { status: r.status || 500 }
      );
    }

    // Intentar parsear como JSON
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      // Si no es JSON válido, retornar el texto como error
      return Response.json(
        { 
          detail: text || "Error desconocido del servidor",
          status: r.status 
        },
        { status: r.status || 500 }
      );
    }

    // Si la respuesta no es exitosa, retornar el error JSON
    if (!r.ok) {
      return Response.json(
        { 
          detail: data.detail || data.message || "Error al crear la orden de trabajo",
          errors: data.errors || undefined,
          status: r.status 
        },
        { status: r.status }
      );
    }

    // Respuesta exitosa
    return Response.json(data, { status: r.status });
  } catch (error) {
    console.error("Error in /api/work/ordenes/create:", error);
    return Response.json(
      { 
        detail: error instanceof Error ? error.message : "Error desconocido al crear la orden de trabajo",
        error: String(error) 
      },
      { status: 500 }
    );
  }
}
