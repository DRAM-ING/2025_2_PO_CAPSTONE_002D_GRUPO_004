"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ENDPOINTS } from "@/lib/constants";
import { useToast } from "@/components/ToastContainer";
import { validateWorkOrder } from "@/lib/validations";
import RoleGuard from "@/components/RoleGuard";
import { useAuth } from "@/store/auth";
import { invalidateCache } from "@/lib/dataRefresh";

export default function CreateWorkOrder() {
  const router = useRouter();
  const toast = useToast();
  const { hasRole } = useAuth();
  const [vehiculos, setVehiculos] = useState<any[]>([]);
  const [usuarios, setUsuarios] = useState<any[]>([]);
  const [repuestos, setRepuestos] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [otActivaInfo, setOtActivaInfo] = useState<{ existe: boolean; id?: string } | null>(null);
  const [form, setForm] = useState({
    vehiculo: "",
    tipo: "MANTENCION",
    prioridad: "MEDIA",
    motivo: "",
    responsable: "",
  });

  const [items, setItems] = useState<any[]>([
    { tipo: "REPUESTO", descripcion: "", cantidad: 1, costo_unitario: 0, repuesto: null },
  ]);

  // -------------------------
  // CARGAR VEHÍCULOS Y USUARIOS
  // -------------------------
  useEffect(() => {
    const loadVehicles = async () => {
      try {
        const r = await fetch("/api/proxy/vehicles/", { credentials: "include" });
        if (r.ok) {
          const data = await r.json();
          setVehiculos(data.results || data || []);
        }
      } catch (error) {
        console.error("Error cargando vehículos:", error);
        toast.error("Error al cargar vehículos");
      }
    };
    
    const loadUsers = async () => {
      try {
        const r = await fetch("/api/proxy/users/", { credentials: "include" });
        if (r.ok) {
          const data = await r.json();
          const allUsers = data.results || data || [];
          // Filtrar solo roles autorizados para ser responsables de OTs
          // Roles permitidos: ADMIN, JEFE_TALLER, SUPERVISOR, COORDINADOR_ZONA, EJECUTIVO, SPONSOR, BODEGA
          // Roles NO permitidos: CHOFER, GUARDIA, MECANICO, RECEPCIONISTA
          const rolesPermitidos = ["ADMIN", "JEFE_TALLER", "SUPERVISOR", "COORDINADOR_ZONA", "EJECUTIVO", "SPONSOR", "BODEGA", "ADMINISTRATIVO_TALLER"];
          const usuariosFiltrados = allUsers.filter((u: any) => 
            u.rol && rolesPermitidos.includes(u.rol) && u.is_active !== false
          );
          setUsuarios(usuariosFiltrados);
        }
      } catch (error) {
        console.error("Error cargando usuarios:", error);
        toast.error("Error al cargar usuarios");
      }
    };
    
    const loadRepuestos = async () => {
      try {
        const r = await fetch("/api/proxy/inventory/repuestos/?activo=true", { credentials: "include" });
        if (r.ok) {
          const data = await r.json();
          setRepuestos(data.results || data || []);
        }
      } catch (error) {
        console.error("Error cargando repuestos:", error);
        // No mostrar error al usuario, solo loguear
      }
    };
    
    loadVehicles();
    loadUsers();
    loadRepuestos();
  }, [toast]);

  // -------------------------
  // HANDLERS
  // -------------------------
  const updateForm = (k: string, v: any) => {
    setForm((f) => ({ ...f, [k]: v }));
    
    // Si se cambia el vehículo, verificar si tiene OT activa y asignar responsable automáticamente
    if (k === "vehiculo" && v) {
      verificarOtActiva(v);
      // Buscar el vehículo seleccionado y asignar su supervisor como responsable
      const vehiculoSeleccionado = vehiculos.find((veh) => veh.id === v);
      if (vehiculoSeleccionado?.supervisor_detalle?.id) {
        setForm((f) => ({ ...f, responsable: vehiculoSeleccionado.supervisor_detalle.id }));
      } else if (vehiculoSeleccionado?.supervisor) {
        setForm((f) => ({ ...f, responsable: vehiculoSeleccionado.supervisor }));
      }
    } else if (k === "vehiculo" && !v) {
      setOtActivaInfo(null);
      setForm((f) => ({ ...f, responsable: "" }));
    }
  };

  // Verificar si el vehículo tiene una OT activa
  const verificarOtActiva = async (vehiculoId: string) => {
    try {
      const r = await fetch(
        `/api/proxy/work/ordenes/?vehiculo=${vehiculoId}&estado=ABIERTA,EN_EJECUCION,QA,EN_DIAGNOSTICO,EN_PAUSA`,
        { credentials: "include" }
      );
      if (r.ok) {
        const data = await r.json();
        const otsActivas = data.results || data || [];
        if (otsActivas.length > 0) {
          setOtActivaInfo({ existe: true, id: otsActivas[0].id });
        } else {
          setOtActivaInfo({ existe: false });
        }
      }
    } catch (error) {
      console.error("Error verificando OT activa:", error);
      // No mostrar error al usuario, solo loguear
    }
  };

  const updateItem = (i: number, k: string, v: any) => {
    const newItems = [...items];
    newItems[i][k] = v;

    // Si se selecciona un repuesto, auto-completar descripción y costo
    if (k === "repuesto" && v) {
      const selectedRepuesto = repuestos.find(r => r.id === v);
      if (selectedRepuesto) {
        newItems[i].descripcion = selectedRepuesto.nombre;
        newItems[i].costo_unitario = selectedRepuesto.precio_referencia || 0;
      }
    } else if (k === "tipo") {
      // Si cambia el tipo, resetear repuesto si no es REPUESTO
      if (v !== "REPUESTO") {
        newItems[i].repuesto = null;
      }
      // Si cambia a SERVICIO y había repuesto seleccionado, resetear costo
      if (v === "SERVICIO" && newItems[i].repuesto) {
        newItems[i].costo_unitario = 0;
      }
    }

    setItems(newItems);
    
    // Limpiar errores del campo modificado
    const key = `items.${i}.${k}`;
    if (errors[key]) {
      const newErrors = { ...errors };
      delete newErrors[key];
      setErrors(newErrors);
    }
  };

  const addItem = () => {
    setItems((x) => [
      ...x,
      { tipo: "REPUESTO", descripcion: "", cantidad: 1, costo_unitario: 0, repuesto: null },
    ]);
  };

  const removeItem = (i: number) => {
    setItems((x) => x.filter((_, idx) => idx !== i));
  };

  // -------------------------
  // ENVIAR FORMULARIO
  // -------------------------
  const submit = async () => {
    // Validar formulario
    const validation = validateWorkOrder({ ...form, items });
    if (!validation.isValid) {
      setErrors(validation.errors);
      toast.error("Por favor corrige los errores en el formulario");
      return;
    }

    setLoading(true);
    setErrors({});

    try {
      // Validar que el vehículo esté seleccionado
      if (!form.vehiculo || form.vehiculo === "" || form.vehiculo === "0") {
        setErrors({ vehiculo: "El vehículo es obligatorio" });
        toast.error("Por favor selecciona un vehículo");
        setLoading(false);
        return;
      }

      // Preparar items_data, asegurando que repuesto se envíe cuando corresponda
      const items_data = items.map(item => {
        const itemData: any = {
          tipo: item.tipo,
          descripcion: item.descripcion,
          cantidad: item.cantidad,
          costo_unitario: item.costo_unitario,
        };
        // Si es REPUESTO y tiene repuesto, incluirlo
        if (item.tipo === "REPUESTO" && item.repuesto) {
          itemData.repuesto = item.repuesto;
        }
        return itemData;
      });

      const r = await fetch("/api/proxy/work/ordenes/", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...form,
          vehiculo: form.vehiculo, // Mantener como string (UUID)
          responsable: form.responsable || null, // Asegurar que responsable se envíe (puede ser null si no se seleccionó)
          items_data: items_data, // El backend espera items_data, no items
        }),
      });

      const text = await r.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        data = { detail: text || "Error desconocido" };
      }

      if (!r.ok) {
        // Importar formateador de errores
        const { formatError, extractFieldErrors } = await import("@/lib/errorFormatter");
        
        // Manejar error específico de OT activa existente (solo para GUARDIA)
        if (data.errors?.vehiculo || data.detail?.includes("OT activa") || data.detail?.includes("ya cuenta con")) {
          const errorMsg = data.errors?.vehiculo || data.detail || "Este vehículo ya cuenta con una OT activa.";
          toast.error(
            errorMsg + " Si el vehículo fue ingresado por un guardia, la OT ya fue creada automáticamente. Por favor, edita la OT existente en lugar de crear una nueva."
          );
          setErrors({ vehiculo: errorMsg });
        } else {
          // Formatear error de manera amigable
          const friendlyError = formatError(data);
          toast.error(friendlyError);
          
          // Extraer errores por campo
          const fieldErrors = extractFieldErrors(data);
          if (Object.keys(fieldErrors).length > 0) {
            setErrors(fieldErrors);
          } else if (data.errors) {
            setErrors(data.errors);
          }
        }
        return;
      }

      // Si la creación fue exitosa, verificar si hay advertencia
      if (data.advertencia) {
        toast.warning(
          data.advertencia.mensaje + 
          (data.advertencia.ot_activa?.ot_id 
            ? ` Puedes ver la OT activa aquí: /workorders/${data.advertencia.ot_activa.ot_id}`
            : "")
        );
      } else {
        toast.success("Orden de trabajo creada correctamente");
      }
      
      // Invalidar cache y refrescar datos
      invalidateCache("WORKORDERS");
      router.refresh();
      router.push("/workorders");
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al crear la orden de trabajo");
    } finally {
      setLoading(false);
    }
  };

  // -------------------------
  // UI
  // -------------------------
  return (
    <RoleGuard allow={["JEFE_TALLER", "ADMIN", "GUARDIA"]}>
      <div className="p-8 space-y-12 max-w-3xl mx-auto">
        <div className="mb-4">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Crear Orden de Trabajo</h1>
          {hasRole(["GUARDIA"]) && (
            <div className="mt-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
              <p className="text-sm text-blue-800 dark:text-blue-300">
                <strong>Nota para Guardia:</strong> Para crear una OT al registrar el ingreso de un vehículo, 
                usa la opción <Link href="/vehicles/ingreso" className="underline font-medium">"Registrar Ingreso"</Link> 
                que crea la OT automáticamente.
              </p>
            </div>
          )}
        </div>

      {/* Datos principales */}
      <section className="space-y-4 bg-white dark:bg-gray-800 p-6 rounded shadow border border-gray-200 dark:border-gray-700">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Datos principales</h2>

        <div>
          <label className="block mb-1 font-medium text-gray-900 dark:text-gray-100">Vehículo *</label>
          <select
            className={`input ${errors.vehiculo ? "border-red-500" : ""}`}
            value={form.vehiculo}
            onChange={(e) => {
              updateForm("vehiculo", e.target.value);
              if (errors.vehiculo) {
                setErrors({ ...errors, vehiculo: "" });
              }
            }}
          >
            <option value="">Selecciona un vehículo...</option>
            {vehiculos.map((v: any) => (
              <option key={v.id} value={v.id}>
                {v.patente} — {v.marca} {v.modelo}
              </option>
            ))}
          </select>
          {errors.vehiculo && (
            <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.vehiculo}</p>
          )}
          {otActivaInfo?.existe && (
            <div className="mt-2 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
              <p className="text-sm text-yellow-800 dark:text-yellow-300">
                <strong>⚠️ Advertencia:</strong> Este vehículo ya tiene una OT activa. 
                {otActivaInfo.id && (
                  <> Por favor, <Link href={`/workorders/${otActivaInfo.id}`} className="underline font-medium">edita la OT existente</Link> en lugar de crear una nueva.</>
                )}
                {!otActivaInfo.id && (
                  <> Si el vehículo fue ingresado por un guardia, la OT ya fue creada automáticamente.</>
                )}
              </p>
            </div>
          )}
        </div>

        <div>
          <label className="block mb-1 text-gray-900 dark:text-gray-100 font-medium">Tipo</label>
          <select
            className="input"
            value={form.tipo}
            onChange={(e) => updateForm("tipo", e.target.value)}
          >
            <option value="MANTENCION">Mantención</option>
            <option value="REPARACION">Reparación</option>
            <option value="OTRO">Otro</option>
          </select>
        </div>

        <div>
          <label className="block mb-1 text-gray-900 dark:text-gray-100 font-medium">Prioridad</label>
          <select
            className="input"
            value={form.prioridad}
            onChange={(e) => updateForm("prioridad", e.target.value)}
          >
            <option value="ALTA">Alta</option>
            <option value="MEDIA">Media</option>
            <option value="BAJA">Baja</option>
          </select>
        </div>

        <div>
          <label className="block mb-1 font-medium text-gray-900 dark:text-gray-100">Motivo *</label>
          <textarea
            className={`input h-32 ${errors.motivo ? "border-red-500" : ""}`}
            value={form.motivo}
            onChange={(e) => {
              updateForm("motivo", e.target.value);
              if (errors.motivo) {
                setErrors({ ...errors, motivo: "" });
              }
            }}
            placeholder="Describe el motivo de la orden de trabajo..."
          />
          {errors.motivo && (
            <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.motivo}</p>
          )}
        </div>

        <div>
          <label className="block mb-1 font-medium text-gray-900 dark:text-gray-100">Responsable *</label>
          <select
            className={`input ${errors.responsable ? "border-red-500" : ""}`}
            value={form.responsable}
            onChange={(e) => {
              updateForm("responsable", e.target.value);
              if (errors.responsable) {
                setErrors({ ...errors, responsable: "" });
              }
            }}
          >
            <option value="">Selecciona un responsable...</option>
            {usuarios.map((u: any) => (
              <option key={u.id} value={u.id}>
                {u.first_name} {u.last_name} ({u.rol})
              </option>
            ))}
          </select>
          {errors.responsable && (
            <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.responsable}</p>
          )}
        </div>
      </section>

      {/* Items */}
      <section className="space-y-4 bg-white dark:bg-gray-800 p-6 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Items de la Orden</h2>
          <button
            type="button"
            onClick={addItem}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm font-medium"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Agregar Item
          </button>
        </div>

        {items.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
            <svg className="mx-auto h-12 w-12 text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
            <p className="text-sm">No hay items agregados</p>
            <p className="text-xs mt-1">Haz clic en "Agregar Item" para comenzar</p>
          </div>
        ) : (
          <div className="space-y-4">
            {items.map((item, i) => {
              const subtotal = (item.cantidad || 0) * (item.costo_unitario || 0);
              return (
                <div
                  key={i}
                  className="border-2 border-gray-200 dark:border-gray-700 p-5 rounded-lg bg-gray-50 dark:bg-gray-900/50 space-y-4 hover:border-blue-300 dark:hover:border-blue-700 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <span className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 font-semibold text-sm">
                        {i + 1}
                      </span>
                      <h3 className="font-medium text-gray-900 dark:text-white">Item #{i + 1}</h3>
                    </div>
                    {items.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeItem(i)}
                        className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 p-1 rounded transition-colors"
                        title="Eliminar item"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    )}
                  </div>

                  <div className="flex gap-4">
                    <div className="flex-1">
                      <label className="block mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Tipo</label>
                      <select
                        className={`input ${errors[`items.${i}.tipo`] ? "border-red-500" : ""}`}
                        value={item.tipo}
                        onChange={(e) => updateItem(i, "tipo", e.target.value)}
                      >
                        <option value="REPUESTO">Repuesto</option>
                        <option value="SERVICIO">Servicio (Mano de obra)</option>
                      </select>
                      {errors[`items.${i}.tipo`] && (
                        <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                          {errors[`items.${i}.tipo`]}
                        </p>
                      )}
                    </div>
                    {item.tipo === "REPUESTO" && (
                      <div className="flex-1">
                        <label className="block mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Repuesto</label>
                        <select
                          className="input"
                          value={item.repuesto || ""}
                          onChange={(e) => updateItem(i, "repuesto", e.target.value)}
                        >
                          <option value="">Seleccionar repuesto</option>
                          {repuestos.map((repuesto) => (
                            <option key={repuesto.id} value={repuesto.id}>
                              {repuesto.nombre} ({repuesto.codigo})
                            </option>
                          ))}
                        </select>
                      </div>
                    )}
                    <div className="flex-1">
                      <label className="block mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Cantidad *</label>
                      <input
                        type="number"
                        min="1"
                        className={`input ${errors[`items.${i}.cantidad`] ? "border-red-500" : ""}`}
                        value={item.cantidad}
                        onChange={(e) => {
                          updateItem(i, "cantidad", Number(e.target.value));
                        }}
                      />
                      {errors[`items.${i}.cantidad`] && (
                        <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                          {errors[`items.${i}.cantidad`]}
                        </p>
                      )}
                    </div>
                    <div className="flex-1">
                      <label className="block mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">
                        {item.tipo === "SERVICIO" ? "Costo por hora *" : "Costo unitario *"}
                      </label>
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        className={`input ${errors[`items.${i}.costo_unitario`] ? "border-red-500" : ""}`}
                        value={item.costo_unitario}
                        onChange={(e) => {
                          updateItem(i, "costo_unitario", Number(e.target.value));
                        }}
                        disabled={item.tipo === "REPUESTO" && item.repuesto !== null}
                      />
                      {errors[`items.${i}.costo_unitario`] && (
                        <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                          {errors[`items.${i}.costo_unitario`]}
                        </p>
                      )}
                    </div>
                  </div>
                  <div>
                    <label className="block mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">Descripción *</label>
                    <input
                      className={`input w-full ${errors[`items.${i}.descripcion`] ? "border-red-500" : ""}`}
                      value={item.descripcion}
                      onChange={(e) => {
                        updateItem(i, "descripcion", e.target.value);
                      }}
                      placeholder="Descripción del item..."
                      disabled={item.tipo === "REPUESTO" && item.repuesto_id !== null}
                    />
                    {errors[`items.${i}.descripcion`] && (
                      <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                        {errors[`items.${i}.descripcion`]}
                      </p>
                    )}
                  </div>
                  {item.tipo === "SERVICIO" && (
                    <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                      El costo por hora se multiplicará por el tiempo de ejecución del mecánico.
                    </p>
                  )}
                  {items.length > 1 && (
                    <button
                      type="button"
                      className="text-red-600 dark:text-red-400 hover:underline text-sm"
                      onClick={() => removeItem(i)}
                    >
                      Eliminar Item
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {items.length > 0 && (
          <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex justify-end">
              <div className="text-right">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total estimado:</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  ${items.reduce((sum, item) => sum + ((item.cantidad || 0) * (item.costo_unitario || 0)), 0).toLocaleString('es-CL', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
              </div>
            </div>
          </div>
        )}
      </section>

      <div className="flex gap-4">
        <button
          type="button"
          onClick={() => router.back()}
          className="flex-1 px-4 py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
        >
          Cancelar
        </button>
        <button
          type="button"
          className="flex-1 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={submit}
          disabled={loading}
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Creando...
            </span>
          ) : (
            "Crear Orden de Trabajo"
          )}
        </button>
      </div>
      </div>
    </RoleGuard>
  );
}
