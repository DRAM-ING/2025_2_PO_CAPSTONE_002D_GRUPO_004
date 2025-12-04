"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import RoleGuard from "@/components/RoleGuard";
import Pagination from "@/components/Pagination";
import { useDataRefresh } from "@/lib/dataRefresh";

const ROLES = [
  { value: "", label: "Todos los roles" },
  { value: "ADMIN", label: "Administrador" },
  { value: "GUARDIA", label: "Guardia de Portería" },
  { value: "CHOFER", label: "Chofer" },
  { value: "MECANICO", label: "Mecánico" },
  { value: "JEFE_TALLER", label: "Jefe de Taller" },
  { value: "SUPERVISOR", label: "Supervisor Zonal" },
  { value: "COORDINADOR_ZONA", label: "Coordinador de Zona" },
  { value: "EJECUTIVO", label: "Ejecutivo" },
  { value: "SPONSOR", label: "Sponsor" },
  { value: "ADMINISTRATIVO_TALLER", label: "Administrativo de Taller" },
  { value: "BODEGA", label: "Bodega / Encargado de Repuestos" },
];

export default function UsersPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [rolFiltro, setRolFiltro] = useState<string>("");
  const itemsPerPage = 20;

  async function load(page: number = 1) {
    setLoading(true);
    try {
      // Construir URL con filtros
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: itemsPerPage.toString(),
      });
      
      if (rolFiltro && rolFiltro.trim() !== "") {
        params.append("rol", rolFiltro);
      }
      
      const r = await fetch(`/api/proxy/users/?${params.toString()}`, {
        credentials: "include",
      });
      
      if (!r.ok) {
        if (r.status === 401) {
          console.warn("No autorizado para ver usuarios");
          setRows([]);
          return;
        }
        throw new Error(`HTTP ${r.status}`);
      }
      
      const text = await r.text();
      if (!text || text.trim() === "") {
        setRows([]);
        return;
      }
      
      const j = JSON.parse(text);
      setRows(j.results ?? j ?? []);
      setTotalPages(Math.ceil((j.count || j.results?.length || 0) / itemsPerPage));
      setTotalItems(j.count || j.results?.length || 0);
    } catch (e) {
      // Solo loguear errores, no mostrar alertas si es por falta de datos
      if (e instanceof Error && e.message.includes("HTTP 5")) {
        console.error("Error crítico al cargar usuarios", e);
      } else {
        console.warn("Sin datos disponibles o error menor al cargar usuarios", e);
      }
      setRows([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // Resetear a página 1 cuando cambia el filtro
    if (rolFiltro !== undefined) {
      setCurrentPage(1);
    }
  }, [rolFiltro]);

  useEffect(() => {
    load(currentPage);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, rolFiltro]);

  // Escuchar eventos de refresh de datos
  useDataRefresh("USERS", () => load(currentPage));

  return (
    <RoleGuard allow={["ADMIN", "SUPERVISOR"]}>
      <div className="p-8 max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold">Usuarios</h1>
          <Link
            href="/users/create"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
          >
            + Nuevo Usuario
          </Link>
        </div>

        {/* Filtros */}
        <div className="mb-6 flex items-center gap-4">
          <div className="flex-1">
            <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
              Filtrar por Rol
            </label>
            <select
              value={rolFiltro}
              onChange={(e) => {
                setRolFiltro(e.target.value);
                setCurrentPage(1); // Resetear a la primera página al cambiar el filtro
              }}
              className="w-full md:w-64 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {ROLES.map((rol) => (
                <option key={rol.value} value={rol.value}>
                  {rol.label}
                </option>
              ))}
            </select>
          </div>
          {rolFiltro && (
            <div className="flex items-end">
              <button
                onClick={() => {
                  setRolFiltro("");
                  setCurrentPage(1);
                }}
                className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium text-sm"
              >
                Limpiar Filtro
              </button>
            </div>
          )}
        </div>

      {loading && <p className="text-gray-500 dark:text-gray-400">Cargando...</p>}
      {!loading && rows.length === 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 text-center">
          <p className="text-gray-500 dark:text-gray-400">
            {rolFiltro
              ? `No hay usuarios con el rol "${ROLES.find((r) => r.value === rolFiltro)?.label || rolFiltro}" registrados.`
              : "No hay usuarios registrados."}
          </p>
          {rolFiltro && (
            <button
              onClick={() => {
                setRolFiltro("");
                setCurrentPage(1);
              }}
              className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium text-sm"
            >
              Ver todos los usuarios
            </button>
          )}
        </div>
      )}

      {!loading && rows.length > 0 && (
        <div className="overflow-x-auto border rounded-lg">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-gray-100 dark:bg-gray-700 border-b">
              <tr>
                <th className="p-3 text-left">ID</th>
                <th className="p-3 text-left">Nombre</th>
                <th className="p-3 text-left">Usuario</th>
                <th className="p-3 text-left">Email</th>
                <th className="p-3 text-left">RUT</th>
                <th className="p-3 text-left">Rol</th>
                <th className="p-3 text-left">Acciones</th>
              </tr>
            </thead>

            <tbody>
              {rows.map((u) => (
                <tr key={u.id} className="border-b hover:bg-gray-50 dark:hover:bg-gray-700 transition">
                  <td className="p-3">{u.id}</td>
                  <td className="p-3">{u.first_name} {u.last_name}</td>
                  <td className="p-3">{u.username}</td>
                  <td className="p-3">{u.email}</td>
                  <td className="p-3">{u.rut || "-"}</td>
                  <td className="p-3">
                    <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded text-xs font-medium">
                      {u.rol}
                    </span>
                  </td>
                  <td className="p-3">
                    <div className="flex gap-2">
                      <Link
                        href={`/users/${u.id}/edit`}
                        className="text-blue-600 dark:text-blue-400 hover:underline text-sm"
                      >
                        Editar
                      </Link>
                      {!u.is_permanent ? (
                        <Link
                          href={`/users/${u.id}/delete`}
                          className="text-red-600 dark:text-red-400 hover:underline text-sm"
                        >
                          Eliminar
                        </Link>
                      ) : (
                        <span className="text-gray-400 dark:text-gray-500 text-sm cursor-not-allowed" title="Usuario permanente - no se puede eliminar">
                          Eliminar
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
            totalItems={totalItems}
            itemsPerPage={itemsPerPage}
          />
        </div>
      )}
      </div>
    </RoleGuard>
  );
}
