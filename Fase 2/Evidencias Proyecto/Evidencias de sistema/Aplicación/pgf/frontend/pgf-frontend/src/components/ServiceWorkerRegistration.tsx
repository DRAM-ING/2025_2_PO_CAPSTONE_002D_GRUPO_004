"use client";

import { useEffect } from "react";

/**
 * Componente para registrar el Service Worker.
 * 
 * Registra el service worker cuando el componente se monta,
 * permitiendo notificaciones push incluso cuando la app está cerrada.
 */
export default function ServiceWorkerRegistration() {
  useEffect(() => {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker
        .register("/sw.js")
        .then((registration) => {
          console.log("Service Worker registrado:", registration);
        })
        .catch((error) => {
          console.error("Error al registrar Service Worker:", error);
        });
    }
  }, []);

  return null;
}

