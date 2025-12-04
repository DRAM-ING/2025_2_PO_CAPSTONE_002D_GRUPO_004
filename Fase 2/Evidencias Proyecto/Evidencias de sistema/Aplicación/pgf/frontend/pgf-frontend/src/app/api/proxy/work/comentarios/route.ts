import { NextRequest } from "next/server";
import { proxyFetch } from "../../utils";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const ot = searchParams.get("ot");
  const endpoint = ot
    ? `/work/comentarios/?ot=${encodeURIComponent(ot)}`
    : "/work/comentarios/";
  return proxyFetch(endpoint, {
    method: "GET",
  });
}

export async function POST(req: NextRequest) {
  return proxyFetch("/work/comentarios/", {
    method: "POST",
    body: await req.text(),
  });
}

