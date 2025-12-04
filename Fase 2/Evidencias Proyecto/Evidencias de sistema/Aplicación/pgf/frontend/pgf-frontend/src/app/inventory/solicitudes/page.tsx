"use client";

import { useEffect, useState } from "react";
import { useToast } from "@/components/ToastContainer";
import { useAuth } from "@/store/auth";
import RoleGuard from "@/components/RoleGuard";
import { ENDPOINTS } from "@/lib/constants";
import Link from "next/link";
import { invalidateCache } from "@/lib/dataRefresh";
import {
  CheckCircleIcon,
  XCircleIcon,
  TruckIcon,
  MagnifyingGlassIcon,
} from "@heroicons/react/24/outline";

interface Solicitud {
  id: string;
  ot: string;
  ot_id: string;
  ot_estado?: string;
  ot_vehiculo_patente?: string;
  ot_vehiculo_id?: string;
  ot_tipo?: string;
  ot_prioridad?: string;
  repuesto: string;
  repuesto_codigo: string;
  repuesto_nombre: string;
  cantidad_solicitada: number;
  cantidad_entregada: number;
  estado: "PENDIENTE" | "APROBADA" | "RECHAZADA" | "ENTREGADA" | "CANCELADA";
  motivo: string;
  solicitante: string;
  solicitante_nombre: string;
  aprobador_nombre?: string;
  entregador_nombre?: string;
  fecha_solicitud: string;
  fecha_aprobacion?: string;
  fecha_entrega?: string;
}

export default function SolicitudesPage() {
  const [solicitudes, setSolicitudes] = useState<Solicitud[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filtroEstado, setFiltroEstado] = useState<string>("");
  const [showAprobarModal, setShowAprobarModal] = useState(false);
  const [showRechazarModal, setShowRechazarModal] = useState(false);
  const [showEntregarModal, setShowEntregarModal] = useState(false);
  const [selectedSolicitud, setSelectedSolicitud] = useState<Solicitud | null>(null);
  const [rechazoMotivo, setRechazoMotivo] = useState("");
  const [cantidadEntregada, setCantidadEntregada] = useState("");
  const toast = useToast();
  const { user } = useAuth();

  const canApprove = user?.rol === "BODEGA" || user?.rol === "ADMIN" || user?.rol === "JEFE_TALLER" || user?.rol === "SUPERVISOR";
  const canDeliver = user?.rol === "BODEGA" || user?.rol === "ADMIN";

  useEffect(() => {
    loadSolicitudes();
  }, [filtroEstado]);

  const loadSolicitudes = async () => {
    try {
      setLoading(true);
      let url = ENDPOINTS.INVENTORY_SOLICITUDES;
      const params = new URLSearchParams();
      
      if (filtroEstado) {
        params.append("estado", filtroEstado);
      }
      
      if (params.toString()) {
        url += `?${params.toString()}`;
      }

      const response = await fetch(url, {
        credentials: "include",
      });
      
      if (!response.ok) {
        throw new Error("Error al cargar solicitudes");
      }
      
      const data = await response.json();
      setSolicitudes(Array.isArray(data) ? data : data.results || []);
    } catch (error) {
      console.error("Error loading solicitudes:", error);
      toast.error("Error al cargar solicitudes");
    } finally {
      setLoading(false);
    }
  };

  const handleAprobar = async () => {
    if (!selectedSolicitud) return;

    try {
      const response = await fetch(
        ENDPOINTS.INVENTORY_SOLICITUD_APROBAR(selectedSolicitud.id),
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({}),
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Error al aprobar solicitud");
      }

      toast.success("Solicitud aprobada");
      invalidateCache("INVENTORY");
      setShowAprobarModal(false);
      setSelectedSolicitud(null);
      loadSolicitudes();
    } catch (error: any) {
      toast.error(error.message || "Error al aprobar solicitud");
    }
  };

  const handleRechazar = async () => {
    if (!selectedSolicitud) return;

    try {
      const response = await fetch(
        ENDPOINTS.INVENTORY_SOLICITUD_RECHAZAR(selectedSolicitud.id),
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            motivo: rechazoMotivo || "Solicitud rechazada",
          }),
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Error al rechazar solicitud");
      }

      toast.success("Solicitud rechazada");
      invalidateCache("INVENTORY");
      setShowRechazarModal(false);
      setSelectedSolicitud(null);
      setRechazoMotivo("");
      loadSolicitudes();
    } catch (error: any) {
      toast.error(error.message || "Error al rechazar solicitud");
    }
  };

  const handleEntregar = async () => {
    if (!selectedSolicitud) return;

    try {
      const response = await fetch(
        ENDPOINTS.INVENTORY_SOLICITUD_ENTREGAR(selectedSolicitud.id),
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            cantidad_entregada: cantidadEntregada
              ? parseInt(cantidadEntregada)
              : selectedSolicitud.cantidad_solicitada,
          }),
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Error al entregar repuesto");
      }

      toast.success("Repuesto entregado");
      invalidateCache("INVENTORY");
      setShowEntregarModal(false);
      setSelectedSolicitud(null);
      setCantidadEntregada("");
      loadSolicitudes();
    } catch (error: any) {
      toast.error(error.message || "Error al entregar repuesto");
    }
  };

  const getEstadoColor = (estado: string) => {
    switch (estado) {
      case "PENDIENTE":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
      case "APROBADA":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
      case "RECHAZADA":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
      case "ENTREGADA":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "CANCELADA":
        return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300";
    }
  };

  const getEstadoLabel = (estado: string) => {
    switch (estado) {
      case "PENDIENTE":
        return "Pendiente";
      case "APROBADA":
        return "Aprobada";
      case "RECHAZADA":
        return "Rechazada";
      case "ENTREGADA":
        return "Entregada";
      case "CANCELADA":
        return "Cancelada";
      default:
        return estado;
    }
  };

  const filteredSolicitudes = solicitudes.filter(
    (s) =>
      s.repuesto_codigo.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.repuesto_nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.ot_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (s.ot_vehiculo_patente && s.ot_vehiculo_patente.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <RoleGuard allowedRoles={["BODEGA", "ADMIN", "JEFE_TALLER", "SUPERVISOR", "MECANICO"]}>
      <div className="p-6 max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Solicitudes de Repuestos
          </h1>
          {(user?.rol === "MECANICO" || user?.rol === "JEFE_TALLER" || user?.rol === "ADMIN") && (
            <Link
              href="/inventory/solicitudes/create"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
            >
              + Nueva Solicitud
            </Link>
          )}
        </div>

        {/* Filtros */}
        <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar por código, nombre o OT..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
            />
          </div>
          <div>
            <select
              value={filtroEstado}
              onChange={(e) => setFiltroEstado(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
            >
              <option value="">Todos los estados</option>
              <option value="PENDIENTE">Pendiente</option>
              <option value="APROBADA">Aprobada</option>
              <option value="RECHAZADA">Rechazada</option>
              <option value="ENTREGADA">Entregada</option>
              <option value="CANCELADA">Cancelada</option>
            </select>
          </div>
        </div>

        {/* Tabla de solicitudes */}
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
                      OT / Vehículo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Cantidad
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Estado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Solicitante
                    </th>
                    {canApprove && (
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Acciones
                      </th>
                    )}
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {filteredSolicitudes.map((solicitud) => (
                    <tr key={solicitud.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                        {new Date(solicitud.fecha_solicitud).toLocaleDateString("es-CL")}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">
                            {solicitud.repuesto_codigo}
                          </div>
                          <div className="text-gray-500 dark:text-gray-400 text-xs">
                            {solicitud.repuesto_nombre}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <div className="space-y-1">
                          <Link
                            href={`/workorders/${solicitud.ot_id}`}
                            className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300 font-medium block"
                          >
                            OT: {solicitud.ot_id.substring(0, 8)}...
                          </Link>
                          {solicitud.ot_vehiculo_patente && (
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              Vehículo: {solicitud.ot_vehiculo_patente}
                            </div>
                          )}
                          {solicitud.ot_estado && (
                            <div className="text-xs">
                              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                solicitud.ot_estado === "CERRADA" 
                                  ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                                  : solicitud.ot_estado === "EN_EJECUCION"
                                  ? "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                                  : solicitud.ot_estado === "EN_PAUSA"
                                  ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
                                  : "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300"
                              }`}>
                                {solicitud.ot_estado}
                              </span>
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                        <div>
                          <div>Solicitada: {solicitud.cantidad_solicitada}</div>
                          {solicitud.cantidad_entregada > 0 && (
                            <div className="text-xs text-green-600 dark:text-green-400">
                              Entregada: {solicitud.cantidad_entregada}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-medium ${getEstadoColor(
                            solicitud.estado
                          )}`}
                        >
                          {getEstadoLabel(solicitud.estado)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                        {solicitud.solicitante_nombre}
                      </td>
                      {canApprove && (
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex justify-end gap-2">
                            {solicitud.estado === "PENDIENTE" && (
                              <>
                                <button
                                  onClick={() => {
                                    setSelectedSolicitud(solicitud);
                                    setShowAprobarModal(true);
                                  }}
                                  className="text-green-600 hover:text-green-900 dark:text-green-400 dark:hover:text-green-300"
                                  title="Aprobar"
                                >
                                  <CheckCircleIcon className="w-5 h-5" />
                                </button>
                                <button
                                  onClick={() => {
                                    setSelectedSolicitud(solicitud);
                                    setRechazoMotivo("");
                                    setShowRechazarModal(true);
                                  }}
                                  className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                                  title="Rechazar"
                                >
                                  <XCircleIcon className="w-5 h-5" />
                                </button>
                              </>
                            )}
                            {solicitud.estado === "APROBADA" && canDeliver && (
                              <button
                                onClick={() => {
                                  setSelectedSolicitud(solicitud);
                                  setCantidadEntregada(solicitud.cantidad_solicitada.toString());
                                  setShowEntregarModal(true);
                                }}
                                className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
                                title="Entregar"
                              >
                                <TruckIcon className="w-5 h-5" />
                              </button>
                            )}
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {filteredSolicitudes.length === 0 && (
              <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                No se encontraron solicitudes
              </div>
            )}
          </div>
        )}

        {/* Modal Aprobar */}
        {showAprobarModal && selectedSolicitud && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
              <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                Aprobar Solicitud
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                ¿Desea aprobar la solicitud de <strong>{selectedSolicitud.cantidad_solicitada}</strong> unidades de{" "}
                <strong>{selectedSolicitud.repuesto_nombre}</strong> para la OT{" "}
                <strong>{selectedSolicitud.ot_id.substring(0, 8)}</strong>?
              </p>
              <div className="flex justify-end gap-3 pt-4">
                <button
                  onClick={() => {
                    setShowAprobarModal(false);
                    setSelectedSolicitud(null);
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleAprobar}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
                >
                  Aprobar
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal Rechazar */}
        {showRechazarModal && selectedSolicitud && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
              <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                Rechazar Solicitud
              </h2>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Motivo del Rechazo *
                </label>
                <textarea
                  required
                  value={rechazoMotivo}
                  onChange={(e) => setRechazoMotivo(e.target.value)}
                  rows={3}
                  placeholder="Ingrese el motivo del rechazo..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button
                  onClick={() => {
                    setShowRechazarModal(false);
                    setSelectedSolicitud(null);
                    setRechazoMotivo("");
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleRechazar}
                  disabled={!rechazoMotivo.trim()}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Rechazar
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal Entregar */}
        {showEntregarModal && selectedSolicitud && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
              <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                Entregar Repuesto
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Repuesto: <strong>{selectedSolicitud.repuesto_nombre}</strong>
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Cantidad solicitada: <strong>{selectedSolicitud.cantidad_solicitada}</strong>
              </p>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Cantidad a Entregar *
                </label>
                <input
                  type="number"
                  required
                  min="1"
                  max={selectedSolicitud.cantidad_solicitada}
                  value={cantidadEntregada}
                  onChange={(e) => setCantidadEntregada(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Máximo: {selectedSolicitud.cantidad_solicitada}
                </p>
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button
                  onClick={() => {
                    setShowEntregarModal(false);
                    setSelectedSolicitud(null);
                    setCantidadEntregada("");
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleEntregar}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  Entregar
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </RoleGuard>
  );
}

