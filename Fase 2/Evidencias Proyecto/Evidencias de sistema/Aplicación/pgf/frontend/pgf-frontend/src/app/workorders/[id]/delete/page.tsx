"use client";

import { useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import ConfirmDialog from "@/components/ConfirmDialog";
import RoleGuard from "@/components/RoleGuard";
import { invalidateCache } from "@/lib/dataRefresh";

export default function DeleteWorkOrder() {
  const params = useParams();
  const id = params?.id as string;
  const router = useRouter();
  const toast = useToast();
  const [showConfirm, setShowConfirm] = useState(true);
  const [loading, setLoading] = useState(false);

  const remove = async () => {
    setLoading(true);
    try {
      const r = await fetch(`/api/proxy/work/ordenes/${id}/`, {
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
        toast.error(data.detail || "Error al eliminar la orden de trabajo");
        return;
      }

      toast.success("Orden de trabajo eliminada correctamente");
      invalidateCache("WORKORDERS");
      router.refresh();
      router.push("/workorders");
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al eliminar la orden de trabajo");
    } finally {
      setLoading(false);
      setShowConfirm(false);
    }
  };

  return (
    <RoleGuard allow={["ADMIN", "SUPERVISOR"]}>
      <ConfirmDialog
        isOpen={showConfirm}
        title="Eliminar Orden de Trabajo"
        message={`¿Estás seguro de que deseas eliminar la orden de trabajo #${id}? Esta acción no se puede deshacer. Solo se pueden eliminar órdenes en estado ABIERTA.`}
        confirmText={loading ? "Eliminando..." : "Sí, eliminar"}
        cancelText="Cancelar"
        onConfirm={remove}
        onCancel={() => router.back()}
        type="danger"
      />
    </RoleGuard>
  );
}

