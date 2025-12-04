"use client";

import { useEffect } from "react";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {

  useEffect(() => {
    const id = setInterval(async () => {
      try {
        const response = await fetch("/api/auth/refresh", {
          method: "POST",
          credentials: "include",
        });
        
        if (!response.ok) {
          console.warn("Failed to refresh token:", response.status);
        }
      } catch (error) {
        // Silently handle network errors - don't spam console
        // The auth system will handle re-authentication if needed
        console.debug("Token refresh error (non-critical):", error);
      }
    }, 1000 * 50); // cada 50 segundos

    return () => clearInterval(id);
  }, []);

  return <>{children}</>;
}
