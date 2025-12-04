import { NextRequest, NextResponse } from "next/server";
import { proxyFetch } from "../../../../utils";

/**
 * Proxy route para descargar evidencias.
 * 
 * GET /api/proxy/work/evidencias/{id}/download/ - Obtener URL presignada o descargar evidencia directamente
 * 
 * Si el backend devuelve use_proxy=true, este endpoint descarga el archivo desde LocalStack
 * y lo sirve al frontend, evitando problemas de Mixed Content (HTTPS -> HTTP).
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    
    // Hacer la petición directamente al backend (no usar proxyFetch porque puede devolver binario)
    const { cookies } = await import("next/headers");
    const cookieStore = await cookies();
    const token = cookieStore.get("pgf_access")?.value;
    
    if (!token) {
      return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
    }
    
    const API_BASE = process.env.API_BASE ?? "http://api:8000/api/v1";
    const url = `${API_BASE}/work/evidencias/${id}/download/`;
    
    // Hacer la petición directamente
    const backendResponse = await fetch(url, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}`,
      },
      cache: "no-store",
    });
    
    if (!backendResponse.ok) {
      // Si hay error, intentar obtener el mensaje de error
      const errorText = await backendResponse.text();
      let errorData;
      try {
        errorData = JSON.parse(errorText);
      } catch {
        errorData = { detail: errorText || `Error ${backendResponse.status}` };
      }
      return NextResponse.json(errorData, { status: backendResponse.status });
    }
    
    // Verificar si el backend devolvió el archivo directamente o JSON con URL
    const contentType = backendResponse.headers.get("content-type") || "";
    
    // Si el backend devolvió el archivo directamente (imagen, PDF, etc.)
    if (contentType.startsWith("image/") || contentType.includes("pdf") || contentType.includes("application/octet-stream") || contentType.includes("application/") || contentType.includes("text/")) {
      // El backend ya sirvió el archivo directamente, solo pasarlo al frontend
      const arrayBuffer = await backendResponse.arrayBuffer();
      
      return new NextResponse(arrayBuffer, {
        status: 200,
        headers: {
          "Content-Type": contentType,
          "Content-Disposition": backendResponse.headers.get("content-disposition") || `inline; filename="evidencia-${id}"`,
          "Cache-Control": backendResponse.headers.get("cache-control") || "public, max-age=3600",
        },
      });
    }
    
    // Si el backend devolvió JSON con URL presignada
    const text = await backendResponse.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch (e) {
      // Si no es JSON, puede ser que el backend devolvió el archivo pero con content-type incorrecto
      // Intentar servir como binario
      const arrayBuffer = await backendResponse.arrayBuffer();
      return new NextResponse(arrayBuffer, {
        status: 200,
        headers: {
          "Content-Type": "application/octet-stream",
          "Content-Disposition": `inline; filename="evidencia-${id}"`,
          "Cache-Control": "public, max-age=3600",
        },
      });
    }
    
    // Si el backend indica que debemos usar el proxy (use_proxy=true)
    // descargar el archivo desde LocalStack y servirlo al frontend
    if (data.use_proxy && data.direct_url) {
      try {
        // Descargar el archivo desde LocalStack usando la URL directa
        const fileResponse = await fetch(data.direct_url, {
          method: "GET",
          // No incluir credentials para evitar problemas de CORS
        });
        
        if (!fileResponse.ok) {
          // Si falla la descarga directa, devolver error
          return NextResponse.json(
            { detail: "Error al descargar el archivo de evidencia" },
            { status: fileResponse.status }
          );
        }
        
        // Obtener el contenido del archivo
        const blob = await fileResponse.blob();
        const arrayBuffer = await blob.arrayBuffer();
        
        // Obtener el Content-Type del archivo original
        const fileContentType = fileResponse.headers.get("content-type") || blob.type || "application/octet-stream";
        
        // Devolver el archivo al frontend
        return new NextResponse(arrayBuffer, {
          status: 200,
          headers: {
            "Content-Type": fileContentType,
            "Content-Disposition": `inline; filename="evidencia-${id}"`,
            "Cache-Control": "public, max-age=3600", // Cache por 1 hora
          },
        });
      } catch (error) {
        console.error("Error al descargar archivo desde LocalStack:", error);
        // Si falla, devolver la URL presignada como fallback
        return NextResponse.json(data);
      }
    }
    
    // Si no se requiere proxy, devolver la respuesta del backend tal cual
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error in proxy for evidence download:", error);
    return NextResponse.json(
      { detail: "Error en el proxy para descarga de evidencia" },
      { status: 500 }
    );
  }
}

