import { NextRequest } from "next/server";
import { proxyFetch } from "../../utils";

export async function POST(request: NextRequest) {
  const body = await request.json();
  return proxyFetch("/auth/password-reset/", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

