"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import ConfirmDialog from "@/components/ConfirmDialog";
import { invalidateCache } from "@/lib/dataRefresh";

export default function DeleteItem() {
  const params = useParams();
  const id = params.id as string;
  const itemId = params.itemId as string;
  const router = useRouter();
  const toast = useToast();
  const [showConfirm, setShowConfirm] = useState(true);
  const [loading, setLoading] = useState(false);

  const remove = async () => {
    setLoading(true);
    try {
      const r = await fetch(`/api/proxy/work/items/${itemId}/`, {
        method: "DELETE",
        credentials: "include",
      });

      if (!r.ok) {
        const text = await r.text();
        let data;
        try {
          data = JSON.parse(text);
        } catch {
          data = { detail: text || "Error desconocido" };
        }
        toast.error(data.detail || "Error al eliminar el ítem");
        return;
      }

      toast.success("Ítem eliminado correctamente");
      invalidateCache("WORKORDERS");
      router.refresh();
      router.push(`/workorders/${id}/items`);
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al eliminar el ítem");
    } finally {
      setLoading(false);
      setShowConfirm(false);
    }
  };

  return (
    <ConfirmDialog
      isOpen={showConfirm}
      title="Eliminar Ítem"
      message="¿Estás seguro de que deseas eliminar este ítem? Esta acción no se puede deshacer."
      confirmText={loading ? "Eliminando..." : "Sí, eliminar"}
      cancelText="Cancelar"
      onConfirm={remove}
      onCancel={() => router.back()}
      type="danger"
    />
  );
}
