"use client";
import { useState } from "react";
import { api } from "@/lib/api.server";
import { ENDPOINTS } from "@/lib/constants";

export default function NewVehicle() {
  const [plate, setPlate] = useState("");
  const [model, setModel] = useState("");

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    await api.post(ENDPOINTS.vehicles, { plate, model });
    window.location.href = "/vehicles";
  };

  return (
    <form onSubmit={save} className="max-w-md space-y-3">
      <h1 className="text-2xl font-semibold">Nuevo vehículo</h1>
      <input className="w-full border rounded p-2" placeholder="Patente" value={plate} onChange={e=>setPlate(e.target.value)} />
      <input className="w-full border rounded p-2" placeholder="Modelo" value={model} onChange={e=>setModel(e.target.value)} />
      <button className="rounded bg-black text-white px-3 py-2">Guardar</button>
    </form>
  );
}
