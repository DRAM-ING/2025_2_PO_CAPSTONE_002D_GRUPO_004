import { NextResponse } from "next/server";

/**
 * Safely parses JSON from a fetch Response
 * Handles empty responses, HTML errors, and invalid JSON gracefully
 */
export async function safeJsonParse(response: Response): Promise<any> {
  const text = await response.text();
  
  // Handle empty responses
  if (!text || text.trim() === "") {
    if (!response.ok) {
      return { detail: "Empty response from backend" };
    }
    return {};
  }
  
  // Detect HTML responses (error pages from Django)
  const trimmedText = text.trim();
  if (trimmedText.startsWith("<!DOCTYPE") || trimmedText.startsWith("<html") || trimmedText.startsWith("<!doctype")) {
    console.error("Backend retornó HTML en lugar de JSON:", trimmedText.substring(0, 300));
    
    // Intentar extraer información útil del HTML si es posible
    let errorMessage = "Error del servidor. El backend retornó una página de error.";
    
    // Buscar mensajes de error comunes en el HTML
    const errorMatch = trimmedText.match(/<title[^>]*>([^<]+)<\/title>/i) || 
                      trimmedText.match(/<h1[^>]*>([^<]+)<\/h1>/i) ||
                      trimmedText.match(/<p[^>]*>([^<]+)<\/p>/i);
    
    if (errorMatch && errorMatch[1]) {
      errorMessage = `Error del servidor: ${errorMatch[1]}`;
    }
    
    return { 
      detail: errorMessage,
      html_response: true,
      status: response.status || 500
    };
  }
  
  try {
    return JSON.parse(text);
  } catch (e) {
    console.error("Invalid JSON response:", text.substring(0, 200));
    return { 
      detail: "Respuesta inválida del servidor. Por favor contacta al administrador.", 
      raw: text.substring(0, 200) 
    };
  }
}

/**
 * Helper to handle backend fetch responses with proper error handling
 */
export async function handleBackendResponse(response: Response): Promise<NextResponse> {
  const data = await safeJsonParse(response);
  
  // If HTML response detected, return error with appropriate status
  if (data.html_response) {
    return NextResponse.json(
      { 
        detail: data.detail || "Error del servidor. Por favor contacta al administrador.",
        status: data.status || response.status || 500
      }, 
      { status: data.status || response.status || 500 }
    );
  }
  
  // If JSON parsing failed, return error
  if (data.detail && (data.detail.includes("Invalid JSON") || data.detail.includes("Respuesta inválida"))) {
    return NextResponse.json(data, { status: response.status || 500 });
  }
  
  return NextResponse.json(data, { status: response.status });
}

