"use client";

import { useState, use } from "react";
import { ENDPOINTS } from "@/lib/constants";
import { withSession } from "@/lib/api.client";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";
import RoleGuard from "@/components/RoleGuard";
import { handleApiError, getRoleHomePage } from "@/lib/permissions";
import { invalidateCache } from "@/lib/dataRefresh";

/**
 * Componente para subir evidencias a una Orden de Trabajo.
 * 
 * Soporta:
 * - Archivos hasta 3GB
 * - Imágenes (JPEG, PNG, GIF, WebP, BMP)
 * - PDFs
 * - Hojas de cálculo (XLSX, XLS, CSV)
 * - Documentos Word (DOC, DOCX)
 * - Archivos comprimidos (ZIP, RAR, 7Z)
 * - Otros tipos de archivo
 * 
 * Proceso:
 * 1. Obtiene URL presigned del backend
 * 2. Sube archivo directamente a S3
 * 3. Registra la evidencia en el backend
 */
export default function UploadEvidence({ params }: { params: Promise<{ id: string }> }) {
  const { id: otId } = use(params);
  const router = useRouter();
  const toast = useToast();
  const { hasRole, user } = useAuth();

  // Roles autorizados para subir evidencias
  const canUpload = hasRole(["MECANICO", "SUPERVISOR", "ADMIN", "GUARDIA", "JEFE_TALLER"]);

  const [file, setFile] = useState<File | null>(null);
  const [descripcion, setDescripcion] = useState("");
  const [tipo, setTipo] = useState<string>("FOTO");
  const [preview, setPreview] = useState("");
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

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
      /\.(xlsx|xls|csv)$/i.test(lowerName)
    ) {
      return "HOJA_CALCULO";
    }
    
    // Documentos Word
    if (
      mimeType.includes("wordprocessing") ||
      mimeType === "application/msword" ||
      /\.(doc|docx)$/i.test(lowerName)
    ) {
      return "DOCUMENTO";
    }
    
    // Archivos comprimidos
    if (
      mimeType.includes("zip") ||
      /\.(zip|rar|7z|tar|gz)$/i.test(lowerName)
    ) {
      return "COMPRIMIDO";
    }
    
    // Por defecto
    return "OTRO";
  };

  /**
   * Formatea el tamaño del archivo en formato legible.
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;

    // Validar tamaño (3GB = 3072 MB = 3221225472 bytes)
    const maxSize = 3 * 1024 * 1024 * 1024; // 3GB en bytes
    if (f.size > maxSize) {
      setError(`El archivo es demasiado grande. Tamaño máximo: 3GB. Tamaño actual: ${formatFileSize(f.size)}`);
      setFile(null);
      setPreview("");
      return;
    }

    setFile(f);
    setError("");

    // Detectar tipo automáticamente
    const detectedTipo = detectTipoEvidencia(f.name, f.type);
    setTipo(detectedTipo);

    // Vista previa solo para imágenes
    if (f.type.startsWith("image/")) {
      setPreview(URL.createObjectURL(f));
    } else {
      setPreview("");
    }
  };

  const upload = async () => {
    if (!file) {
      setError("Selecciona un archivo");
      return;
    }

    setError("");
    setUploading(true);
    setUploadProgress(0);

    try {
      // Crear FormData con el archivo y metadatos
      const formData = new FormData();
      formData.append("file", file);
      formData.append("ot", otId);
      formData.append("tipo", tipo);
      formData.append("descripcion", descripcion || file.name);

      // Usar XMLHttpRequest para monitorear progreso en archivos grandes
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
            let errorMessage = `Error al subir archivo: ${xhr.statusText}`;
            try {
              const errorData = JSON.parse(xhr.responseText);
              errorMessage = errorData.detail || errorMessage;
              
              // Mensaje específico para NoSuchBucket
              if (errorMessage.includes("NoSuchBucket")) {
                errorMessage = "El bucket de almacenamiento no existe. Por favor, contacta al administrador del sistema.";
              }
            } catch {
              // Si no se puede parsear, usar el mensaje por defecto
              if (xhr.status === 500) {
                errorMessage = "Error del servidor al subir el archivo. Por favor, intenta nuevamente.";
              }
            }
            reject(new Error(errorMessage));
          }
        });

        xhr.addEventListener("error", () => {
          reject(new Error("Error de red al subir archivo"));
        });

        xhr.addEventListener("abort", () => {
          reject(new Error("Subida cancelada"));
        });

        // Configurar request
        xhr.open("POST", ENDPOINTS.EVIDENCE_PRESIGN);
        
        // Obtener token de las cookies para la autorización
        const token = document.cookie
          .split("; ")
          .find((row) => row.startsWith("pgf_access="))
          ?.split("=")[1];
        
        if (token) {
          xhr.setRequestHeader("Authorization", `Bearer ${token}`);
        }
        
        // No establecer Content-Type, el navegador lo hará automáticamente con el boundary correcto
        xhr.withCredentials = true; // Incluir cookies
        
        xhr.send(formData);
      });

      toast.success("Evidencia subida correctamente");
      invalidateCache("EVIDENCES");
      invalidateCache("WORKORDERS");
      router.refresh();
      router.push(`/workorders/${otId}/evidences`);
    } catch (err: any) {
      console.error("Error al subir evidencia:", err);
      const errorMessage = err.message || "Error al subir evidencia";
      setError(errorMessage);
      toast.error(errorMessage);
      
      // Manejar errores específicos
      if (err.message && err.message.includes("403")) {
        toast.error("Permisos insuficientes. No tiene acceso para subir evidencias.");
        setTimeout(() => {
          router.push(getRoleHomePage(user?.rol));
        }, 2000);
      }
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <RoleGuard allow={["MECANICO", "JEFE_TALLER", "ADMIN"]}>
      <div className="p-6 max-w-2xl mx-auto space-y-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Subir Evidencia</h1>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-6">
        <div>
          <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
            Descripción
          </label>
          <input
            className="input w-full"
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
            placeholder="ej: Foto del daño en el motor, Hoja de cálculo de costos, etc."
          />
        </div>

        <div>
          <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
            Archivo (hasta 3GB)
          </label>
          <input
            type="file"
            onChange={onFileChange}
            className="input w-full"
            accept="image/*,.pdf,.xlsx,.xls,.csv,.doc,.docx,.zip,.rar,.7z"
          />
          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            Formatos soportados: Imágenes (JPEG, PNG, GIF, WebP, BMP), PDFs, Hojas de cálculo (Excel, CSV), 
            Documentos Word, Archivos comprimidos (ZIP, RAR, 7Z), y otros. Tamaño máximo: 3GB
          </p>
          {file && (
            <div className="mt-2 p-3 bg-gray-50 dark:bg-gray-700 rounded">
              <p className="text-sm text-gray-700 dark:text-gray-300">
                <strong>Archivo seleccionado:</strong> {file.name}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Tamaño: {formatFileSize(file.size)}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Tipo detectado: {tipo}
              </p>
            </div>
          )}
        </div>

        <div>
          <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
            Tipo de Evidencia
          </label>
          <select
            className="input w-full"
            value={tipo}
            onChange={(e) => setTipo(e.target.value)}
          >
            <option value="FOTO">FOTO</option>
            <option value="PDF">PDF</option>
            <option value="HOJA_CALCULO">HOJA_CALCULO</option>
            <option value="DOCUMENTO">DOCUMENTO</option>
            <option value="COMPRIMIDO">COMPRIMIDO</option>
            <option value="OTRO">OTRO</option>
          </select>
        </div>

        {preview && (
          <div className="mt-4">
            <p className="label mb-2">Vista previa</p>
            <img src={preview} className="rounded shadow max-h-60 mx-auto" alt="Preview" />
          </div>
        )}

        {uploading && (
          <div className="mt-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-700 dark:text-gray-300">Subiendo archivo...</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {Math.round(uploadProgress)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
              <div
                className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
          </div>
        )}

        {error && (
          <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded">
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}

        <div className="flex gap-4 pt-4">
          <button
            onClick={() => router.back()}
            className="flex-1 px-4 py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
          >
            Cancelar
          </button>
          <button
            onClick={upload}
            disabled={uploading || !file}
            className="flex-1 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Subiendo...
              </span>
            ) : (
              "Subir Evidencia"
            )}
          </button>
        </div>
      </div>
      </div>
    </RoleGuard>
  );
}
