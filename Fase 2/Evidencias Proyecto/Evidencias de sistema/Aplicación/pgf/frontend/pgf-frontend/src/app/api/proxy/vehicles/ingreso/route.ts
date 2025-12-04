import { NextRequest } from "next/server";
import { proxyFetch } from "../../utils";

export async function POST(req: NextRequest) {
  return proxyFetch("/vehicles/ingreso/", {
    method: "POST",
    body: await req.text(),
  });
}

