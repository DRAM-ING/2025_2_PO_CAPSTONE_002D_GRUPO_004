import { NextRequest, NextResponse } from "next/server";
import { proxyFetch } from "../../../utils";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  return proxyFetch(`/scheduling/agendas/${id}/`, {
    method: "GET",
  });
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const body = await request.json();
  return proxyFetch(`/scheduling/agendas/${id}/`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  return proxyFetch(`/scheduling/agendas/${id}/`, {
    method: "DELETE",
  });
}

