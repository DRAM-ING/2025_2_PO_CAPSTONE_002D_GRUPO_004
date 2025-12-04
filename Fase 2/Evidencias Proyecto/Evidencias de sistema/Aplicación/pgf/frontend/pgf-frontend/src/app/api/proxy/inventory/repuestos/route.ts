import { NextRequest } from "next/server";
import { proxyFetch } from "../../utils";

export async function GET(req: NextRequest) {
  const searchParams = req.nextUrl.searchParams;
  const queryString = searchParams.toString();
  const url = queryString ? `/inventory/repuestos/?${queryString}` : "/inventory/repuestos/";
  return proxyFetch(url);
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    return proxyFetch("/inventory/repuestos/", {
      method: "POST",
      body: JSON.stringify(body),
    });
  } catch (error) {
    console.error("Error parsing request body:", error);
    return proxyFetch("/inventory/repuestos/", {
      method: "POST",
      body: await req.text(),
    });
  }
}

