"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";
import RoleGuard from "@/components/RoleGuard";
import Link from "next/link";
import { ENDPOINTS } from "@/lib/constants";
import { withSession } from "@/lib/api.client";
import { normalizarPatente } from "@/lib/validations";

interface Marca {
  id: number;
  nombre: string;
  activa: boolean;
}

/**
 * Página para que el Guardia registre el ingreso de vehículos al taller.
 * 
 * Esta página permite:
 * - Registrar ingreso de vehículo por patente
 * - Crear vehículo si no existe
 * - Generar OT automáticamente
 * - Agregar observaciones y kilometraje
 * 
 * Permisos:
 * - Solo GUARDIA puede acceder
 */
export default function IngresoVehiculoPage() {
  const router = useRouter();
  const toast = useToast();
  const { hasRole, user } = useAuth();

  const [form, setForm] = useState({
    patente: "",
    marca: "",
    modelo: "",
    anio: "",
    vin: "",
    observaciones: "",
    kilometraje: "",
    motivo: "",
    prioridad: "MEDIA",
    chofer_nombre: "",
    chofer_rut: "",
  });

  const [marcas, setMarcas] = useState<Marca[]>([]);
  const [loadingMarcas, setLoadingMarcas] = useState(true);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [ingresoRegistrado, setIngresoRegistrado] = useState<{ id: string; ot_generada?: any; vehiculo_id?: string } | null>(null);
  const [vehiculoEncontrado, setVehiculoEncontrado] = useState<any>(null);
  const [buscandoVehiculo, setBuscandoVehiculo] = useState(false);
  const [imagenes, setImagenes] = useState<File[]>([]);
  const [subiendoImagenes, setSubiendoImagenes] = useState(false);

  useEffect(() => {
    const cargarMarcas = async () => {
      try {
        setLoadingMarcas(true);
        const r = await fetch("/api/proxy/vehicles/marcas", {
          credentials: "include",
        });
        if (r.ok) {
          const text = await r.text();
          if (!text || text.trim() === "") {
            console.warn("Respuesta vacía al cargar marcas");
            setMarcas([]);
            return;
          }
          const data = JSON.parse(text);
          // Manejar tanto array directo como objeto con results
          const marcasData = Array.isArray(data) ? data : (data.results || data || []);
          setMarcas(marcasData);
          if (marcasData.length === 0) {
            console.warn("No se encontraron marcas activas");
          }
        } else {
          console.error("Error al cargar marcas:", r.status, r.statusText);
          toast.error("Error al cargar marcas");
        }
      } catch (error) {
        console.error("Error al cargar marcas:", error);
        toast.error("Error al cargar marcas");
      } finally {
        setLoadingMarcas(false);
      }
    };
    cargarMarcas();
  }, []); // toast es estable de Zustand, no necesita estar en dependencias

  // Verificar permisos - RoleGuard manejará la redirección si no tiene acceso

  const handleChange = (field: string, value: any) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    // Limpiar error del campo cuando el usuario empieza a escribir
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
    
    // Si cambia la patente, buscar el vehículo solo cuando tenga exactamente 6 caracteres
    if (field === "patente") {
      // Normalizar patente: quitar espacios, guiones y convertir a mayúsculas
      const patenteLimpia = value.replace(/\s/g, "").replace(/-/g, "").toUpperCase();
      // Actualizar el valor normalizado en el formulario
      setForm((prev) => ({ ...prev, patente: patenteLimpia }));
      
      if (patenteLimpia.length === 6) {
        buscarVehiculo(patenteLimpia);
      } else if (patenteLimpia.length === 0) {
        setVehiculoEncontrado(null);
      } else {
        // Si tiene menos de 6 caracteres, limpiar el vehículo encontrado
        setVehiculoEncontrado(null);
      }
    }
  };

  const buscarVehiculo = async (patente: string) => {
    // Solo buscar si la patente tiene exactamente 6 caracteres
    if (!patente || patente.length !== 6) {
      setVehiculoEncontrado(null);
      return;
    }
    
    setBuscandoVehiculo(true);
    try {
      // Buscar vehículo por patente exacta usando el endpoint de búsqueda
      const response = await fetch(`${ENDPOINTS.VEHICLES}?search=${encodeURIComponent(patente)}`, {
        method: "GET",
        ...withSession(),
      });

      if (response.ok) {
        const data = await response.json();
        const vehiculos = data.results || data || [];
        // Solo considerar el vehículo si la patente coincide EXACTAMENTE (case-insensitive)
        const patenteUpper = patente.toUpperCase().trim();
        const vehiculo = vehiculos.find((v: any) => v.patente && v.patente.toUpperCase().trim() === patenteUpper);
        
        if (vehiculo) {
          setVehiculoEncontrado(vehiculo);
          
          // Prellenar campos si el vehículo existe
          if (!form.marca) {
            // Buscar el ID de la marca: puede venir como ID o como nombre
            let marcaId = null;
            if (vehiculo.marca && typeof vehiculo.marca === 'number') {
              marcaId = vehiculo.marca;
            } else if (vehiculo.marca_nombre) {
              const marcaEncontrada = marcas.find(m => m.nombre === vehiculo.marca_nombre);
              marcaId = marcaEncontrada?.id;
            }
            if (marcaId) setForm(prev => ({ ...prev, marca: String(marcaId) }));
          }
          if (!form.modelo) setForm(prev => ({ ...prev, modelo: vehiculo.modelo || "" }));
          if (!form.anio) setForm(prev => ({ ...prev, anio: vehiculo.anio ? String(vehiculo.anio) : "" }));
          if (!form.vin) setForm(prev => ({ ...prev, vin: vehiculo.vin || "" }));
        } else {
          setVehiculoEncontrado(null);
        }
      } else {
        setVehiculoEncontrado(null);
      }
    } catch (error) {
      console.error("Error al buscar vehículo:", error);
      setVehiculoEncontrado(null);
    } finally {
      setBuscandoVehiculo(false);
    }
  };


  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrors({});

    // Validar patente (requerida)
    if (!form.patente.trim()) {
      setErrors({ patente: "La patente es requerida" });
      setLoading(false);
      return;
    }

    try {
      const response = await fetch("/api/proxy/vehicles/ingreso/", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          patente: form.patente.trim().toUpperCase(),
          marca: form.marca ? Number(form.marca) : undefined,
          modelo: form.modelo.trim() || undefined,
          anio: form.anio ? parseInt(form.anio) : undefined,
          vin: form.vin.trim() || undefined,
          observaciones: form.observaciones.trim() || undefined,
          kilometraje: form.kilometraje ? parseInt(form.kilometraje) : undefined,
          motivo: form.motivo.trim() || undefined,
          prioridad: form.prioridad,
          chofer_nombre: form.chofer_nombre.trim() || undefined,
          chofer_rut: form.chofer_rut.trim() || undefined,
        }),
      });

      const text = await response.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        data = { detail: text || "Error desconocido" };
      }

      if (!response.ok) {
        // Manejar errores de validación
        if (data.patente) {
          setErrors({ patente: Array.isArray(data.patente) ? data.patente[0] : data.patente });
        } else if (data.chofer_rut) {
          setErrors({ chofer_rut: Array.isArray(data.chofer_rut) ? data.chofer_rut[0] : data.chofer_rut });
          toast.error("Error en el RUT del chofer");
        } else if (data.detail) {
          toast.error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail));
        } else if (data.message) {
          toast.error(data.message);
        } else {
          toast.error("Error al registrar ingreso");
        }
        setLoading(false);
        return;
      }

      // Éxito
      toast.success("Ingreso registrado correctamente. OT creada automáticamente.");
      
      // Obtener ID del vehículo de la respuesta
      const vehiculoId = data.vehiculo?.id || data.vehiculo_detalle?.id || data.vehiculo_id || vehiculoEncontrado?.id;
      
      // Guardar información del ingreso para mostrar botón de PDF y subir imágenes
      setIngresoRegistrado({
        id: data.id,
        ot_generada: data.ot_generada,
        vehiculo_id: vehiculoId,
      });
      
      // Si se generó una OT, mostrar información
      if (data.ot_generada) {
        toast.success(`OT #${data.ot_generada.id} creada con estado ${data.ot_generada.estado}`);
      }

      // Si hay imágenes seleccionadas, subirlas ahora
      if (imagenes.length > 0 && vehiculoId) {
        await subirImagenes(vehiculoId);
      } else if (imagenes.length > 0) {
        toast.warning("No se pudo obtener el ID del vehículo para subir las imágenes. Intenta subirlas manualmente desde el historial.");
      }

      // Limpiar formulario
      setForm({
        patente: "",
        marca: "",
        modelo: "",
        anio: "",
        vin: "",
        observaciones: "",
        kilometraje: "",
        motivo: "",
        prioridad: "MEDIA",
        chofer_nombre: "",
        chofer_rut: "",
      });
      setImagenes([]);
    } catch (error) {
      console.error("Error al registrar ingreso:", error);
      toast.error("Error al registrar ingreso del vehículo");
      setLoading(false);
    }
  };

  const subirImagenes = async (vehiculoId: string) => {
    if (imagenes.length === 0) return;
    
    setSubiendoImagenes(true);
    try {
      for (const imagen of imagenes) {
        const formData = new FormData();
        formData.append("file", imagen);
        formData.append("tipo", "FOTO_INGRESO");
        formData.append("descripcion", `Foto del vehículo al ingreso - ${imagen.name}`);

        const response = await fetch(`/api/proxy/vehicles/${vehiculoId}/ingreso/evidencias/`, {
          method: "POST",
          credentials: "include",
          body: formData,
        });

        if (!response.ok) {
          const errorText = await response.text();
          console.error("Error al subir imagen:", errorText);
          toast.error(`Error al subir imagen ${imagen.name}`);
        }
      }
      
      if (imagenes.length > 0) {
        toast.success(`${imagenes.length} imagen(es) subida(s) correctamente`);
      }
    } catch (error) {
      console.error("Error al subir imágenes:", error);
      toast.error("Error al subir algunas imágenes");
    } finally {
      setSubiendoImagenes(false);
    }
  };

  const handleImagenChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setImagenes(prev => [...prev, ...files]);
  };

  const eliminarImagen = (index: number) => {
    setImagenes(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <RoleGuard 
      allow={["GUARDIA", "ADMIN", "JEFE_TALLER"]}
      redirectTo="/vehicles"
    >
      <div className="p-6 max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Registrar Ingreso de Vehículo
          </h1>
          <Link
            href="/vehicles"
            className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
          >
            ← Volver
          </Link>
        </div>

        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
          <p className="text-sm text-blue-800 dark:text-blue-300">
            <strong>Nota:</strong> Al registrar el ingreso de un vehículo, se creará automáticamente 
            una Orden de Trabajo (OT) con estado <strong>ABIERTA</strong>. Si el vehículo no existe 
            en el sistema, se creará automáticamente.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-6">
          {/* Información del Vehículo */}
          <div>
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              Información del Vehículo
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Patente (requerida) */}
              <div className="md:col-span-2">
                <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Patente <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={form.patente}
                    onChange={(e) => handleChange("patente", e.target.value)}
                    className={`w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
                      errors.patente ? "border-red-500" : "border-gray-300 dark:border-gray-600"
                    }`}
                    placeholder="ABC123"
                    required
                  />
                  {buscandoVehiculo && (
                    <div className="absolute right-3 top-2.5">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                    </div>
                  )}
                </div>
                {errors.patente && (
                  <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.patente}</p>
                )}
                {vehiculoEncontrado && (
                  <div className="mt-2 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-green-800 dark:text-green-300">
                          ✓ Vehículo encontrado: {vehiculoEncontrado.patente}
                        </p>
                        <p className="text-xs text-green-700 dark:text-green-400 mt-1">
                          {vehiculoEncontrado.marca_nombre || vehiculoEncontrado.marca || "Sin marca"} {vehiculoEncontrado.modelo} ({vehiculoEncontrado.anio || "N/A"})
                        </p>
                        <p className="text-xs text-green-700 dark:text-green-400">
                          Estado: {vehiculoEncontrado.estado}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Marca */}
              <div>
                <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Marca
                </label>
                <select
                  value={form.marca}
                  onChange={(e) => handleChange("marca", e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  disabled={loadingMarcas}
                >
                  <option value="">{loadingMarcas ? "Cargando marcas..." : "Seleccione una marca"}</option>
                  {marcas.map((marca) => (
                    <option key={marca.id} value={marca.id}>
                      {marca.nombre}
                    </option>
                  ))}
                </select>
              </div>

              {/* Modelo */}
              <div>
                <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Modelo
                </label>
                <input
                  type="text"
                  value={form.modelo}
                  onChange={(e) => handleChange("modelo", e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Hilux"
                />
              </div>

              {/* Año */}
              <div>
                <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Año
                </label>
                <input
                  type="number"
                  value={form.anio}
                  onChange={(e) => handleChange("anio", e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="2020"
                  min="1900"
                  max="2100"
                />
              </div>

              {/* VIN */}
              <div>
                <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                  VIN (Número de Chasis)
                </label>
                <input
                  type="text"
                  value={form.vin}
                  onChange={(e) => handleChange("vin", e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="123456789"
                />
              </div>
            </div>
          </div>

          {/* Subida de Imágenes */}
          <div>
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              Evidencias Fotográficas (Opcional)
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Subir Imágenes del Vehículo
                </label>
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={handleImagenChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  Puedes subir múltiples imágenes del estado del vehículo al ingreso
                </p>
              </div>
              
              {imagenes.length > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {imagenes.map((imagen, index) => (
                    <div key={index} className="relative group">
                      <img
                        src={URL.createObjectURL(imagen)}
                        alt={`Preview ${index + 1}`}
                        className="w-full h-32 object-cover rounded-lg border border-gray-300 dark:border-gray-600"
                      />
                      <button
                        type="button"
                        onClick={() => eliminarImagen(index)}
                        className="absolute top-2 right-2 bg-red-500 hover:bg-red-600 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Eliminar imagen"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                      <p className="mt-1 text-xs text-gray-600 dark:text-gray-400 truncate">
                        {imagen.name}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Información del Ingreso */}
          <div>
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              Información del Ingreso
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Motivo (para la OT) */}
              <div className="md:col-span-2">
                <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Motivo del Ingreso (para la OT)
                </label>
                <textarea
                  value={form.motivo}
                  onChange={(e) => handleChange("motivo", e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  rows={3}
                  placeholder="Ej: Reparación de parachoques, Mantención preventiva, etc."
                />
              </div>

              {/* Observaciones */}
              <div className="md:col-span-2">
                <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Observaciones
                </label>
                <textarea
                  value={form.observaciones}
                  onChange={(e) => handleChange("observaciones", e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  rows={3}
                  placeholder="Observaciones adicionales sobre el estado del vehículo..."
                />
              </div>

              {/* Kilometraje */}
              <div>
                <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Kilometraje
                </label>
                <input
                  type="number"
                  value={form.kilometraje}
                  onChange={(e) => handleChange("kilometraje", e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="50000"
                  min="0"
                />
              </div>

              {/* Prioridad */}
              <div>
                <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Prioridad de la OT
                </label>
                <select
                  value={form.prioridad}
                  onChange={(e) => handleChange("prioridad", e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="ALTA">Alta</option>
                  <option value="MEDIA">Media</option>
                  <option value="BAJA">Baja</option>
                </select>
              </div>

            </div>
          </div>

          {/* Información del Chofer */}
          <div>
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              Información del Chofer (Opcional)
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Nombre del Chofer */}
              <div>
                <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Nombre del Chofer
                </label>
                <input
                  type="text"
                  value={form.chofer_nombre}
                  onChange={(e) => handleChange("chofer_nombre", e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Juan Pérez"
                />
              </div>

              {/* RUT del Chofer */}
              <div>
                <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                  RUT del Chofer
                </label>
                <input
                  type="text"
                  value={form.chofer_rut}
                  onChange={(e) => handleChange("chofer_rut", e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
                    errors.chofer_rut ? "border-red-500" : "border-gray-300 dark:border-gray-600"
                  }`}
                  placeholder="12345678-5"
                />
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  Formato: 12345678-5 o 123456785 (opcional - si el chofer ya existe, se usará el existente)
                </p>
                {errors.chofer_rut && (
                  <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.chofer_rut}</p>
                )}
              </div>
            </div>
          </div>

          {/* Botones */}
          <div className="flex gap-4 pt-4">
            <button
              type="button"
              onClick={() => router.back()}
              className="flex-1 px-4 py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading || subiendoImagenes}
              className="flex-1 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading || subiendoImagenes ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {subiendoImagenes ? "Subiendo imágenes..." : "Registrando..."}
                </span>
              ) : (
                "Registrar Ingreso y Crear OT"
              )}
            </button>
          </div>
        </form>

        {/* Botón para descargar PDF del ticket */}
        {ingresoRegistrado && (
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
              ✓ Ingreso Registrado Exitosamente
            </h3>
            <div className="space-y-3">
              <p className="text-sm text-gray-700 dark:text-gray-300">
                El ingreso ha sido registrado correctamente. Puedes descargar el ticket en PDF.
              </p>
              {ingresoRegistrado.ot_generada && (
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  <strong>OT Generada:</strong> #{ingresoRegistrado.ot_generada.id.slice(0, 8)} - Estado: {ingresoRegistrado.ot_generada.estado}
                </p>
              )}
              <div className="flex gap-3">
                <button
                  onClick={async () => {
                    try {
                      const response = await fetch(
                        ENDPOINTS.VEHICLES_TICKET_INGRESO(ingresoRegistrado.id),
                        {
                          method: "GET",
                          ...withSession(),
                        }
                      );

                      if (!response.ok) {
                        toast.error("Error al generar el ticket PDF");
                        return;
                      }

                      // Descargar el PDF
                      const blob = await response.blob();
                      const url = window.URL.createObjectURL(blob);
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = `ticket_ingreso_${ingresoRegistrado.id.slice(0, 8)}.pdf`;
                      document.body.appendChild(a);
                      a.click();
                      window.URL.revokeObjectURL(url);
                      document.body.removeChild(a);
                      toast.success("Ticket PDF descargado correctamente");
                    } catch (error) {
                      console.error("Error al descargar PDF:", error);
                      toast.error("Error al descargar el ticket PDF");
                    }
                  }}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
                >
                  📄 Descargar Ticket PDF
                </button>
                {ingresoRegistrado.ot_generada && (
                  <Link
                    href={`/workorders/${ingresoRegistrado.ot_generada.id}`}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors font-medium"
                  >
                    Ver OT Generada
                  </Link>
                )}
                <button
                  onClick={() => {
                    setIngresoRegistrado(null);
                  }}
                  className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
                >
                  Registrar Otro Ingreso
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </RoleGuard>
  );
}

