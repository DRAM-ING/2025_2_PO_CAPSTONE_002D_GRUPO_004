import { NextRequest } from "next/server";
import { proxyFetch } from "../../utils";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    return proxyFetch("/vehicles/salida/", {
      method: "POST",
      body: JSON.stringify(body),
    });
  } catch (error) {
    console.error("Error parsing request body:", error);
    return proxyFetch("/vehicles/salida/", {
      method: "POST",
      body: await req.text(),
    });
  }
}

