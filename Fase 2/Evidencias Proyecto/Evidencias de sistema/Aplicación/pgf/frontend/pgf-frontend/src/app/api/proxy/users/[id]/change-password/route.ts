import { NextRequest } from "next/server";
import { proxyFetch } from "../../../utils";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const body = await request.json();
  const id = id;
  return proxyFetch(`/users/${id}/change-password/`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

