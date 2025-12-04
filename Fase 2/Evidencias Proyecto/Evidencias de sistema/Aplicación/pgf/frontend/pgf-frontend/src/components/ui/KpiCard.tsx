'use client'
import { ReactNode } from 'react'


export function KpiCard({ title, value, hint, icon }: { title: string; value: ReactNode; hint?: string; icon?: ReactNode }) {
return (
<div className="rounded-2xl border border-neutral-800 p-4 shadow hover:shadow-lg transition">
<div className="flex items-center gap-3">
{icon && <div className="text-neutral-400">{icon}</div>}
<div className="text-sm text-neutral-400">{title}</div>
</div>
<div className="mt-2 text-3xl font-semibold tracking-tight">{value}</div>
{hint && <div className="mt-1 text-xs text-neutral-500">{hint}</div>}
</div>
)
}