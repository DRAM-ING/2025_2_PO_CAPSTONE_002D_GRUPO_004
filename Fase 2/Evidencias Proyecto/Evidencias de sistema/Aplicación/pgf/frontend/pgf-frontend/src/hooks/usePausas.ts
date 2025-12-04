export function usePausas() {
  async function crearPausa(body: any) {
    try {
      const r = await fetch("/api/work/pausas", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!r.ok) {
        const errorText = await r.text().catch(() => 'Unknown error');
        throw new Error(errorText || `HTTP ${r.status}`);
      }

      const text = await r.text();
      
      if (!text || text.trim() === "") {
        return {};
      }

      try {
        return JSON.parse(text);
      } catch (e) {
        console.error("Invalid JSON response:", text);
        throw new Error("Invalid JSON response from server");
      }
    } catch (error) {
      console.error("Error in crearPausa:", error);
      throw error;
    }
  }

  return { crearPausa };
}
