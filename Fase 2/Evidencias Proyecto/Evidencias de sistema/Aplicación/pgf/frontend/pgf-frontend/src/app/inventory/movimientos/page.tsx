"use client";

import { useEffect, useState } from "react";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";
import RoleGuard from "@/components/RoleGuard";
import { ENDPOINTS } from "@/lib/constants";
import { MagnifyingGlassIcon } from "@heroicons/react/24/outline";

interface Movimiento {
  id: string;
  repuesto: string;
  repuesto_codigo: string;
  repuesto_nombre: string;
  tipo: "ENTRADA" | "SALIDA" | "AJUSTE" | "DEVOLUCION";
  cantidad: number;
  cantidad_anterior: number;
  cantidad_nueva: number;
  motivo: string;
  usuario: string;
  usuario_nombre: string;
  fecha: string;
  ot_id?: string;
  vehiculo_patente?: string;
}

export default function MovimientosPage() {
  const [movimientos, setMovimientos] = useState<Movimiento[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filtroTipo, setFiltroTipo] = useState<string>("");
  const toast = useToast();

  useEffect(() => {
    loadMovimientos();
  }, [filtroTipo]);

  const loadMovimientos = async () => {
    try {
      setLoading(true);
      let url = ENDPOINTS.INVENTORY_MOVIMIENTOS;
      const params = new URLSearchParams();
      
      if (filtroTipo) {
        params.append("tipo", filtroTipo);
      }
      
      if (params.toString()) {
        url += `?${params.toString()}`;
      }

      const response = await fetch(url, {
        credentials: "include",
      });
      
      if (!response.ok) {
        throw new Error("Error al cargar movimientos");
      }
      
      const data = await response.json();
      setMovimientos(Array.isArray(data) ? data : data.results || []);
    } catch (error) {
      console.error("Error loading movimientos:", error);
      toast.error("Error al cargar movimientos");
    } finally {
      setLoading(false);
    }
  };

  const getTipoColor = (tipo: string) => {
    switch (tipo) {
      case "ENTRADA":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "SALIDA":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
      case "AJUSTE":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
      case "DEVOLUCION":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300";
    }
  };

  const getTipoLabel = (tipo: string) => {
    switch (tipo) {
      case "ENTRADA":
        return "Entrada";
      case "SALIDA":
        return "Salida";
      case "AJUSTE":
        return "Ajuste";
      case "DEVOLUCION":
        return "Devolución";
      default:
        return tipo;
    }
  };

  const filteredMovimientos = movimientos.filter(
    (m) =>
      m.repuesto_codigo.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.repuesto_nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (m.vehiculo_patente && m.vehiculo_patente.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <RoleGuard allowedRoles={["BODEGA", "ADMIN"]}>
      <div className="p-6 max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Movimientos de Stock
          </h1>
        </div>

        {/* Filtros */}
        <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar por código, nombre o patente..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
            />
          </div>
          <div>
            <select
              value={filtroTipo}
              onChange={(e) => setFiltroTipo(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
            >
              <option value="">Todos los tipos</option>
              <option value="ENTRADA">Entrada</option>
              <option value="SALIDA">Salida</option>
              <option value="AJUSTE">Ajuste</option>
              <option value="DEVOLUCION">Devolución</option>
            </select>
          </div>
        </div>

        {/* Tabla de movimientos */}
        {loading ? (
          <div className="text-center py-12">Cargando...</div>
        ) : (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Fecha
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Repuesto
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Tipo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Cantidad
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Stock Anterior
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Stock Nuevo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Usuario
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Relación
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Motivo
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {filteredMovimientos.map((movimiento) => (
                    <tr key={movimiento.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                        {new Date(movimiento.fecha).toLocaleString("es-CL")}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">
                            {movimiento.repuesto_codigo}
                          </div>
                          <div className="text-gray-500 dark:text-gray-400 text-xs">
                            {movimiento.repuesto_nombre}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-medium ${getTipoColor(
                            movimiento.tipo
                          )}`}
                        >
                          {getTipoLabel(movimiento.tipo)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                        {movimiento.cantidad}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                        {movimiento.cantidad_anterior}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                        {movimiento.cantidad_nueva}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                        {movimiento.usuario_nombre}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                        {movimiento.ot_id && (
                          <div>
                            <div className="text-xs">OT: {movimiento.ot_id.substring(0, 8)}...</div>
                            {movimiento.vehiculo_patente && (
                              <div className="text-xs">Veh: {movimiento.vehiculo_patente}</div>
                            )}
                          </div>
                        )}
                        {!movimiento.ot_id && "-"}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-300 max-w-xs truncate">
                        {movimiento.motivo || "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {filteredMovimientos.length === 0 && (
              <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                No se encontraron movimientos
              </div>
            )}
          </div>
        )}
      </div>
    </RoleGuard>
  );
}

