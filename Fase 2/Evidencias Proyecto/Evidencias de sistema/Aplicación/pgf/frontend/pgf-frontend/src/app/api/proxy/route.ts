// location: frontend/pgf-frontend/src/app/api/proxy/route.ts
import { NextRequest, NextResponse } from 'next/server'


const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'


export async function GET(req: NextRequest) {
const path = req.nextUrl.searchParams.get('path') || '/'
const url = new URL(path, API_BASE)
const res = await fetch(url, { headers: { cookie: req.headers.get('cookie') || '' }, credentials: 'include' as any })
const headers = new Headers(res.headers)
const setCookie = res.headers.get('set-cookie')
if (setCookie) headers.set('set-cookie', setCookie)
return new NextResponse(res.body, { status: res.status, headers })
}


export async function POST(req: NextRequest) {
const path = req.nextUrl.searchParams.get('path') || '/'
const url = new URL(path, API_BASE)
const body = await req.text()
const res = await fetch(url, {
method: 'POST',
headers: { 'content-type': req.headers.get('content-type') || 'application/json', cookie: req.headers.get('cookie') || '' },
body,
credentials: 'include' as any,
})
const headers = new Headers(res.headers)
const setCookie = res.headers.get('set-cookie')
if (setCookie) headers.set('set-cookie', setCookie)
return new NextResponse(res.body, { status: res.status, headers })
}


export async function PATCH(req: NextRequest) {
const path = req.nextUrl.searchParams.get('path') || '/'
const url = new URL(path, API_BASE)
const body = await req.text()
const res = await fetch(url, {
method: 'PATCH', headers: { 'content-type': req.headers.get('content-type') || 'application/json', cookie: req.headers.get('cookie') || '' }, body,
})
return new NextResponse(res.body, { status: res.status, headers: res.headers })
}


export async function DELETE(req: NextRequest) {
const path = req.nextUrl.searchParams.get('path') || '/'
const url = new URL(path, API_BASE)
const res = await fetch(url, { method: 'DELETE', headers: { cookie: req.headers.get('cookie') || '' } })
return new NextResponse(res.body, { status: res.status, headers: res.headers })
}
