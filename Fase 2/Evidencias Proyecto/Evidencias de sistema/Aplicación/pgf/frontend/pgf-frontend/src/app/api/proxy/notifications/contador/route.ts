import { NextRequest } from "next/server";
import { proxyFetch } from "../../utils";

export async function GET(request: NextRequest) {
  return proxyFetch("/notifications/contador/");
}

