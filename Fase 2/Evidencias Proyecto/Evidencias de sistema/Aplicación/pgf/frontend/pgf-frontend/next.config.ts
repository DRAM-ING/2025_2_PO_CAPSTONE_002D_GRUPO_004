import type { NextConfig } from "next";

// Obtener variables de entorno
const isProduction = process.env.NODE_ENV === "production";
const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const s3Endpoint = process.env.NEXT_PUBLIC_S3_ENDPOINT || "http://localhost:4566";

// Parsear el hostname del API para imágenes
const apiUrl = new URL(apiBaseUrl);
const s3Url = new URL(s3Endpoint);

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "standalone", // Necesario para Docker
  images: {
    remotePatterns: [
      { 
        protocol: s3Url.protocol.replace(":", "") as "http" | "https",
        hostname: s3Url.hostname,
        port: s3Url.port || undefined,
        pathname: "/**",
      },
      {
        protocol: apiUrl.protocol.replace(":", "") as "http" | "https",
        hostname: apiUrl.hostname,
        port: apiUrl.port || undefined,
        pathname: "/**",
      },
    ],
  },
  experimental: {
    serverActions: {
      allowedOrigins: isProduction 
        ? [process.env.FRONTEND_URL || "https://localhost:3000"]
        : [
            "http://localhost:3000", 
            "http://127.0.0.1:3000",
            // Permitir URL específica de Cloudflare Tunnel si está definida
            ...(process.env.CLOUDFLARE_TUNNEL_URL ? [process.env.CLOUDFLARE_TUNNEL_URL] : []),
          ],
    },
  },
  // Configuración para permitir requests desde Cloudflare Tunnel
  // El warning sobre allowedDevOrigins es para una versión futura de Next.js
  // Por ahora, Next.js 15.5.5 no requiere esta configuración explícita
};

export default nextConfig;
