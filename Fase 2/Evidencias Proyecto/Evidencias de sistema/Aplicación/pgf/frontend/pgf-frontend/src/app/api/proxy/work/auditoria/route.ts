import { NextRequest, NextResponse } from "next/server";
import { proxyFetch } from "../../utils";

/**
 * Proxy route para listar registros de auditoría.
 */
export async function GET(req: NextRequest) {
  return proxyFetch("/work/auditoria/");
}

