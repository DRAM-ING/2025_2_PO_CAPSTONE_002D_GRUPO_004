'use client'
import { useState } from 'react'
import { apiPost } from '@/lib/http'


export function EvidenceUploader({ otId }: { otId: string }) {
const [busy, setBusy] = useState(false)
const [msg, setMsg] = useState('')


async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
const f = e.target.files?.[0]
if (!f) return
setBusy(true)
try {
const pres = await apiPost<{ upload: any; file_url: string }>(`/api/v1/work/evidencias/presigned/`, {
ot: otId,
filename: f.name,
content_type: f.type || 'application/octet-stream',
})
const form = new FormData()
Object.entries(pres.upload.fields).forEach(([k, v]) => form.append(k, String(v)))
form.append('file', f)
const up = await fetch(pres.upload.url, { method: 'POST', body: form })
if (!up.ok) throw new Error('upload failed')
setMsg('Evidencia subida ✔')
} catch (err: any) {
setMsg(err.message || 'Error subiendo evidencia')
} finally {
setBusy(false)
e.target.value = ''
}
}


return (
<div className="flex items-center gap-3">
<input disabled={busy} type="file" onChange={onFile} className="file:mr-2 file:rounded-lg file:border file:border-neutral-700 file:bg-neutral-900 file:px-3 file:py-1" />
{busy && <span className="text-sm text-neutral-400">Subiendo…</span>}
{msg && <span className="text-sm text-neutral-300">{msg}</span>}
</div>
)
}