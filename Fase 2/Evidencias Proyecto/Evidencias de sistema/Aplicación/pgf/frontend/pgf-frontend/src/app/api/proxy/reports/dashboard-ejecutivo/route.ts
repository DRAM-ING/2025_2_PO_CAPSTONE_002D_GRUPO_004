import { proxyFetch } from "../../utils";

export async function GET() {
  return proxyFetch("/reports/dashboard-ejecutivo/");
}

