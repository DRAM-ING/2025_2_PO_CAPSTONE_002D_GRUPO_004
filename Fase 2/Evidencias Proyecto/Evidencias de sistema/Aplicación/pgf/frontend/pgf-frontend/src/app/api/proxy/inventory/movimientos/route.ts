import { NextRequest } from "next/server";
import { proxyFetch } from "../../utils";

export async function GET(req: NextRequest) {
  const searchParams = req.nextUrl.searchParams;
  const queryString = searchParams.toString();
  const url = queryString ? `/inventory/movimientos/?${queryString}` : "/inventory/movimientos/";
  return proxyFetch(url);
}

