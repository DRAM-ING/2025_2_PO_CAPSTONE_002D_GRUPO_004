"use client";

import { useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import ConfirmDialog from "@/components/ConfirmDialog";
import RoleGuard from "@/components/RoleGuard";
import { invalidateCache } from "@/lib/dataRefresh";

export default function DeleteUser() {
  const params = useParams();
  const id = params?.id as string;
  const router = useRouter();
  const toast = useToast();
  const [showConfirm, setShowConfirm] = useState(true);
  const [loading, setLoading] = useState(false);

  const remove = async () => {
    setLoading(true);
    try {
      const r = await fetch(`/api/proxy/users/${id}/`, {
        method: "DELETE",
        credentials: "include",
      });

      if (!r.ok) {
        const text = await r.text();
        
        // Detectar si la respuesta es HTML (error del servidor)
        if (text.trim().startsWith("<!DOCTYPE") || text.trim().startsWith("<html")) {
          console.error("Backend retornó HTML en lugar de JSON:", text.substring(0, 200));
          toast.error("Error del servidor. El usuario no se puede eliminar porque tiene relaciones protegidas en el sistema.");
          return;
        }
        
        let data;
        try {
          data = JSON.parse(text);
        } catch (e) {
          console.error("Error parseando JSON:", e, "Response:", text.substring(0, 200));
          toast.error("Error procesando respuesta del servidor");
          return;
        }
        
        // Extraer mensaje de error
        const errorMessage = data.detail || data.message || "Error al eliminar el usuario";
        toast.error(errorMessage);
        return;
      }

      toast.success("Usuario eliminado correctamente");
      invalidateCache("USERS");
      router.refresh();
      router.push("/users");
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al eliminar el usuario");
    } finally {
      setLoading(false);
      setShowConfirm(false);
    }
  };

  return (
    <RoleGuard allow={["ADMIN", "SUPERVISOR"]}>
      <ConfirmDialog
        isOpen={showConfirm}
        title="Eliminar Usuario"
        message="¿Estás seguro de que deseas eliminar este usuario? Esta acción no se puede deshacer."
        confirmText={loading ? "Eliminando..." : "Sí, eliminar"}
        cancelText="Cancelar"
        onConfirm={remove}
        onCancel={() => router.back()}
        type="danger"
      />
    </RoleGuard>
  );
}
