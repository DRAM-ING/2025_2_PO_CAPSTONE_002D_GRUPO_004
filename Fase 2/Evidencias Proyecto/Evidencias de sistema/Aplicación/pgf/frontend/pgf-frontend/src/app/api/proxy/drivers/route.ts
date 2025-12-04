import { NextRequest } from "next/server";
import { proxyFetch } from "../utils";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const queryString = searchParams.toString();
  const url = queryString ? `/drivers/choferes/?${queryString}` : "/drivers/choferes/";
  
  return proxyFetch(url, {
    method: "GET",
  });
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  return proxyFetch("/drivers/choferes/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

