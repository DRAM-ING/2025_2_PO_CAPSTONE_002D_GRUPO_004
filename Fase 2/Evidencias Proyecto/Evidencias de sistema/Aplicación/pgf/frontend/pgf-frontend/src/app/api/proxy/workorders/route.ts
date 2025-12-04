import { NextRequest } from "next/server";
import { proxyFetch } from "../utils";

export async function GET(req: NextRequest) {
  const search = req.nextUrl.search; // ?estado=ABIERTA
  return proxyFetch(`/work/ordenes/${search}`);
}
