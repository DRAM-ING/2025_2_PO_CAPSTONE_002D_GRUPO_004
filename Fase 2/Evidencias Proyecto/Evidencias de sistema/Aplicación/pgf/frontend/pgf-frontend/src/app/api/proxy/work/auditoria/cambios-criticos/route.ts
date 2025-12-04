import { NextRequest, NextResponse } from "next/server";
import { proxyFetch } from "../../../utils";

/**
 * Proxy route para obtener cambios críticos.
 */
export async function GET(req: NextRequest) {
  return proxyFetch("/work/auditoria/cambios-criticos/");
}

