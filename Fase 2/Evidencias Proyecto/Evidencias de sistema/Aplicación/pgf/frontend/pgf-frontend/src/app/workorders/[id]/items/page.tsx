"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ENDPOINTS } from "@/lib/constants";
import { withSession } from "@/lib/api.client";
import Link from "next/link";

export default function ItemsPage() {
  const params = useParams();
  const otId = params.id as string;
  const [rows, setRows] = useState<any[]>([]);

  const load = async () => {
    const r = await fetch(
      `${ENDPOINTS.WORK_ITEMS}?ot=${otId}`,
      withSession()
    );
    const j = await r.json();
    setRows(j.results ?? j);
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Items de OT</h1>

        <Link
          href={`/workorders/${otId}/items/create`}
          className="px-4 py-2 bg-blue-600 text-white rounded"
        >
          + Agregar Ítem
        </Link>
      </div>

      <table className="w-full border-collapse">
        <thead className="bg-gray-200">
          <tr>
            <th className="p-2">Tipo</th>
            <th className="p-2">Descripción</th>
            <th className="p-2">Cantidad</th>
            <th className="p-2">Costo Unitario</th>
            <th className="p-2">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((i) => (
            <tr key={i.id} className="border-b">
              <td className="p-2">{i.tipo}</td>
              <td className="p-2">{i.descripcion}</td>
              <td className="p-2">{i.cantidad}</td>
              <td className="p-2">$ {i.costo_unitario}</td>

              <td className="p-2 flex space-x-3">
                <Link
                  href={`/workorders/${otId}/items/${i.id}/edit`}
                  className="text-blue-600 hover:underline"
                >
                  Editar
                </Link>

                <Link
                  href={`/workorders/${otId}/items/${i.id}/delete`}
                  className="text-red-600 hover:underline"
                >
                  Eliminar
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
