import { NextRequest } from "next/server";

/**
 * Proxy route para subir evidencias directamente al backend.
 * El backend se encarga de subirlas a S3.
 * 
 * POST /api/proxy/work/evidencias/presigned/
 * 
 * El frontend envía FormData con el archivo y metadatos.
 * Este proxy route reenvía el FormData al backend.
 */
export async function POST(request: NextRequest) {
  try {
    // Intentar leer como FormData (el frontend siempre envía FormData ahora)
    const formData = await request.formData();
    const backend = process.env.NEXT_PUBLIC_API_BASE_URL || "http://api:8000";
    const token = request.cookies.get("pgf_access")?.value;
    
    if (!token) {
      return Response.json(
        { detail: "No autenticado" },
        { status: 401 }
      );
    }
    
    // Crear nuevo FormData para enviar al backend
    const backendFormData = new FormData();
    for (const [key, value] of formData.entries()) {
      backendFormData.append(key, value);
    }
    
    const response = await fetch(`${backend}/api/v1/work/evidencias/presigned/`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        // No establecer Content-Type, el navegador lo hará automáticamente con el boundary correcto
      },
      body: backendFormData,
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      let errorData;
      try {
        errorData = JSON.parse(errorText);
      } catch {
        errorData = { detail: errorText || "Error al subir evidencia" };
      }
      return Response.json(errorData, {
        status: response.status,
      });
    }
    
    const data = await response.json();
    return Response.json(data);
  } catch (error) {
    console.error("Error en proxy de evidencias:", error);
    return Response.json(
      { detail: `Error al subir evidencia: ${error instanceof Error ? error.message : "Error desconocido"}` },
      { status: 500 }
    );
  }
}

