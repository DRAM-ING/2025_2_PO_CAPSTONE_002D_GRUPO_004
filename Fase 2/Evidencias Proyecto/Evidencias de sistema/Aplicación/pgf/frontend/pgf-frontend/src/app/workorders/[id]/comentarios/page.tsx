"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";
import RoleGuard from "@/components/RoleGuard";
import Link from "next/link";
import { ENDPOINTS } from "@/lib/constants";
import { withSession } from "@/lib/api.client";

/**
 * Página de comentarios de una OT.
 * 
 * Permite:
 * - Ver todos los comentarios de una OT
 * - Crear nuevos comentarios
 * - Editar comentarios propios (si aplica)
 * - Mencionar usuarios
 */
export default function ComentariosOTPage() {
  const params = useParams();
  const otId = params?.id as string;
  const router = useRouter();
  const toast = useToast();
  const { user } = useAuth();

  const [comentarios, setComentarios] = useState<any[]>([]);
  const [nuevoComentario, setNuevoComentario] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [ot, setOt] = useState<any>(null);

  useEffect(() => {
    if (otId) {
      cargarDatos();
    }
  }, [otId]);

  const cargarDatos = async () => {
    setLoading(true);
    try {
      // Cargar OT
      const otResponse = await fetch(ENDPOINTS.WORK_ORDER(otId), {
        method: "GET",
        ...withSession(),
      });

      if (otResponse.ok) {
        const otData = await otResponse.json();
        setOt(otData);
      }

      // Cargar comentarios
      const comentariosResponse = await fetch(`${ENDPOINTS.WORK_COMENTARIOS}?ot=${otId}`, {
        method: "GET",
        ...withSession(),
      });

      if (comentariosResponse.ok) {
        const comentariosData = await comentariosResponse.json();
        setComentarios(comentariosData.results || comentariosData || []);
      } else {
        const text = await comentariosResponse.text();
        let errorData;
        try {
          errorData = JSON.parse(text);
        } catch {
          errorData = { detail: text || "Error desconocido" };
        }
        toast.error(errorData.detail || "Error al cargar comentarios");
      }
    } catch (error) {
      console.error("Error al cargar datos:", error);
      toast.error("Error al cargar comentarios");
    } finally {
      setLoading(false);
    }
  };

  const crearComentario = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!nuevoComentario.trim()) {
      toast.error("El comentario no puede estar vacío");
      return;
    }

    setSaving(true);
    try {
      const response = await fetch(ENDPOINTS.WORK_COMENTARIOS, {
        method: "POST",
        ...withSession(),
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ot: otId,
          contenido: nuevoComentario,
        }),
      });

      if (response.ok) {
        toast.success("Comentario agregado correctamente");
        setNuevoComentario("");
        cargarDatos();
      } else {
        const text = await response.text();
        let errorData;
        try {
          errorData = JSON.parse(text);
        } catch {
          errorData = { detail: text || "Error desconocido" };
        }
        toast.error(errorData.detail || "Error al crear comentario");
      }
    } catch (error) {
      console.error("Error al crear comentario:", error);
      toast.error("Error al crear comentario");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <RoleGuard allow={["ADMIN", "SUPERVISOR", "MECANICO", "JEFE_TALLER", "GUARDIA", "COORDINADOR_ZONA"]}>
        <div className="p-6 flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando comentarios...</p>
          </div>
        </div>
      </RoleGuard>
    );
  }

  return (
    <RoleGuard allow={["ADMIN", "SUPERVISOR", "MECANICO", "JEFE_TALLER", "GUARDIA", "COORDINADOR_ZONA"]}>
      <div className="p-6 max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Comentarios de la OT
          </h1>
          <Link
            href={`/workorders/${otId}`}
            className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
          >
            ← Volver a OT
          </Link>
        </div>

        {/* Información de la OT */}
        {ot && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  OT #{ot.id.slice(0, 8)}
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {ot.vehiculo_patente || ot.vehiculo_detalle?.patente || ot.vehiculo?.patente || "N/A"} - Estado: {ot.estado}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Formulario para nuevo comentario */}
        <form onSubmit={crearComentario} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            Agregar Comentario
          </h2>
          <textarea
            value={nuevoComentario}
            onChange={(e) => setNuevoComentario(e.target.value)}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white mb-4"
            placeholder="Escribe tu comentario aquí..."
          />
          <button
            type="submit"
            disabled={saving || !nuevoComentario.trim()}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? "Enviando..." : "Agregar Comentario"}
          </button>
        </form>

        {/* Lista de comentarios */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            Comentarios ({comentarios.length})
          </h2>
          {comentarios.length > 0 ? (
            <div className="space-y-4">
              {comentarios.map((comentario) => (
                <div
                  key={comentario.id}
                  className="border-l-4 border-blue-500 pl-4 py-2"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <p className="font-semibold text-gray-900 dark:text-white">
                        {comentario.usuario_nombre || (comentario.usuario?.first_name && comentario.usuario?.last_name ? `${comentario.usuario.first_name} ${comentario.usuario.last_name}` : comentario.usuario?.username) || "Usuario desconocido"}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {comentario.creado_en ? new Date(comentario.creado_en).toLocaleString() : "Fecha no disponible"}
                        {comentario.editado && (
                          <span className="ml-2 text-gray-400">(editado)</span>
                        )}
                      </p>
                    </div>
                  </div>
                  <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                    {comentario.contenido}
                  </p>
                  {comentario.menciones && comentario.menciones.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Mencionado: {comentario.menciones.join(", ")}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 dark:text-gray-400">
              No hay comentarios aún. Sé el primero en comentar.
            </p>
          )}
        </div>
      </div>
    </RoleGuard>
  );
}
