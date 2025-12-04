export function WorkOrderStatusBadge({ estado }: { estado: string }) {
const map: Record<string, string> = {
ABIERTA: 'bg-blue-500/15 text-blue-300',
EN_EJECUCION: 'bg-amber-500/15 text-amber-300',
EN_QA: 'bg-cyan-500/15 text-cyan-300',
CERRADA: 'bg-emerald-500/15 text-emerald-300',
ANULADA: 'bg-rose-500/15 text-rose-300',
}
return <span className={`px-2 py-1 text-xs rounded-full ${map[estado] || 'bg-neutral-700 text-neutral-200'}`}>{estado}</span>
}