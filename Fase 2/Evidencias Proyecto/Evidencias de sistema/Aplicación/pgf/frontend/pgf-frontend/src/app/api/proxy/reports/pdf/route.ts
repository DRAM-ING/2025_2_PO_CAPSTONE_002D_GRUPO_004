import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

const API_BASE = process.env.API_BASE ?? "http://api:8000/api/v1";

export async function GET(request: NextRequest) {
  try {
    // Obtener el token de las cookies
    const cookieStore = await cookies();
    const token = cookieStore.get("pgf_access")?.value;

    if (!token) {
      return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
    }

    // Construir la URL del endpoint
    const searchParams = request.nextUrl.searchParams;
    let endpoint = "/reports/pdf/";
    if (searchParams.toString()) {
      endpoint += `?${searchParams.toString()}`;
    }
    
    const url = `${API_BASE}${endpoint}`;

    // Hacer la petición directamente al backend sin usar proxyFetch
    // porque proxyFetch convierte todo a texto/JSON y corrompe el PDF binario
    const response = await fetch(url, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      cache: "no-store",
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = "Error al generar PDF";
      try {
        const errorJson = JSON.parse(errorText);
        errorMessage = errorJson.detail || errorMessage;
      } catch {
        errorMessage = errorText || errorMessage;
      }
      return NextResponse.json(
        { detail: errorMessage },
        { status: response.status }
      );
    }

    // Obtener el PDF como ArrayBuffer para preservar los datos binarios
    const arrayBuffer = await response.arrayBuffer();
    
    // Obtener headers del backend
    const contentType = response.headers.get("content-type") || "application/pdf";
    const contentDisposition = response.headers.get("content-disposition") || 'attachment; filename="reporte.pdf"';

    // Retornar el PDF como respuesta binaria
    return new NextResponse(arrayBuffer, {
      status: 200,
      headers: {
        "Content-Type": contentType,
        "Content-Disposition": contentDisposition,
      },
    });
  } catch (error) {
    console.error("Error al generar PDF:", error);
    return NextResponse.json(
      { detail: "Error al generar PDF: " + (error instanceof Error ? error.message : "Error desconocido") },
      { status: 500 }
    );
  }
}

