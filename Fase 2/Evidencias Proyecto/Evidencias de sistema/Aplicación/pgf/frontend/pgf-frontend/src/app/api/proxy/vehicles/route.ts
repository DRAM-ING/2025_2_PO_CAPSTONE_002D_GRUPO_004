import { NextRequest } from "next/server";
import { proxyFetch } from "../utils";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const queryString = searchParams.toString();
  const url = queryString ? `/vehicles/?${queryString}` : "/vehicles/";
  return proxyFetch(url);
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  return proxyFetch("/vehicles/", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
