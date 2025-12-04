"use client";

import { useEffect, useState } from "react";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";
import RoleGuard from "@/components/RoleGuard";
import { ENDPOINTS } from "@/lib/constants";
import { PlusIcon, PencilIcon, TrashIcon, MagnifyingGlassIcon } from "@heroicons/react/24/outline";
import { invalidateCache } from "@/lib/dataRefresh";

interface Repuesto {
  id: string;
  codigo: string;
  nombre: string;
  descripcion: string;
  marca: string;
  categoria: string;
  precio_referencia: number;
  unidad_medida: string;
  activo: boolean;
  stock_actual: number;
  necesita_reorden: boolean;
  created_at: string;
}

export default function RepuestosPage() {
  const [repuestos, setRepuestos] = useState<Repuesto[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [editingRepuesto, setEditingRepuesto] = useState<Repuesto | null>(null);
  const [formData, setFormData] = useState({
    codigo: "",
    nombre: "",
    descripcion: "",
    marca: "",
    categoria: "",
    precio_referencia: "",
    unidad_medida: "UNIDAD",
    cantidad_minima: "",
    ubicacion: "",
  });
  const toast = useToast();
  const { user } = useAuth();

  const canEdit = user?.rol === "BODEGA" || user?.rol === "ADMIN";

  const [marcas, setMarcas] = useState<{ id: number; nombre: string; activa: boolean }[]>([]);
  const [loadingMarcas, setLoadingMarcas] = useState(true);

  useEffect(() => {
    loadRepuestos();
    loadMarcas();
  }, []);

  const loadMarcas = async () => {
    try {
      setLoadingMarcas(true);
      const response = await fetch("/api/proxy/vehicles/marcas", {
        credentials: "include",
      });
      if (response.ok) {
        const text = await response.text();
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
        console.error("Error al cargar marcas:", response.status, response.statusText);
      }
    } catch (error) {
      console.error("Error loading marcas:", error);
    } finally {
      setLoadingMarcas(false);
    }
  };

  const loadRepuestos = async () => {
    try {
      setLoading(true);
      const response = await fetch(ENDPOINTS.INVENTORY_REPUESTOS, {
        credentials: "include",
      });
      
      if (!response.ok) {
        throw new Error("Error al cargar repuestos");
      }
      
      const data = await response.json();
      setRepuestos(Array.isArray(data) ? data : data.results || []);
    } catch (error) {
      console.error("Error loading repuestos:", error);
      toast.error("Error al cargar repuestos");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const url = editingRepuesto
        ? ENDPOINTS.INVENTORY_REPUESTO(editingRepuesto.id)
        : ENDPOINTS.INVENTORY_REPUESTOS;
      
      const method = editingRepuesto ? "PUT" : "POST";
      
      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          codigo: formData.codigo,
          nombre: formData.nombre,
          descripcion: formData.descripcion,
          marca: formData.marca,
          categoria: formData.categoria,
          precio_referencia: formData.precio_referencia ? parseFloat(formData.precio_referencia) : null,
          unidad_medida: formData.unidad_medida,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Error al guardar repuesto");
      }

      const repuestoData = await response.json();
      
      // Si se creó un nuevo repuesto y se especificó cantidad_minima o ubicacion, actualizar el stock
      if (!editingRepuesto && (formData.cantidad_minima || formData.ubicacion)) {
        try {
          // Obtener el stock del repuesto recién creado
          const stockResponse = await fetch(ENDPOINTS.INVENTORY_STOCK, {
            credentials: "include",
          });
          
          if (stockResponse.ok) {
            const stocks = await stockResponse.json();
            const stockArray = Array.isArray(stocks) ? stocks : stocks.results || [];
            const stock = stockArray.find((s: any) => s.repuesto === repuestoData.id);
            
            if (stock) {
              // Actualizar stock con cantidad_minima y ubicacion
              await fetch(ENDPOINTS.INVENTORY_STOCK_UPDATE(stock.id), {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({
                  cantidad_minima: formData.cantidad_minima ? parseInt(formData.cantidad_minima) : 0,
                  ubicacion: formData.ubicacion || "",
                }),
              });
            }
          }
        } catch (stockError) {
          console.warn("No se pudo actualizar el stock inicial:", stockError);
          // No fallar la creación del repuesto si falla la actualización del stock
        }
      }

      toast.success(
        editingRepuesto ? "Repuesto actualizado" : "Repuesto creado"
      );
      invalidateCache("INVENTORY");
      setShowModal(false);
      resetForm();
      loadRepuestos();
    } catch (error: any) {
      toast.error(error.message || "Error al guardar repuesto");
    }
  };

  const handleEdit = (repuesto: Repuesto) => {
    setEditingRepuesto(repuesto);
    setFormData({
      codigo: repuesto.codigo,
      nombre: repuesto.nombre,
      descripcion: repuesto.descripcion || "",
      marca: repuesto.marca || "",
      categoria: repuesto.categoria || "",
      precio_referencia: repuesto.precio_referencia?.toString() || "",
      unidad_medida: repuesto.unidad_medida || "UNIDAD",
      cantidad_minima: "",
      ubicacion: "",
    });
    setShowModal(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm("¿Está seguro de desactivar este repuesto?")) return;

    try {
      const response = await fetch(ENDPOINTS.INVENTORY_REPUESTO(id), {
        method: "DELETE",
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error("Error al desactivar repuesto");
      }

      toast.success("Repuesto desactivado");
      invalidateCache("INVENTORY");
      loadRepuestos();
    } catch (error) {
      toast.error("Error al desactivar repuesto");
    }
  };

  const resetForm = () => {
    setFormData({
      codigo: "",
      nombre: "",
      descripcion: "",
      marca: "",
      categoria: "",
      precio_referencia: "",
      unidad_medida: "UNIDAD",
      cantidad_minima: "",
      ubicacion: "",
    });
    setEditingRepuesto(null);
  };

  const filteredRepuestos = repuestos.filter(
    (r) =>
      r.codigo.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (r.marca && r.marca.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <RoleGuard allowedRoles={["BODEGA", "ADMIN", "JEFE_TALLER", "SUPERVISOR"]}>
      <div className="p-6 max-w-7xl mx-auto">
        <div className="flex flex-col gap-6">
          {/* PageHeading */}
          <header className="flex flex-wrap items-center justify-between gap-4">
            <h2 className="text-3xl font-bold text-gray-800 dark:text-white leading-tight">
              Listado de Repuestos
            </h2>
            {canEdit && (
              <button
                onClick={() => {
                  resetForm();
                  setShowModal(true);
                }}
                className="flex items-center gap-2 px-4 py-2 bg-[#003DA5] hover:bg-[#002D7A] text-white rounded-lg transition-colors font-semibold text-sm shadow-md hover:shadow-lg"
              >
                <PlusIcon className="w-5 h-5" />
                <span>Añadir Nuevo Repuesto</span>
              </button>
            )}
          </header>
          
          {/* Search and Filters */}
          <div className="flex flex-col gap-4">
            {/* SearchBar */}
            <div>
              <label className="flex flex-col w-full">
                <div className="flex w-full flex-1 items-stretch rounded-lg h-12 bg-white dark:bg-gray-800 ring-1 ring-gray-200 dark:ring-gray-700 focus-within:ring-2 focus-within:ring-[#003DA5]">
                  <div className="text-gray-400 dark:text-gray-400 flex items-center justify-center pl-4">
                    <MagnifyingGlassIcon className="w-5 h-5" />
                  </div>
                  <input
                    type="text"
                    placeholder="Buscar por nombre o código SKU..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-r-lg text-gray-800 dark:text-white focus:outline-0 focus:ring-0 border-none bg-transparent h-full placeholder:text-gray-400 dark:placeholder:text-gray-400 pl-2 text-base font-normal leading-normal"
                  />
                </div>
              </label>
            </div>
          </div>

          {/* Table */}
          {loading ? (
            <div className="text-center py-12">
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#003DA5]"></div>
                <span className="ml-3 text-gray-600 dark:text-white">Cargando...</span>
              </div>
            </div>
          ) : (
            <div className="overflow-hidden rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
              <table className="table">
                <thead>
                  <tr>
                    <th scope="col" className="text-gray-900 dark:text-white">Nombre</th>
                    <th scope="col" className="text-gray-900 dark:text-white">Código (SKU)</th>
                    <th scope="col" className="text-gray-900 dark:text-white">Stock</th>
                    <th scope="col" className="text-gray-900 dark:text-white">Precio Unitario</th>
                    <th scope="col" className="text-gray-900 dark:text-white">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRepuestos.map((repuesto) => (
                    <tr key={repuesto.id} className="table-row">
                      <th scope="row" className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                        {repuesto.nombre}
                      </th>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-white">
                        {repuesto.codigo}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={`badge ${
                          repuesto.necesita_reorden ? "badge-danger" : "badge-success"
                        }`}>
                          <span className="h-2 w-2 rounded-full bg-current mr-1.5"></span>
                          {repuesto.stock_actual || 0} Unidades
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-white">
                        {repuesto.precio_referencia
                          ? `$${repuesto.precio_referencia.toLocaleString()}`
                          : "-"}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-[#003DA5] hover:text-[#002D7A]">
                        {canEdit ? (
                          <div className="flex justify-end gap-2">
                            <button
                              onClick={() => handleEdit(repuesto)}
                              className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700"
                              title="Editar"
                            >
                              <PencilIcon className="w-5 h-5" />
                            </button>
                            <button
                              onClick={() => handleDelete(repuesto.id)}
                              className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700"
                              title="Eliminar"
                            >
                              <TrashIcon className="w-5 h-5" />
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => handleEdit(repuesto)}
                            className="text-[#003DA5] hover:text-[#002D7A] hover:underline cursor-pointer"
                          >
                            Detalle/Editar
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {filteredRepuestos.length === 0 && (
                <div className="text-center py-12 text-gray-500 dark:text-white">
                  No se encontraron repuestos
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal de creación/edición */}
        {showModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                {editingRepuesto ? "Editar Repuesto" : "Nuevo Repuesto"}
              </h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Código *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.codigo}
                      onChange={(e) =>
                        setFormData({ ...formData, codigo: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Unidad de Medida
                    </label>
                    <select
                      value={formData.unidad_medida}
                      onChange={(e) =>
                        setFormData({ ...formData, unidad_medida: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                    >
                      <option value="UNIDAD">Unidad</option>
                      <option value="LITRO">Litro</option>
                      <option value="KILO">Kilo</option>
                      <option value="METRO">Metro</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Nombre *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.nombre}
                    onChange={(e) =>
                      setFormData({ ...formData, nombre: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Marca
                    </label>
                    <select
                      value={formData.marca}
                      onChange={(e) =>
                        setFormData({ ...formData, marca: e.target.value })
                      }
                      disabled={loadingMarcas}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <option value="">
                        {loadingMarcas ? "Cargando marcas..." : "Seleccionar marca..."}
                      </option>
                      {marcas
                        .filter((m) => m.activa)
                        .map((marca) => (
                          <option key={marca.id} value={marca.nombre}>
                            {marca.nombre}
                          </option>
                        ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Categoría
                    </label>
                    <input
                      type="text"
                      value={formData.categoria}
                      onChange={(e) =>
                        setFormData({ ...formData, categoria: e.target.value })
                      }
                      placeholder="Ej: Frenos, Motor, Transmisión"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Precio de Referencia
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.precio_referencia}
                    onChange={(e) =>
                      setFormData({ ...formData, precio_referencia: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Descripción
                  </label>
                  <textarea
                    value={formData.descripcion}
                    onChange={(e) =>
                      setFormData({ ...formData, descripcion: e.target.value })
                    }
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  />
                </div>
                {!editingRepuesto && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Cantidad Mínima (Stock Inicial)
                      </label>
                      <input
                        type="number"
                        min="0"
                        value={formData.cantidad_minima}
                        onChange={(e) =>
                          setFormData({ ...formData, cantidad_minima: e.target.value })
                        }
                        placeholder="Nivel de reorden"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                      />
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        Alerta cuando el stock llegue a este valor
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Ubicación en Bodega
                      </label>
                      <input
                        type="text"
                        value={formData.ubicacion}
                        onChange={(e) =>
                          setFormData({ ...formData, ubicacion: e.target.value })
                        }
                        placeholder="Ej: Estante A-3, Pasillo 2"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                      />
                    </div>
                  </div>
                )}
                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowModal(false);
                      resetForm();
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                  >
                    {editingRepuesto ? "Actualizar" : "Crear"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </RoleGuard>
  );
}

