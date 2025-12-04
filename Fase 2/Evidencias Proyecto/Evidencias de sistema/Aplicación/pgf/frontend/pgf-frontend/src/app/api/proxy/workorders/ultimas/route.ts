import { proxyFetch } from "../../utils";

export async function GET() {
  return proxyFetch("/work/ordenes/?ordering=-id&limit=5");
}

// import { NextRequest, NextResponse } from "next/server";
// import { cookies } from "next/headers";

// const API_BASE = process.env.API_BASE ?? "http://api:8000/api/v1";

// export async function GET() {
//   try {
//     const cookieStore = await cookies();
//     const token = cookieStore.get("pgf_access")?.value;

//     if (!token)
//       return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });

//     const r = await fetch(`${API_BASE}/work/ordenes/?ordering=-id&limit=5`, {
//       headers: { Authorization: `Bearer ${token}` },
//       cache: "no-store",
//     });

//     if (!r.ok) return NextResponse.json({ detail: "Error" }, { status: r.status });

//     const data = await r.json();
//     return NextResponse.json(data.results ?? []);
//   } catch (e) {
//     console.error(e);
//     return NextResponse.json({ detail: "Server error" }, { status: 500 });
//   }
// }
