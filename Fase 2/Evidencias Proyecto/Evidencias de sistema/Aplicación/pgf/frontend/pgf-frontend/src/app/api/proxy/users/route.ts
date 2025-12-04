import { NextRequest } from "next/server";
import { proxyFetch } from "../utils";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const queryString = searchParams.toString();
  const url = queryString ? `/users/?${queryString}` : "/users/";
  return proxyFetch(url);
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  return proxyFetch("/users/", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
// import { NextResponse as Response } from "next/server";

// import { cookies } from "next/headers";
// import { ENDPOINTS } from "@/lib/constants";
// import { proxyFetch } from "../utils";


// export async function GET() {
  
//   const cookieStore = await cookies();
//   const token = cookieStore.get("pgf_token")?.value;

//   if (!token)
//     return Response.json({ detail: "Unauthorized" }, { status: 401 });

//   const r = await fetch(ENDPOINTS.USERS, {
//     headers: {
//       Authorization: `Bearer ${token}`,
//     },
//     cache: "no-store",
//   });

//   return Response.json(await r.json(), { status: r.status });
  
// }

// export async function POST(req: Request) {
//   const cookieStore = await cookies();
//   const token = cookieStore.get("pgf_token")?.value;

//   if (!token)
//     return Response.json({ detail: "Unauthorized" }, { status: 401 });

//   const body = await req.json();

//   const r = await fetch(ENDPOINTS.USERS, {
//     method: "POST",
//     headers: {
//       Authorization: `Bearer ${token}`,
//       "Content-Type": "application/json",
//     },
//     body: JSON.stringify(body),
//   });

//   return Response.json(await r.json(), { status: r.status });
// }
