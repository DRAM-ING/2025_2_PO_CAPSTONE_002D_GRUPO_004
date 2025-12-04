import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  const body = await request.json();
  
  // Este endpoint NO requiere autenticación
  const backend = process.env.NEXT_PUBLIC_API_BASE_URL || "http://api:8000";
  
  try {
    const r = await fetch(`${backend}/api/v1/auth/password-reset/confirm/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const text = await r.text();
    
    if (!text || text.trim() === "") {
      return NextResponse.json(
        { detail: "Empty response from backend" },
        { status: r.status || 500 }
      );
    }

    let data;
    try {
      data = JSON.parse(text);
    } catch {
      return NextResponse.json(
        { detail: "Invalid response from backend", raw: text },
        { status: r.status || 500 }
      );
    }

    return NextResponse.json(data, { status: r.status });
  } catch (error) {
    console.error("Error in /api/auth/password-reset/confirm/public:", error);
    return NextResponse.json(
      { detail: "Failed to process request", error: String(error) },
      { status: 500 }
    );
  }
}

