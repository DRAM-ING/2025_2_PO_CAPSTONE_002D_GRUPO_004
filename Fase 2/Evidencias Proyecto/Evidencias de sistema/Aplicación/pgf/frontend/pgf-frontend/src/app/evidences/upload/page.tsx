"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";
import RoleGuard from "@/components/RoleGuard";
import Link from "next/link";

/**
 * Página para subir evidencias generales.
 * 
 * Permite subir archivos sin necesidad de una OT específica.
 * La OT es opcional.
 * 
 * Soporta:
 * - Archivos hasta 3GB
 * - Imágenes, PDFs, documentos, etc.
 */
export default function UploadEvidencePage() {
  const router = useRouter();
  const toast = useToast();
  const { hasRole } = useAuth();

  const [file, setFile] = useState<File | null>(null);
  const [descripcion, setDescripcion] = useState("");
  const [tipo, setTipo] = useState<string>("FOTO");
  const [otId, setOtId] = useState<string>("");
  const [preview, setPreview] = useState("");
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [ordenesTrabajo, setOrdenesTrabajo] = useState<any[]>([]);
  const [loadingOTs, setLoadingOTs] = useState(true);

  const canUpload = hasRole(["ADMIN", "SUPERVISOR", "MECANICO", "JEFE_TALLER", "GUARDIA"]);

  // Cargar lista de OTs disponibles
  useEffect(() => {
    const loadOrdenesTrabajo = async () => {
      try {
        setLoadingOTs(true);
        const response = await fetch("/api/proxy/work/ordenes/?page_size=100", {
          credentials: "include",
        });
        
        if (response.ok) {
          const data = await response.json();
          // Extraer OTs de results o directamente del array
          const ots = Array.isArray(data) ? data : (data.results || []);
          // Filtrar solo OTs activas (no cerradas ni anuladas)
          const otsActivas = ots.filter((ot: any) => 
            ot.estado && !["CERRADA", "ANULADA"].includes(ot.estado)
          );
          setOrdenesTrabajo(otsActivas);
        }
      } catch (error) {
        console.error("Error cargando órdenes de trabajo:", error);
      } finally {
        setLoadingOTs(false);
      }
    };

    if (canUpload) {
      loadOrdenesTrabajo();
    }
  }, [canUpload]);

  if (!canUpload) {
    return (
      <RoleGuard allow={["ADMIN", "SUPERVISOR", "MECANICO", "JEFE_TALLER", "GUARDIA"]}>
        <div></div>
      </RoleGuard>
    );
  }

  /**
   * Detecta el tipo de evidencia basado en la extensión del archivo.
   */
  const detectTipoEvidencia = (filename: string, mimeType: string): string => {
    const lowerName = filename.toLowerCase();
    
    // Imágenes
    if (mimeType.startsWith("image/") || /\.(jpg|jpeg|png|gif|webp|bmp)$/i.test(lowerName)) {
      return "FOTO";
    }
    
    // PDFs
    if (mimeType === "application/pdf" || lowerName.endsWith(".pdf")) {
      return "PDF";
    }
    
    // Hojas de cálculo
    if (
      mimeType.includes("spreadsheet") ||
      mimeType.includes("excel") ||
      /\.(xlsx|xls|csv)$/i.test(lowerName)
    ) {
      return "HOJA_CALCULO";
    }
    
    // Documentos Word
    if (
      mimeType.includes("word") ||
      mimeType.includes("document") ||
      /\.(doc|docx)$/i.test(lowerName)
    ) {
      return "DOCUMENTO";
    }
    
    // Archivos comprimidos
    if (
      mimeType.includes("zip") ||
      mimeType.includes("rar") ||
      mimeType.includes("7z") ||
      /\.(zip|rar|7z)$/i.test(lowerName)
    ) {
      return "COMPRIMIDO";
    }
    
    return "OTRO";
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setError("");

    // Detectar tipo automáticamente
    const detectedType = detectTipoEvidencia(selectedFile.name, selectedFile.type);
    setTipo(detectedType);

    // Preview para imágenes
    if (selectedFile.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreview(e.target?.result as string);
      };
      reader.readAsDataURL(selectedFile);
    } else {
      setPreview("");
    }
  };

  const upload = async () => {
    if (!file) {
      setError("Selecciona un archivo");
      return;
    }

    // Validar que la OT seleccionada existe (si se seleccionó una)
    if (otId && !ordenesTrabajo.find(ot => ot.id === otId)) {
      setError("La OT seleccionada no es válida");
      return;
    }

    setError("");
    setUploading(true);
    setUploadProgress(0);

    try {
      // Subir archivo directamente al backend (el backend lo sube a S3)
      const formData = new FormData();
      formData.append("file", file);
      formData.append("ot", otId || "");
      formData.append("tipo", tipo);
      formData.append("descripcion", descripcion || "");

      // Usar XMLHttpRequest para monitorear progreso
      await new Promise<void>((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener("progress", (e) => {
          if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            setUploadProgress(percentComplete);
          }
        });

        xhr.addEventListener("load", () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve();
          } else {
            let errorMessage = `Error al subir archivo: ${xhr.status} ${xhr.statusText}`;
            try {
              const errorData = JSON.parse(xhr.responseText);
              errorMessage = errorData.detail || errorMessage;
            } catch {
              // Si no se puede parsear, usar el mensaje por defecto
            }
            reject(new Error(errorMessage));
          }
        });

        xhr.addEventListener("error", (e) => {
          console.error('Error de red XHR:', e);
          reject(new Error("Error de red al subir archivo"));
        });

        xhr.addEventListener("abort", () => {
          reject(new Error("Subida cancelada"));
        });

        xhr.open("POST", "/api/proxy/work/evidencias/presigned/");
        xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
        xhr.withCredentials = true;
        xhr.send(formData);
      });

      toast.success("Evidencia subida correctamente");
      router.push("/evidences");
    } catch (error) {
      console.error("Error al subir evidencia:", error);
      setError(error instanceof Error ? error.message : "Error al subir evidencia");
      toast.error(error instanceof Error ? error.message : "Error al subir evidencia");
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <Link
          href="/evidences"
          className="text-blue-600 hover:underline mb-4 inline-block"
        >
          ← Volver a Evidencias
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">Subir Evidencia</h1>
      </div>

      <div className="bg-white rounded-lg shadow p-6 max-w-2xl">
        {error && (
          <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        <div className="space-y-4">
          {/* Archivo */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Archivo *
            </label>
            <input
              type="file"
              onChange={onFileChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
              accept="image/*,application/pdf,.xlsx,.xls,.csv,.doc,.docx,.zip,.rar,.7z"
            />
            {file && (
              <p className="mt-2 text-sm text-gray-500">
                {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
              </p>
            )}
          </div>

          {/* Preview de imagen */}
          {preview && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Vista Previa
              </label>
              <img
                src={preview}
                alt="Preview"
                className="max-w-full h-64 object-contain rounded-lg border border-gray-300"
              />
            </div>
          )}

          {/* OT (opcional) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Orden de Trabajo (Opcional)
            </label>
            <select
              value={otId}
              onChange={(e) => setOtId(e.target.value)}
              disabled={loadingOTs}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <option value="">
                {loadingOTs ? "Cargando OTs..." : "Sin OT (Evidencia general)"}
              </option>
              {ordenesTrabajo.map((ot) => {
                const patente = ot.vehiculo?.patente || ot.vehiculo_patente || "Sin patente";
                const estado = ot.estado || "Sin estado";
                const motivo = ot.motivo ? (ot.motivo.length > 40 ? ot.motivo.substring(0, 40) + "..." : ot.motivo) : "Sin motivo";
                const otShortId = ot.id?.substring(0, 8) || "N/A";
                
                return (
                  <option key={ot.id} value={ot.id}>
                    OT #{otShortId} | {patente} | {estado} | {motivo}
                  </option>
                );
              })}
            </select>
            <p className="mt-1 text-xs text-gray-500">
              Selecciona una OT para vincular la evidencia, o deja "Sin OT" para una evidencia general
            </p>
            {otId && (() => {
              const otSeleccionada = ordenesTrabajo.find(ot => ot.id === otId);
              if (!otSeleccionada) return null;
              
              const patente = otSeleccionada.vehiculo?.patente || otSeleccionada.vehiculo_patente || "Sin patente";
              const estado = otSeleccionada.estado || "Sin estado";
              const motivo = otSeleccionada.motivo || "Sin motivo";
              
              return (
                <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm">
                  <p className="text-blue-800 font-semibold mb-1">
                    OT seleccionada:
                  </p>
                  <div className="space-y-1 text-blue-700">
                    <p><strong>ID:</strong> {otId.substring(0, 8)}...</p>
                    <p><strong>Vehículo:</strong> {patente}</p>
                    <p><strong>Estado:</strong> {estado}</p>
                    <p><strong>Motivo:</strong> {motivo.length > 80 ? motivo.substring(0, 80) + "..." : motivo}</p>
                  </div>
                </div>
              );
            })()}
          </div>

          {/* Tipo */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tipo *
            </label>
            <select
              value={tipo}
              onChange={(e) => setTipo(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
            >
              <option value="FOTO">FOTO</option>
              <option value="PDF">PDF</option>
              <option value="HOJA_CALCULO">Hoja de Cálculo</option>
              <option value="DOCUMENTO">Documento</option>
              <option value="COMPRIMIDO">Comprimido</option>
              <option value="OTRO">Otro</option>
            </select>
          </div>

          {/* Descripción */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Descripción
            </label>
            <textarea
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
              rows={3}
              placeholder="Descripción de la evidencia..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
            />
          </div>

          {/* Barra de progreso */}
          {uploading && (
            <div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              <p className="mt-2 text-sm text-gray-600 text-center">
                Subiendo... {Math.round(uploadProgress)}%
              </p>
            </div>
          )}

          {/* Botones */}
          <div className="flex gap-4">
            <button
              onClick={upload}
              disabled={uploading || !file}
              className="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploading ? "Subiendo..." : "Subir Evidencia"}
            </button>
            <Link
              href="/evidences"
              className="px-6 py-3 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg transition-colors font-medium"
            >
              Cancelar
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
