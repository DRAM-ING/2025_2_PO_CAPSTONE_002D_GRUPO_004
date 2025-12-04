// src/app/_components/Nav.tsx
"use client";
import Link from "next/link";
import { useAuth } from "@/store/auth";

export default function Nav() {
  const { allowed } = useAuth();
  return (
    <nav className="flex gap-4 p-3 border-b">
      {allowed("dashboard")  && <Link href="/dashboard">Dashboard</Link>}
      {allowed("vehicles")   && <Link href="/vehicles">Vehículos</Link>}
      {allowed("workorders") && <Link href="/workorders">OT</Link>}
      {allowed("evidences")  && <Link href="/evidences">Evidencias</Link>}
      {allowed("routes")     && <Link href="/routes">Ingresos</Link>}
    </nav>
  );
}
