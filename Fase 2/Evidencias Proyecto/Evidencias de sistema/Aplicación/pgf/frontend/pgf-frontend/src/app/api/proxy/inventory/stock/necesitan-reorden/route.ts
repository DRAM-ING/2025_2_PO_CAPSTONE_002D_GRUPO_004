import { NextRequest } from "next/server";
import { proxyFetch } from "../../utils";

export async function GET(req: NextRequest) {
  return proxyFetch("/inventory/stock/necesitan-reorden/");
}

