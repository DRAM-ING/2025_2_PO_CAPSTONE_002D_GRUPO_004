"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useToast } from "@/components/ToastContainer";
import { validateWorkOrder } from "@/lib/validations";
import RoleGuard from "@/components/RoleGuard";
import { invalidateCache } from "@/lib/dataRefresh";

interface FormData {
  vehiculo: string;
  tipo: string;
  prioridad: string;
  motivo: string;
  responsable: string;
}

interface ItemData {
  id?: string | null;
  tipo: string;
  descripcion: string;
  cantidad: number;
  costo_unitario: number | string; // Puede ser string temporal mientras se escribe (formato con coma)
  repuesto: string | null;
}

export default function EditWorkOrder() {
  const router = useRouter();
  const params = useParams();
  const id = params?.id as string;
  const toast = useToast();

  const [vehiculos, setVehiculos] = useState<any[]>([]);
  const [usuarios, setUsuarios] = useState<any[]>([]);
  const [form, setForm] = useState<FormData | null>(null);
  const [items, setItems] = useState<ItemData[]>([]);
  const [repuestos, setRepuestos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Cargar datos iniciales
  useEffect(() => {
    if (!id) return;

    const loadData = async () => {
      try {
        setLoading(true);

        // Cargar OT
        const otRes = await fetch(`/api/proxy/work/ordenes/${id}/`, {
          credentials: "include",
        });

        if (!otRes.ok) {
          toast.error("Error al cargar la orden de trabajo");
          router.push("/workorders");
          return;
        }

        const otData = await otRes.json();

        // Cargar vehículo
        if (otData.vehiculo?.id) {
          const vehicleRes = await fetch(`/api/proxy/vehicles/${otData.vehiculo.id}/`, {
            credentials: "include",
          });
          if (vehicleRes.ok) {
            const vehicleData = await vehicleRes.json();
            setVehiculos([vehicleData]);
          } else {
            setVehiculos([otData.vehiculo]);
          }
        }

        // Inicializar formulario - asegurar que todos los campos estén presentes
        const formData: FormData = {
          vehiculo: String(otData.vehiculo?.id || otData.vehiculo || ""),
          tipo: otData.tipo || "MANTENCION",
          prioridad: otData.prioridad || "MEDIA",
          motivo: otData.motivo || "",
          responsable: String(otData.responsable?.id || otData.responsable || ""),
        };
        
        console.log("📝 Inicializando form con datos:", formData);
        console.log("📝 otData completo:", otData);
        setForm(formData);

        // Inicializar items
        const itemsData: ItemData[] = (otData.items || []).map((item: any) => {
          let repuestoId: string | null = null;
          if (item.repuesto) {
            if (typeof item.repuesto === "object" && item.repuesto.id) {
              repuestoId = String(item.repuesto.id);
            } else if (typeof item.repuesto === "string" && item.repuesto !== "") {
              repuestoId = item.repuesto;
            }
          } else if (item.repuesto_id) {
            repuestoId = String(item.repuesto_id);
          }

          // Normalizar costo_unitario
          let costo = 0;
          if (item.costo_unitario !== null && item.costo_unitario !== undefined) {
            if (typeof item.costo_unitario === 'string') {
              costo = parseFloat(item.costo_unitario.replace(',', '.')) || 0;
            } else if (typeof item.costo_unitario === 'number') {
              costo = item.costo_unitario;
            }
          }

          return {
            id: item.id || null,
            tipo: item.tipo || "REPUESTO",
            descripcion: item.descripcion || "",
            cantidad: Number(item.cantidad) || 1,
            costo_unitario: costo,
            repuesto: repuestoId,
          };
        });

        setItems(itemsData.length > 0 ? itemsData : [{
          tipo: "REPUESTO",
          descripcion: "",
          cantidad: 1,
          costo_unitario: 0,
          repuesto: null,
        }]);

        // Cargar repuestos
        const repuestosRes = await fetch(`/api/proxy/inventory/repuestos/?activo=true`, {
          credentials: "include",
        });
        if (repuestosRes.ok) {
          const repuestosData = await repuestosRes.json();
          setRepuestos(repuestosData.results || repuestosData || []);
        }

        // Cargar usuarios
        const usuariosRes = await fetch("/api/proxy/users/", { credentials: "include" });
        if (usuariosRes.ok) {
          const usuariosData = await usuariosRes.json();
          const allUsers = usuariosData.results || usuariosData || [];
          const rolesPermitidos = ["ADMIN", "JEFE_TALLER", "SUPERVISOR", "COORDINADOR_ZONA", "EJECUTIVO", "SPONSOR", "BODEGA", "ADMINISTRATIVO_TALLER"];
          const usuariosFiltrados = allUsers.filter((u: any) =>
            u.rol && rolesPermitidos.includes(u.rol) && u.is_active !== false
          );
          setUsuarios(usuariosFiltrados);
        }
      } catch (error) {
        console.error("Error cargando datos:", error);
        toast.error("Error al cargar la orden de trabajo");
        router.push("/workorders");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [id, router, toast]);

  // Actualizar campo del formulario
  const updateFormField = (field: keyof FormData, value: string) => {
    setForm((prev) => {
      if (!prev) return prev;
      return { ...prev, [field]: value };
    });
    // Limpiar error del campo
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  // Actualizar item
  const updateItem = (index: number, field: keyof ItemData, value: any) => {
    setItems((prevItems) => {
      const newItems = [...prevItems];
      if (!newItems[index]) {
        newItems[index] = {
          tipo: "REPUESTO",
          descripcion: "",
          cantidad: 1,
          costo_unitario: 0,
          repuesto: null,
        };
      }

      const updatedItem = { ...newItems[index], [field]: value };

      // Auto-completar cuando se selecciona un repuesto
      if (field === "repuesto" && value && value !== "" && value !== "0") {
        const selectedRepuesto = repuestos.find((r: any) => r.id === value);
        if (selectedRepuesto) {
          updatedItem.descripcion = selectedRepuesto.nombre || "";
          updatedItem.costo_unitario = selectedRepuesto.precio_referencia || 0;
        }
      } else if (field === "repuesto" && (!value || value === "" || value === "0")) {
        updatedItem.repuesto = null;
      }

      // Limpiar repuesto si cambia a SERVICIO
      if (field === "tipo" && value === "SERVICIO") {
        updatedItem.repuesto = null;
        if (updatedItem.descripcion === "") {
          updatedItem.costo_unitario = 0;
        }
      }

      newItems[index] = updatedItem;
      return newItems;
    });

    // Limpiar error del campo
    const errorKey = `items.${index}.${field}`;
    if (errors[errorKey]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[errorKey];
        return newErrors;
      });
    }
  };

  // Agregar item
  const addItem = () => {
    setItems((prev) => [
      ...prev,
      {
        tipo: "REPUESTO",
        descripcion: "",
        cantidad: 1,
        costo_unitario: 0,
        repuesto: null,
      },
    ]);
  };

  // Eliminar item
  const removeItem = (index: number) => {
    setItems((prev) => prev.filter((_, i) => i !== index));
  };

  // Enviar formulario
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    e.stopPropagation();

    // Validar que form esté cargado y tenga datos
    if (!form || saving) {
      console.error("❌ Form no está cargado o se está guardando");
      toast.error("Por favor espera a que se carguen los datos");
      return;
    }

    // Verificar que form tenga los campos necesarios (no esté vacío)
    if (Object.keys(form).length === 0) {
      console.error("❌ Form está vacío. Recargando datos...");
      toast.error("Error: El formulario está vacío. Por favor recarga la página.");
      // Intentar recargar los datos
      router.refresh();
      return;
    }

    // Verificar que form tenga los campos necesarios
    if (!form.vehiculo || !form.responsable) {
      console.error("❌ Form incompleto:", form);
      console.error("❌ vehiculo:", form.vehiculo);
      console.error("❌ responsable:", form.responsable);
      toast.error("Por favor completa todos los campos requeridos");
      return;
    }

    // Validar formulario
    console.log("🔍 Iniciando validación del formulario...");
    console.log("📋 Form actual:", form);
    console.log("📦 Items actuales:", items);
    
    const itemsForValidation = items
      .filter((item) => item && item.tipo)
      .map((item) => {
        // Normalizar costo_unitario: si es string con coma, convertir a número
        let costo = 0;
        if (typeof item.costo_unitario === 'string') {
          costo = parseFloat(item.costo_unitario.replace(',', '.')) || 0;
        } else if (typeof item.costo_unitario === 'number') {
          costo = item.costo_unitario;
        }
        
        // Normalizar repuesto: asegurar que sea string o null
        let repuesto = null;
        if (item.repuesto) {
          if (typeof item.repuesto === 'string' && item.repuesto !== '' && item.repuesto !== '0') {
            repuesto = item.repuesto;
          } else if (typeof item.repuesto === 'number') {
            repuesto = String(item.repuesto);
          }
        }
        
        return {
          tipo: item.tipo || "REPUESTO",
          descripcion: (item.descripcion || "").trim(),
          cantidad: Number(item.cantidad) || 1,
          costo_unitario: costo,
          repuesto: repuesto,
        };
      });

    console.log("📦 Items para validación:", itemsForValidation);

    // Asegurar que responsable sea string válido
    const responsableValue = form.responsable ? String(form.responsable).trim() : "";
    
    const validationData = {
      vehiculo: form.vehiculo ? String(form.vehiculo).trim() : "",
      tipo: form.tipo || "MANTENCION",
      prioridad: form.prioridad || "MEDIA",
      motivo: (form.motivo || "").trim(),
      responsable: responsableValue,
      items: itemsForValidation,
    };

    console.log("📊 Datos de validación:", validationData);

    const validation = validateWorkOrder(validationData);
    console.log("✅ Resultado de validación:", validation);
    console.log("📊 validationData completo:", JSON.stringify(validationData, null, 2));
    
    if (!validation.isValid) {
      console.error("❌ Errores de validación:", validation.errors);
      console.error("📋 Form completo:", JSON.stringify(form, null, 2));
      console.error("📦 Items completos:", JSON.stringify(items, null, 2));
      console.error("📊 validationData:", JSON.stringify(validationData, null, 2));
      
      // Si no hay errores específicos pero isValid es false, puede ser un problema con la validación
      if (Object.keys(validation.errors).length === 0) {
        console.error("⚠️ Validación falló pero no hay errores específicos. Revisar lógica de validación.");
        toast.error("Error de validación. Por favor verifica que todos los campos estén completos.");
        return;
      }
      
      setErrors(validation.errors);
      toast.error("Por favor corrige los errores en el formulario");
      return;
    }

    console.log("✅ Validación pasada, enviando datos...");
    setSaving(true);
    setErrors({});

    try {
      // Preparar items_data para el backend
      const items_data = items
        .filter((item) => {
          if (!item || !item.tipo) return false;
          const tieneDescripcion = item.descripcion && item.descripcion.trim() !== "";
          const tieneRepuesto = item.repuesto && item.repuesto !== "" && item.repuesto !== "0";
          if (item.tipo === "REPUESTO") {
            return tieneDescripcion || tieneRepuesto;
          }
          return tieneDescripcion;
        })
        .map((item) => {
          // Normalizar costo_unitario: manejar formato con coma
          let costo = 0;
          if (typeof item.costo_unitario === 'string') {
            costo = parseFloat(item.costo_unitario.replace(',', '.')) || 0;
          } else if (typeof item.costo_unitario === 'number') {
            costo = item.costo_unitario;
          }
          
          // Normalizar descripción - si está vacía y es REPUESTO con repuesto, usar nombre del repuesto
          let descripcion = (item.descripcion || "").trim();
          if (!descripcion && item.tipo === "REPUESTO" && item.repuesto) {
            // Buscar el nombre del repuesto en la lista cargada
            const repuestoSeleccionado = repuestos.find((r: any) => r.id === item.repuesto);
            if (repuestoSeleccionado) {
              descripcion = repuestoSeleccionado.nombre || "Repuesto";
            }
          }
          
          // Si después de todo sigue vacía, usar un valor por defecto
          if (!descripcion) {
            descripcion = item.tipo === "REPUESTO" ? "Repuesto" : "Servicio";
          }
          
          const itemData: any = {
            tipo: item.tipo,
            descripcion: descripcion,
            cantidad: Number(item.cantidad) || 1,
            costo_unitario: String(costo), // Django DecimalField espera string
          };

          if (item.tipo === "REPUESTO" && item.repuesto && item.repuesto !== "" && item.repuesto !== "0" && item.repuesto !== null) {
            itemData.repuesto = String(item.repuesto);
          }

          return itemData;
        });

      if (items_data.length === 0) {
        setErrors({ items: "Debe agregar al menos un item válido" });
        toast.error("Debe agregar al menos un item válido");
        setSaving(false);
        return;
      }

      // Asegurar responsable
      let responsableFinal = form.responsable;
      if (!responsableFinal || responsableFinal === "") {
        const otResponse = await fetch(`/api/proxy/work/ordenes/${id}/`, {
          credentials: "include",
        });
        if (otResponse.ok) {
          const otData = await otResponse.json();
          if (otData.responsable?.id) {
            responsableFinal = String(otData.responsable.id);
          } else if (otData.responsable) {
            responsableFinal = String(otData.responsable);
          }
        }
      }

      if (!responsableFinal || responsableFinal === "") {
        setErrors({ responsable: "El responsable es obligatorio" });
        toast.error("Debe seleccionar un responsable");
        setSaving(false);
        return;
      }

      // Preparar datos para enviar
      const payload = {
        tipo: form.tipo,
        prioridad: form.prioridad,
        motivo: (form.motivo || "").trim(),
        responsable: responsableFinal,
        items_data: items_data,
      };

      console.log("=== ENVIANDO DATOS AL BACKEND ===");
      console.log("Payload completo:", JSON.stringify(payload, null, 2));
      console.log("Items data:", JSON.stringify(items_data, null, 2));

      // Enviar al backend
      const response = await fetch(`/api/proxy/work/ordenes/${id}/`, {
        method: "PUT",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const responseText = await response.text();
      let responseData: any;
      try {
        responseData = responseText ? JSON.parse(responseText) : {};
      } catch {
        responseData = { detail: responseText || "Error desconocido" };
      }

      console.log("=== RESPUESTA DEL BACKEND ===");
      console.log("Status:", response.status);
      console.log("Status Text:", response.statusText);
      console.log("Response Text:", responseText);
      console.log("Response Data:", responseData);

      if (!response.ok) {
        console.error("❌ Error del backend:", responseData);
        console.error("❌ Status:", response.status);
        console.error("❌ Payload enviado:", JSON.stringify(payload, null, 2));
        
        // Manejar errores de validación del backend
        if (responseData && typeof responseData === 'object') {
          // Si hay errores de validación específicos
          if (responseData.errors) {
            setErrors(responseData.errors);
            // Mostrar el primer error
            const firstErrorKey = Object.keys(responseData.errors)[0];
            const firstError = responseData.errors[firstErrorKey];
            if (Array.isArray(firstError) && firstError.length > 0) {
              toast.error(`${firstErrorKey}: ${firstError[0]}`);
            } else if (typeof firstError === "string") {
              toast.error(`${firstErrorKey}: ${firstError}`);
            } else {
              toast.error(responseData.detail || "Error de validación");
            }
          } 
          // Si hay un mensaje de error general
          else if (responseData.detail) {
            toast.error(responseData.detail);
            // Si hay errores en el detail, intentar parsearlos
            if (typeof responseData.detail === 'object' && responseData.detail.errors) {
              setErrors(responseData.detail.errors);
            }
          }
          // Si hay errores directamente en el objeto (formato DRF)
          else {
            // Buscar errores en el objeto
            const errorKeys = Object.keys(responseData).filter(key => 
              Array.isArray(responseData[key]) || typeof responseData[key] === 'string'
            );
            if (errorKeys.length > 0) {
              setErrors(responseData);
              const firstErrorKey = errorKeys[0];
              const firstError = responseData[firstErrorKey];
              if (Array.isArray(firstError) && firstError.length > 0) {
                toast.error(`${firstErrorKey}: ${firstError[0]}`);
              } else if (typeof firstError === "string") {
                toast.error(`${firstErrorKey}: ${firstError}`);
              } else {
                toast.error("Error de validación");
              }
            } else {
              toast.error(`Error ${response.status}: ${response.statusText || "Error al actualizar la orden de trabajo"}`);
            }
          }
        } else {
          // Si responseData está vacío o no es un objeto válido
          const errorMessage = response.status === 400 
            ? "Error de validación. Por favor verifica que todos los campos estén correctos."
            : response.status === 403
            ? "No tienes permisos para editar esta orden de trabajo."
            : response.status === 404
            ? "La orden de trabajo no fue encontrada."
            : response.status === 500
            ? "Error interno del servidor. Por favor intenta nuevamente."
            : `Error ${response.status}: ${response.statusText || "Error desconocido"}`;
          
          toast.error(errorMessage);
        }
        setSaving(false);
        return;
      }

      console.log("✅ Orden de trabajo actualizada exitosamente");
      toast.success("Orden de trabajo actualizada correctamente");
      invalidateCache("WORKORDERS");
      // Pequeño delay para asegurar que el cache se invalide
      setTimeout(() => {
        router.replace(`/workorders/${id}`);
      }, 100);
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al actualizar la orden de trabajo");
      setSaving(false);
    }
  };

  if (loading || !form) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Cargando...</p>
        </div>
      </div>
    );
  }

  return (
    <RoleGuard allow={["JEFE_TALLER", "ADMIN"]}>
      <div className="p-8 max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">
          Editar Orden de Trabajo #{id}
        </h1>

        <form onSubmit={handleSubmit} className="space-y-6" noValidate>
          {/* Datos principales */}
          <section className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Datos principales
            </h2>

            <div className="space-y-4">
              {/* Vehículo (solo lectura) */}
              <div>
                <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">
                  Vehículo *
                </label>
                <select
                  className="input w-full bg-gray-100 dark:bg-gray-700"
                  value={form.vehiculo}
                  disabled
                >
                  {vehiculos.map((v: any) => (
                    <option key={v.id} value={v.id}>
                      {v.patente} — {v.marca_nombre || v.marca} {v.modelo}
                    </option>
                  ))}
                </select>
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  El vehículo no puede ser modificado
                </p>
              </div>

              {/* Tipo */}
              <div>
                <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">
                  Tipo
                </label>
                <select
                  className="input w-full"
                  value={form.tipo}
                  onChange={(e) => updateFormField("tipo", e.target.value)}
                >
                  <option value="MANTENCION">Mantención</option>
                  <option value="REPARACION">Reparación</option>
                  <option value="OTRO">Otro</option>
                </select>
              </div>

              {/* Prioridad */}
              <div>
                <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">
                  Prioridad
                </label>
                <select
                  className="input w-full"
                  value={form.prioridad}
                  onChange={(e) => updateFormField("prioridad", e.target.value)}
                >
                  <option value="ALTA">Alta</option>
                  <option value="MEDIA">Media</option>
                  <option value="BAJA">Baja</option>
                </select>
              </div>

              {/* Motivo */}
              <div>
                <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">
                  Motivo *
                </label>
                <textarea
                  className={`input w-full h-32 ${errors.motivo ? "border-red-500" : ""}`}
                  value={form.motivo}
                  onChange={(e) => updateFormField("motivo", e.target.value)}
                  placeholder="Describe el motivo de la orden de trabajo..."
                />
                {errors.motivo && (
                  <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.motivo}</p>
                )}
              </div>

              {/* Responsable */}
              <div>
                <label className="block mb-1 font-medium text-gray-700 dark:text-gray-300">
                  Responsable *
                </label>
                <select
                  className={`input w-full ${errors.responsable ? "border-red-500" : ""}`}
                  value={form.responsable}
                  onChange={(e) => updateFormField("responsable", e.target.value)}
                >
                  <option value="">Selecciona un responsable...</option>
                  {usuarios.map((u: any) => (
                    <option key={u.id} value={u.id}>
                      {u.first_name} {u.last_name} ({u.rol})
                    </option>
                  ))}
                </select>
                {errors.responsable && (
                  <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                    {errors.responsable}
                  </p>
                )}
              </div>
            </div>
          </section>

          {/* Items */}
          <section className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Items</h2>

            <div className="space-y-4">
              {items.length === 0 && (
                <p className="text-sm text-gray-500 dark:text-gray-400 italic">
                  No hay items. Agrega al menos un item para continuar.
                </p>
              )}

              {items.map((item, index) => (
                <div key={index} className="border dark:border-gray-700 p-4 rounded-lg space-y-3">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {/* Tipo */}
                    <div>
                      <label className="block mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">
                        Tipo
                      </label>
                      <select
                        className="input w-full"
                        value={item.tipo}
                        onChange={(e) => updateItem(index, "tipo", e.target.value)}
                      >
                        <option value="REPUESTO">Repuesto</option>
                        <option value="SERVICIO">Servicio</option>
                      </select>
                    </div>

                    {/* Repuesto (solo si es tipo REPUESTO) */}
                    {item.tipo === "REPUESTO" && (
                      <div>
                        <label className="block mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">
                          Repuesto
                        </label>
                        <select
                          className="input w-full"
                          value={item.repuesto || ""}
                          onChange={(e) => updateItem(index, "repuesto", e.target.value || null)}
                        >
                          <option value="">Seleccionar repuesto</option>
                          {repuestos.map((repuesto: any) => (
                            <option key={repuesto.id} value={repuesto.id}>
                              {repuesto.nombre} ({repuesto.codigo})
                            </option>
                          ))}
                        </select>
                      </div>
                    )}

                    {/* Cantidad */}
                    <div>
                      <label className="block mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">
                        Cantidad *
                      </label>
                      <input
                        type="number"
                        min="1"
                        className={`input w-full ${errors[`items.${index}.cantidad`] ? "border-red-500" : ""}`}
                        value={item.cantidad}
                        onChange={(e) => {
                          const val = parseInt(e.target.value) || 1;
                          updateItem(index, "cantidad", val > 0 ? val : 1);
                        }}
                      />
                      {errors[`items.${index}.cantidad`] && (
                        <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                          {errors[`items.${index}.cantidad`]}
                        </p>
                      )}
                    </div>

                    {/* Costo unitario */}
                    <div>
                      <label className="block mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">
                        {item.tipo === "SERVICIO" ? "Costo por hora *" : "Costo unitario *"}
                      </label>
                      <input
                        type="text"
                        className={`input w-full ${errors[`items.${index}.costo_unitario`] ? "border-red-500" : ""}`}
                        value={typeof item.costo_unitario === 'number' 
                          ? item.costo_unitario.toString().replace('.', ',') 
                          : (typeof item.costo_unitario === 'string' ? item.costo_unitario : '')}
                        onChange={(e) => {
                          // Permitir entrada con coma o punto, normalizar a número
                          let inputValue = e.target.value.replace(/[^\d,.-]/g, ''); // Solo números, coma, punto y guión
                          // Reemplazar coma por punto para parseFloat
                          const normalizedValue = inputValue.replace(',', '.');
                          const val = parseFloat(normalizedValue);
                          if (!isNaN(val) && val >= 0) {
                            // Guardar como número
                            updateItem(index, "costo_unitario", val);
                          } else if (inputValue === '' || inputValue === '-') {
                            // Permitir campo vacío o guión mientras se escribe (guardar como string temporal)
                            updateItem(index, "costo_unitario", inputValue);
                          } else {
                            // Si no es válido, mantener el valor anterior
                            const currentVal = item.costo_unitario;
                            if (typeof currentVal === 'number') {
                              updateItem(index, "costo_unitario", currentVal);
                            }
                          }
                        }}
                        onBlur={(e) => {
                          // Al perder el foco, asegurar que sea un número válido
                          const inputValue = e.target.value.replace(',', '.');
                          const val = parseFloat(inputValue);
                          if (isNaN(val) || val < 0) {
                            updateItem(index, "costo_unitario", 0);
                          } else {
                            updateItem(index, "costo_unitario", val);
                          }
                        }}
                        disabled={item.tipo === "REPUESTO" && item.repuesto !== null}
                        placeholder="0,00"
                      />
                      {errors[`items.${index}.costo_unitario`] && (
                        <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                          {errors[`items.${index}.costo_unitario`]}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Descripción */}
                  <div>
                    <label className="block mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">
                      Descripción *
                    </label>
                    <input
                      type="text"
                      className={`input w-full ${errors[`items.${index}.descripcion`] ? "border-red-500" : ""}`}
                      value={item.descripcion}
                      onChange={(e) => updateItem(index, "descripcion", e.target.value)}
                      placeholder="Descripción del item..."
                      disabled={item.tipo === "REPUESTO" && item.repuesto !== null}
                    />
                    {errors[`items.${index}.descripcion`] && (
                      <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                        {errors[`items.${index}.descripcion`]}
                      </p>
                    )}
                  </div>

                  {/* Botón eliminar */}
                  {items.length > 1 && (
                    <button
                      type="button"
                      className="text-red-600 dark:text-red-400 hover:underline text-sm"
                      onClick={() => removeItem(index)}
                    >
                      Eliminar item
                    </button>
                  )}
                </div>
              ))}

              {/* Botón agregar item */}
              <button
                type="button"
                className="btn w-full"
                onClick={addItem}
              >
                + Agregar item
              </button>
            </div>
          </section>

          {/* Botones de acción */}
          <div className="flex gap-4">
            <button
              type="button"
              onClick={() => router.back()}
              className="flex-1 px-4 py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={saving}
            >
              {saving ? (
                <span className="flex items-center justify-center">
                  <svg
                    className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  Guardando...
                </span>
              ) : (
                "Guardar Cambios"
              )}
            </button>
          </div>
        </form>
      </div>
    </RoleGuard>
  );
}
