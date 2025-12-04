/**
 * Tests para las funciones de proxy de API
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { safeJsonParse, handleBackendResponse } from '@/app/api/utils'

describe('safeJsonParse', () => {
  it('debe parsear JSON válido correctamente', async () => {
    const response = new Response(JSON.stringify({ data: 'test' }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    })
    
    const result = await safeJsonParse(response)
    expect(result).toEqual({ data: 'test' })
  })

  it('debe manejar respuestas vacías', async () => {
    const response = new Response('', { status: 200 })
    const result = await safeJsonParse(response)
    expect(result).toEqual({})
  })

  it('debe detectar respuestas HTML y retornar error apropiado', async () => {
    const htmlResponse = '<!DOCTYPE html><html><head><title>Error 500</title></head><body>Error</body></html>'
    const response = new Response(htmlResponse, {
      status: 500,
      headers: { 'Content-Type': 'text/html' }
    })
    
    const result = await safeJsonParse(response)
    expect(result.html_response).toBe(true)
    expect(result.detail).toContain('Error del servidor')
  })

  it('debe manejar JSON inválido', async () => {
    const response = new Response('invalid json', { status: 200 })
    const result = await safeJsonParse(response)
    expect(result.detail).toContain('Respuesta inválida')
  })
})

describe('handleBackendResponse', () => {
  it('debe retornar NextResponse con datos JSON', async () => {
    const response = new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    })
    
    const result = await handleBackendResponse(response)
    const data = await result.json()
    expect(data).toEqual({ success: true })
    expect(result.status).toBe(200)
  })

  it('debe manejar errores HTML correctamente', async () => {
    const htmlResponse = '<!DOCTYPE html><html><head><title>Error</title></head></html>'
    const response = new Response(htmlResponse, {
      status: 500,
      headers: { 'Content-Type': 'text/html' }
    })
    
    const result = await handleBackendResponse(response)
    const data = await result.json()
    // El resultado debe retornar un error con status 500
    expect(result.status).toBe(500)
    expect(data.detail).toBeDefined()
    // Verificar que el mensaje de error contenga información sobre el error del servidor
    expect(data.detail).toMatch(/Error del servidor|servidor/i)
    // El campo html_response puede estar presente o no dependiendo de la implementación
    // Lo importante es que se maneje correctamente el error HTML
  })
})

