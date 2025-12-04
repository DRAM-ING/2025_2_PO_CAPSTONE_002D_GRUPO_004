import { NextRequest, NextResponse } from "next/server";
import { proxyFetch } from "../../../utils";

/**
 * Proxy route para obtener actividad por usuario.
 */
export async function GET(req: NextRequest) {
  return proxyFetch("/work/auditoria/actividad-usuario/");
}

