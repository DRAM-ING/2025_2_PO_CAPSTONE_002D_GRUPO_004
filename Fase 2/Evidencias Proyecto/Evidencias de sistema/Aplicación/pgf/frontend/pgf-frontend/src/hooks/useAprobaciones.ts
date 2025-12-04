export function useAprobaciones() {
  async function aprobar(id: string) {
    try {
      const r = await fetch(`/api/work/aprobaciones/${id}/aprobar`, {
        method: "POST",
        credentials: "include",
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
      console.error("Error in aprobar:", error);
      throw error;
    }
  }

  async function rechazar(id: string) {
    try {
      const r = await fetch(`/api/work/aprobaciones/${id}/rechazar`, {
        method: "POST",
        credentials: "include",
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
      console.error("Error in rechazar:", error);
      throw error;
    }
  }

  return { aprobar, rechazar };
}
