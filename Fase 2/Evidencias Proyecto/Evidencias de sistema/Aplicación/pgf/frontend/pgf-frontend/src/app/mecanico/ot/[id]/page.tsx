"use client";

import { useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import RoleGuard from "@/components/RoleGuard";

/**
 * Vista de detalle de OT para Mecánico.
 * 
 * Redirige a la página principal de workorders/[id] para mantener consistencia
 * y funcionalidad completa en todas las vistas de OTs.
 * 
 * Permisos:
 * - Solo MECANICO puede acceder
 */
export default function MecanicoOTPage() {
  const router = useRouter();
  const params = useParams();
  const otId = params?.id as string | undefined;

  useEffect(() => {
    if (otId && typeof otId === 'string' && otId.trim() !== '') {
      // Redirigir a la página principal de workorders para mantener consistencia
      router.replace(`/workorders/${otId}`);
    }
  }, [otId, router]);

  return (
    <RoleGuard allow={["MECANICO"]}>
      <div className="p-6 flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Redirigiendo...</p>
        </div>
      </div>
    </RoleGuard>
  );
}
