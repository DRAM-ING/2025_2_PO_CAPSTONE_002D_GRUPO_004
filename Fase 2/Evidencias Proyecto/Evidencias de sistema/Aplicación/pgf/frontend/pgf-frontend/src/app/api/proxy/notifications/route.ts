import { NextRequest, NextResponse } from "next/server";
import { proxyFetch } from "../utils";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const queryString = searchParams.toString();
  const url = queryString ? `/notifications/?${queryString}` : "/notifications/";
  return proxyFetch(url);
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  return proxyFetch("/notifications/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

