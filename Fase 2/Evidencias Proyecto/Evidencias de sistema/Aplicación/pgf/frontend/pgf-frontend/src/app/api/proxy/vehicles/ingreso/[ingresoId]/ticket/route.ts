import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { API_BASE } from "../../../../utils";

/**
 * Proxy endpoint para generar PDF del ticket de ingreso.
 * 
 * GET /api/proxy/vehicles/ingreso/[ingresoId]/ticket/
 * 
 * Genera un PDF del ticket de ingreso de un vehículo.
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ ingresoId: string }> }
) {
  try {
    const { ingresoId } = await params;
    const cookieStore = await cookies();
    const token = cookieStore.get("pgf_access")?.value;

    if (!token) {
      return NextResponse.json(
        { detail: "No autenticado" },
        { status: 401 }
      );
    }

    // Llamar al backend
    const backendUrl = `${API_BASE}/vehicles/ingreso/${ingresoId}/ticket/`;
    const response = await fetch(backendUrl, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      cache: "no-store",
    });

    if (!response.ok) {
      // Intentar leer como JSON primero
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        const error = await response.json().catch(() => ({ detail: "Error al generar ticket" }));
        return NextResponse.json(error, { status: response.status });
      }
      // Si no es JSON, retornar error genérico
      return NextResponse.json(
        { detail: `Error ${response.status}: ${response.statusText}` },
        { status: response.status }
      );
    }

    // Retornar el PDF
    const pdfBuffer = await response.arrayBuffer();
    return new NextResponse(pdfBuffer, {
      status: 200,
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `inline; filename="ticket_ingreso_${ingresoId.slice(0, 8)}.pdf"`,
      },
    });
  } catch (error) {
    console.error("Error en proxy de ticket de ingreso:", error);
    return NextResponse.json(
      { detail: "Error interno del servidor" },
      { status: 500 }
    );
  }
}

