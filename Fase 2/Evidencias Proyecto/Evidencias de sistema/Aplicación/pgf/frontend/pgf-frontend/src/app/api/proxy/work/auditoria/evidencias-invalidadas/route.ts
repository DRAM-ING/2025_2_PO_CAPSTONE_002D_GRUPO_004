import { NextRequest, NextResponse } from "next/server";
import { proxyFetch } from "../../../utils";

/**
 * Proxy route para obtener evidencias invalidadas.
 */
export async function GET(req: NextRequest) {
  return proxyFetch("/work/auditoria/evidencias-invalidadas/");
}

