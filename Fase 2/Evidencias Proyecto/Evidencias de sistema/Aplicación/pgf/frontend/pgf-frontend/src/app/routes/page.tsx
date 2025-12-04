"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api.server";
import { ENDPOINTS } from "@/lib/constants";

type RouteState = { vehicle:string; state:"EN_TRANSITO"|"DETENIDO"|"ENTREGADO"; updated_at:string };

export default function RoutesBoard() {
  const [rows, setRows] = useState<RouteState[]>([]);
  useEffect(()=>{ api.get(ENDPOINTS.routes).then(({data})=>setRows(data)); },[]);
  const badge = (s:RouteState["state"]) => ({
    EN_TRANSITO: "bg-blue-100 text-blue-700",
    DETENIDO: "bg-yellow-100 text-yellow-700",
    ENTREGADO: "bg-green-100 text-green-700",
  }[s] || "bg-gray-100 text-gray-700");

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Estado de Ruta</h1>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {rows.map((r,i)=>(
          <div key={i} className="border rounded-xl p-4">
            <div className="font-semibold">{r.vehicle}</div>
            <div className={`mt-2 inline-block text-xs px-2 py-1 rounded ${badge(r.state)}`}>{r.state}</div>
            <div className="text-xs text-gray-500 mt-2">Actualizado: {new Date(r.updated_at).toLocaleString()}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
