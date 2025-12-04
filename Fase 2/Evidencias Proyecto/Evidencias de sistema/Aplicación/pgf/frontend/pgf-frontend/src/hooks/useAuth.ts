import useSWR from "swr";
import { useState } from "react";

const fetcher = async (url: string) => {
  try {
    const r = await fetch(url, { credentials: "include" });
    
    if (r.status === 401) return null;
    
    if (!r.ok) {
      return null;
    }
    
    const text = await r.text();
    
    // Handle empty responses
    if (!text || text.trim() === "") {
      return null;
    }
    
    try {
      return JSON.parse(text);
    } catch (e) {
      console.error("Invalid JSON response from", url, ":", text);
      return null;
    }
  } catch (error) {
    console.error("Fetch error in useAuth:", error);
    return null;
  }
};

export function useAuth() {
  const { data: user, error, mutate } = useSWR("/api/auth/me", fetcher, {
    refreshInterval: 5_000, // intenta revalidar sesión
  });

  const loading = !user && !error;

  async function login(username: string, password: string) {
    const r = await fetch("/api/auth/login", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    if (!r.ok) return false;

    await mutate(); // recargar sesión
    return true;
  }

  async function logout() {
    // borrar cookies client-side
    await fetch("/api/auth/logout", { method: "POST" });
    await mutate(null);
  }

  return { user, loading, error, login, logout, mutate };
}
