"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/store/auth";

export default function Dashboard() {
  const router = useRouter();
  const { user, refreshMe } = useAuth();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAndRedirect = async () => {
      // Si no hay usuario, intentar cargarlo
      if (!user) {
        try {
          await refreshMe();
        } catch {
          router.replace("/auth/login");
          return;
        }
      }

      // Esperar un momento para que el usuario se cargue
      await new Promise(resolve => setTimeout(resolve, 100));

      const currentUser = useAuth.getState().user;
      
      if (!currentUser) {
        router.replace("/auth/login");
        return;
      }

      setLoading(false);

      // Redirigir al dashboard ejecutivo si el usuario tiene permisos
      if (["ADMIN", "SPONSOR", "EJECUTIVO"].includes(currentUser.rol)) {
        router.replace("/dashboard/ejecutivo");
      } else {
        // Si no tiene permisos, redirigir según su rol
        if (currentUser.rol === "SUPERVISOR" || currentUser.rol === "JEFE_TALLER") {
          router.replace("/workorders");
        } else {
          router.replace("/vehicles");
        }
      }
    };

    checkAndRedirect();
  }, [user, router, refreshMe]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
        <p className="mt-4 text-gray-600 dark:text-gray-400">Redirigiendo...</p>
      </div>
    </div>
  );
}
