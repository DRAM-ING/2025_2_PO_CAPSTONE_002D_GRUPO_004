import { NextRequest } from "next/server";
import { proxyFetch } from "../../../utils";

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  return proxyFetch(`/inventory/repuestos/${id}/`);
}

export async function PUT(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const body = await req.json();
    return proxyFetch(`/inventory/repuestos/${id}/`, {
      method: "PUT",
      body: JSON.stringify(body),
    });
  } catch (error) {
    console.error("Error parsing request body:", error);
    const { id } = await params;
    return proxyFetch(`/inventory/repuestos/${id}/`, {
      method: "PUT",
      body: await req.text(),
    });
  }
}

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const body = await req.json();
    return proxyFetch(`/inventory/repuestos/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  } catch (error) {
    console.error("Error parsing request body:", error);
    const { id } = await params;
    return proxyFetch(`/inventory/repuestos/${id}/`, {
      method: "PATCH",
      body: await req.text(),
    });
  }
}

export async function DELETE(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  return proxyFetch(`/inventory/repuestos/${id}/`, {
    method: "DELETE",
  });
}

