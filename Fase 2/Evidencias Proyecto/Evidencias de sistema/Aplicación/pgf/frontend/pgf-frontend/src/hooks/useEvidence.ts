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
    console.error("Fetch error in useEvidence:", error);
    return [];
  }
};

export function useEvidence(otId?: string) {
  const qs = otId ? `?ot=${otId}` : "";

  const { data, error, isLoading, mutate } = useSWR(
    `/api/work/evidencias${qs}`,
    fetcher
  );

  async function presigned(ot: string, filename: string, content_type?: string) {
    try {
      const r = await fetch("/api/work/evidencias/presigned", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ot, filename, content_type }),
      });

      if (!r.ok) {
        throw new Error(`HTTP ${r.status}`);
      }

      const text = await r.text();
      
      if (!text || text.trim() === "") {
        throw new Error("Empty response from server");
      }

      try {
        return JSON.parse(text);
      } catch (e) {
        console.error("Invalid JSON response:", text);
        throw new Error("Invalid JSON response");
      }
    } catch (error) {
      console.error("Error in presigned:", error);
      throw error;
    }
  }

  return {
    evidencias: data || [],
    loading: isLoading,
    error,
    refresh: mutate,
    presigned,
  };
}
