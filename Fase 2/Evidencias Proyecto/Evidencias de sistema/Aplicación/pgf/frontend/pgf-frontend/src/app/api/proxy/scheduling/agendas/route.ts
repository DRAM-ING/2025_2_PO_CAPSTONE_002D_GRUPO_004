import { NextRequest, NextResponse } from "next/server";
import { proxyFetch } from "../../utils";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  let endpoint = "/scheduling/agendas/";
  if (searchParams.toString()) {
    endpoint += `?${searchParams.toString()}`;
  }
  
  return proxyFetch(endpoint, {
    method: "GET",
  });
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  return proxyFetch("/scheduling/agendas/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

