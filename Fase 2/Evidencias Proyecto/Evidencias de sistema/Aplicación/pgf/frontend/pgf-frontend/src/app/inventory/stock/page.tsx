"use client";

import { useEffect, useState } from "react";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";
import RoleGuard from "@/components/RoleGuard";
import { ENDPOINTS } from "@/lib/constants";
import { PlusIcon, PencilIcon, ArrowUpIcon, AdjustmentsHorizontalIcon, ExclamationTriangleIcon } from "@heroicons/react/24/outline";
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { invalidateCache } from "@/lib/dataRefresh";

interface Stock {
  id: string;
  repuesto: string;
  repuesto_nombre: string;
  repuesto_codigo: string;
  cantidad_actual: number;
  cantidad_minima: number;
  ubicacion: string;
  necesita_reorden: boolean;
  updated_at: string;
}

export default function StockPage() {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [showEntradaModal, setShowEntradaModal] = useState(false);
  const [showAjusteModal, setShowAjusteModal] = useState(false);
  const [showEditarModal, setShowEditarModal] = useState(false);
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
  const [entradaData, setEntradaData] = useState({ cantidad: "", motivo: "" });
  const [ajusteData, setAjusteData] = useState({ cantidad_nueva: "", motivo: "" });
  const [editarData, setEditarData] = useState({ cantidad_minima: "", ubicacion: "" });
  const toast = useToast();
  const { user } = useAuth();

  const canEdit = user?.rol === "BODEGA" || user?.rol === "ADMIN";

  useEffect(() => {
    loadStock();
  }, []);

  const loadStock = async () => {
    try {
      setLoading(true);
      const response = await fetch(ENDPOINTS.INVENTORY_STOCK, {
        credentials: "include",
      });
      
      if (!response.ok) {
        throw new Error("Error al cargar stock");
      }
      
      const data = await response.json();
      setStocks(Array.isArray(data) ? data : data.results || []);
    } catch (error) {
      console.error("Error loading stock:", error);
      toast.error("Error al cargar stock");
    } finally {
      setLoading(false);
    }
  };

  const handleEntrada = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedStock) return;

    try {
      const response = await fetch(ENDPOINTS.INVENTORY_STOCK_ENTRADA(selectedStock.id), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          cantidad: parseInt(entradaData.cantidad),
          motivo: entradaData.motivo || "Entrada de stock",
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Error al registrar entrada");
      }

      toast.success("Entrada de stock registrada");
      setShowEntradaModal(false);
      setEntradaData({ cantidad: "", motivo: "" });
      setSelectedStock(null);
      loadStock();
    } catch (error: any) {
      toast.error(error.message || "Error al registrar entrada");
    }
  };

  const handleAjuste = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedStock) return;

    try {
      const response = await fetch(ENDPOINTS.INVENTORY_STOCK_AJUSTAR(selectedStock.id), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          cantidad_nueva: parseInt(ajusteData.cantidad_nueva),
          motivo: ajusteData.motivo || "Ajuste de inventario",
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Error al ajustar stock");
      }

      toast.success("Stock ajustado correctamente");
      setShowAjusteModal(false);
      setAjusteData({ cantidad_nueva: "", motivo: "" });
      setSelectedStock(null);
      loadStock();
    } catch (error: any) {
      toast.error(error.message || "Error al ajustar stock");
    }
  };

  const openEntradaModal = (stock: Stock) => {
    setSelectedStock(stock);
    setEntradaData({ cantidad: "", motivo: "" });
    setShowEntradaModal(true);
  };

  const openAjusteModal = (stock: Stock) => {
    setSelectedStock(stock);
    setAjusteData({ cantidad_nueva: stock.cantidad_actual.toString(), motivo: "" });
    setShowAjusteModal(true);
  };

  const openEditarModal = (stock: Stock) => {
    setSelectedStock(stock);
    setEditarData({ 
      cantidad_minima: stock.cantidad_minima.toString(), 
      ubicacion: stock.ubicacion || "" 
    });
    setShowEditarModal(true);
  };

  const handleEditar = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedStock) return;

    try {
      const response = await fetch(ENDPOINTS.INVENTORY_STOCK_UPDATE(selectedStock.id), {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          cantidad_minima: parseInt(editarData.cantidad_minima) || 0,
          ubicacion: editarData.ubicacion || "",
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Error al actualizar stock");
      }

      toast.success("Stock actualizado correctamente");
      invalidateCache("INVENTORY");
      setShowEditarModal(false);
      setEditarData({ cantidad_minima: "", ubicacion: "" });
      setSelectedStock(null);
      loadStock();
    } catch (error: any) {
      toast.error(error.message || "Error al actualizar stock");
    }
  };

  const filteredStocks = stocks.filter(
    (s) =>
      s.repuesto_codigo.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.repuesto_nombre.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const stocksBajoMinimo = filteredStocks.filter((s) => s.necesita_reorden);

  // Datos para gráficos
  const datosStock = filteredStocks.map((s) => ({
    nombre: s.repuesto_codigo,
    actual: s.cantidad_actual,
    minimo: s.cantidad_minima,
    diferencia: s.cantidad_actual - s.cantidad_minima,
  })).slice(0, 10); // Top 10 para el gráfico

  const datosEstado = [
    { name: "Bajo Mínimo", value: stocksBajoMinimo.length, color: "#ef4444" },
    { name: "OK", value: filteredStocks.length - stocksBajoMinimo.length, color: "#10b981" },
  ];

  const COLORS = ['#ef4444', '#10b981', '#f59e0b', '#8b5cf6'];

  return (
    <RoleGuard allowedRoles={["BODEGA", "ADMIN"]}>
      <div className="p-6 max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Control de Stock
          </h1>
          {stocksBajoMinimo.length > 0 && (
            <div className="flex items-center gap-2 px-4 py-2 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 rounded-lg">
              <ExclamationTriangleIcon className="w-5 h-5" />
              <span className="font-medium">
                {stocksBajoMinimo.length} repuesto(s) bajo mínimo
              </span>
            </div>
          )}
        </div>

        {/* Buscador */}
        <div className="mb-6">
          <input
            type="text"
            placeholder="Buscar por código o nombre..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
          />
        </div>

        {/* Gráficos de Stock */}
        {filteredStocks.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Gráfico de Estado del Stock */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                Estado del Stock
              </h2>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={datosEstado}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value, percent }) => `${name}: ${value} (${(percent * 100).toFixed(0)}%)`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                    nameKey="name"
                  >
                    {datosEstado.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'rgba(255, 255, 255, 0.95)',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Gráfico de Stock Actual vs Mínimo (Top 10) */}
            {datosStock.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                  Stock Actual vs Mínimo (Top 10)
                </h2>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={datosStock}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-gray-300 dark:stroke-gray-600" />
                    <XAxis 
                      dataKey="nombre" 
                      className="text-gray-600 dark:text-gray-400"
                      tick={{ fill: 'currentColor' }}
                      angle={-45}
                      textAnchor="end"
                      height={100}
                    />
                    <YAxis 
                      className="text-gray-600 dark:text-gray-400"
                      tick={{ fill: 'currentColor' }}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px'
                      }}
                    />
                    <Legend />
                    <Bar 
                      dataKey="actual" 
                      fill="#003DA5"
                      name="Stock Actual"
                      radius={[8, 8, 0, 0]}
                    />
                    <Bar 
                      dataKey="minimo" 
                      fill="#ef4444"
                      name="Stock Mínimo"
                      radius={[8, 8, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        )}

        {/* Tabla de stock */}
        {loading ? (
          <div className="text-center py-12">Cargando...</div>
        ) : (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Código
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Repuesto
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Stock Actual
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Mínimo
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Ubicación
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Estado
                  </th>
                  {canEdit && (
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Acciones
                    </th>
                  )}
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {filteredStocks.map((stock) => (
                  <tr
                    key={stock.id}
                    className={`hover:bg-gray-50 dark:hover:bg-gray-700 ${
                      stock.necesita_reorden ? "bg-red-50 dark:bg-red-900/20" : ""
                    }`}
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                      {stock.repuesto_codigo}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                      {stock.repuesto_nombre}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className="font-medium text-gray-900 dark:text-white">
                        {stock.cantidad_actual}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                      {stock.cantidad_minima}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                      {stock.ubicacion || "-"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${
                          stock.necesita_reorden
                            ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                            : "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                        }`}
                      >
                        {stock.necesita_reorden ? "Bajo Mínimo" : "OK"}
                      </span>
                    </td>
                    {canEdit && (
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => openEntradaModal(stock)}
                            className="text-green-600 hover:text-green-900 dark:text-green-400 dark:hover:text-green-300"
                            title="Registrar entrada"
                          >
                            <ArrowUpIcon className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => openAjusteModal(stock)}
                            className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
                            title="Ajustar stock"
                          >
                            <AdjustmentsHorizontalIcon className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => openEditarModal(stock)}
                            className="text-purple-600 hover:text-purple-900 dark:text-purple-400 dark:hover:text-purple-300"
                            title="Editar mínimo y ubicación"
                          >
                            <PencilIcon className="w-5 h-5" />
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
            {filteredStocks.length === 0 && (
              <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                No se encontraron registros de stock
              </div>
            )}
          </div>
        )}

        {/* Modal de editar stock */}
        {showEditarModal && selectedStock && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
              <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                Editar Stock
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Repuesto: <strong>{selectedStock.repuesto_nombre}</strong> ({selectedStock.repuesto_codigo})
              </p>
              <form onSubmit={handleEditar} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Cantidad Mínima *
                  </label>
                  <input
                    type="number"
                    required
                    min="0"
                    value={editarData.cantidad_minima}
                    onChange={(e) =>
                      setEditarData({ ...editarData, cantidad_minima: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Nivel de reorden: cuando el stock llegue a este valor, se marcará como "bajo mínimo"
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Ubicación en Bodega
                  </label>
                  <input
                    type="text"
                    value={editarData.ubicacion}
                    onChange={(e) =>
                      setEditarData({ ...editarData, ubicacion: e.target.value })
                    }
                    placeholder="Ej: Estante A-3, Pasillo 2, etc."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  />
                </div>
                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowEditarModal(false);
                      setSelectedStock(null);
                      setEditarData({ cantidad_minima: "", ubicacion: "" });
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
                  >
                    Guardar Cambios
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal de entrada */}
        {showEntradaModal && selectedStock && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
              <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                Registrar Entrada de Stock
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Repuesto: <strong>{selectedStock.repuesto_nombre}</strong> ({selectedStock.repuesto_codigo})
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Stock actual: <strong>{selectedStock.cantidad_actual}</strong>
              </p>
              <form onSubmit={handleEntrada} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Cantidad *
                  </label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={entradaData.cantidad}
                    onChange={(e) =>
                      setEntradaData({ ...entradaData, cantidad: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Motivo
                  </label>
                  <textarea
                    value={entradaData.motivo}
                    onChange={(e) =>
                      setEntradaData({ ...entradaData, motivo: e.target.value })
                    }
                    rows={3}
                    placeholder="Ej: Compra, Devolución, Ajuste..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  />
                </div>
                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowEntradaModal(false);
                      setSelectedStock(null);
                      setEntradaData({ cantidad: "", motivo: "" });
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
                  >
                    Registrar Entrada
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal de ajuste */}
        {showAjusteModal && selectedStock && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
              <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                Ajustar Stock
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Repuesto: <strong>{selectedStock.repuesto_nombre}</strong> ({selectedStock.repuesto_codigo})
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Stock actual: <strong>{selectedStock.cantidad_actual}</strong>
              </p>
              <form onSubmit={handleAjuste} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Nueva Cantidad *
                  </label>
                  <input
                    type="number"
                    required
                    min="0"
                    value={ajusteData.cantidad_nueva}
                    onChange={(e) =>
                      setAjusteData({ ...ajusteData, cantidad_nueva: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Motivo del Ajuste *
                  </label>
                  <textarea
                    required
                    value={ajusteData.motivo}
                    onChange={(e) =>
                      setAjusteData({ ...ajusteData, motivo: e.target.value })
                    }
                    rows={3}
                    placeholder="Ej: Inventario físico, Pérdida, Error de registro..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  />
                </div>
                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowAjusteModal(false);
                      setSelectedStock(null);
                      setAjusteData({ cantidad_nueva: "", motivo: "" });
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                  >
                    Ajustar Stock
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

