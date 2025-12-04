"use client";

import { useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import ConfirmDialog from "@/components/ConfirmDialog";
import { invalidateCache } from "@/lib/dataRefresh";

export default function DeleteVehicle() {
  const params = useParams();
  const id = params?.id as string | undefined;
  const router = useRouter();
  const toast = useToast();
  const [showConfirm, setShowConfirm] = useState(true);
  const [loading, setLoading] = useState(false);

  const remove = async () => {
    if (!id) {
      toast.error("ID de vehículo no válido");
      return;
    }

    setLoading(true);
    try {
      const r = await fetch(`/api/proxy/vehicles/${id}/`, {
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
        toast.error(data.detail || "Error al eliminar el vehículo");
        return;
      }

      toast.success("Vehículo eliminado correctamente");
      invalidateCache("VEHICLES");
      router.refresh();
      router.push("/vehicles");
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al eliminar el vehículo");
    } finally {
      setLoading(false);
      setShowConfirm(false);
    }
  };

  return (
    <ConfirmDialog
      isOpen={showConfirm}
      title="Eliminar Vehículo"
      message="¿Estás seguro de que deseas eliminar este vehículo? Esta acción no se puede deshacer."
      confirmText={loading ? "Eliminando..." : "Sí, eliminar"}
      cancelText="Cancelar"
      onConfirm={remove}
      onCancel={() => router.back()}
      type="danger"
    />
  );
}
