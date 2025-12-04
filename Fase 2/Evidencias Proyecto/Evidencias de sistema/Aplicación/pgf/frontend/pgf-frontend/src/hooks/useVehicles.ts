import useSWR from "swr";

const fetcher = async (url: string) => {
  try {
    const r = await fetch(url, { credentials: "include" });
    
    if (!r.ok) {
      return [];
    }
    
    const text = await r.text();
    
    if (!text || text.trim() === "") {
      return [];
    }
    
    try {
      const json = JSON.parse(text);
      return json.results || json || [];
    } catch (e) {
      console.error("Invalid JSON response from", url, ":", text);
      return [];
    }
  } catch (error) {
    console.error("Fetch error in useVehicles:", error);
    return [];
  }
};

export function useVehicles() {
  const { data, error, isLoading, mutate } = useSWR(
    "/api/vehiculos",
    fetcher
  );

  return {
    vehiculos: data || [],
    loading: isLoading,
    error,
    refresh: mutate,
  };
}
