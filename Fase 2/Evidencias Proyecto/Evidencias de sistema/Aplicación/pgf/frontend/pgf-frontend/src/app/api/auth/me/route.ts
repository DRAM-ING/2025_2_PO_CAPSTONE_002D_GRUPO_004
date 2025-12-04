import { cookies } from "next/headers";
import { ENDPOINTS } from "@/lib/constants";

export async function GET() {
  const cookieStore = await cookies();
  const token = cookieStore.get("pgf_access")?.value;

  if (!token)
    return Response.json({ detail: "Unauthorized" }, { status: 401 });

  try {
    // Usar el endpoint correcto: /api/v1/users/me/ (definido en UserViewSet.me)
    const backend = process.env.NEXT_PUBLIC_API_BASE_URL || "http://api:8000";
    const r = await fetch(`${backend}/api/v1/users/me/`, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    const text = await r.text();
    
    // Handle empty responses
    if (!text || text.trim() === "") {
      return Response.json({ detail: "Empty response from backend" }, { status: r.status || 500 });
    }

    let json;
    try {
      json = JSON.parse(text);
    } catch (e) {
      return Response.json(
        { detail: "Invalid JSON response from backend", raw: text },
        { status: r.status || 500 }
      );
    }

    return Response.json(json, { status: r.status });
  } catch (error) {
    console.error("Error in /api/auth/me:", error);
    return Response.json(
      { detail: "Failed to fetch user data", error: String(error) },
      { status: 500 }
    );
  }
}
