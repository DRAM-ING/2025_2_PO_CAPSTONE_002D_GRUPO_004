"use client";

import { usePathname } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import Topbar from "@/components/Topbar";
import ToastContainer from "@/components/ToastContainer";

export default function ConditionalLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuthPage = pathname?.startsWith("/auth");

  // Si es página de autenticación, no mostrar sidebar ni topbar
  if (isAuthPage) {
    return (
      <>
        {children}
        <ToastContainer />
      </>
    );
  }

  // Para el resto de páginas, mostrar layout completo
  // El sidebar es fixed, así que el contenido necesita margen izquierdo
  return (
    <div className="flex min-h-screen bg-[#f6f6f8] dark:bg-[#101622]">
      <Sidebar />
      <div className="flex-1 flex flex-col ml-64">
        <Topbar />
        <main className="flex-1 min-h-screen text-gray-900 dark:text-gray-200 relative">
          {children}
        </main>
      </div>
      <ToastContainer />
    </div>
  );
}

