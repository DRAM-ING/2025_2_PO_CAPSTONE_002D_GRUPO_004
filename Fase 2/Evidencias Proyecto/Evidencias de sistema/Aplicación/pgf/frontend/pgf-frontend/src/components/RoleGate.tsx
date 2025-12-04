// components/RoleGate.tsx
"use client";

import { ReactNode } from "react";
import { useAuth } from "@/store/auth";
import type { Rol } from "@/lib/constants";

export default function RoleGate({
  allow = [],
  children,
  fallback = null,
}: {
  allow: Rol[];
  children: ReactNode;
  fallback?: ReactNode;
}) {
  const { hasRole } = useAuth();
  if (allow.length && !hasRole(allow)) return <>{fallback}</>;
  return <>{children}</>;
}
