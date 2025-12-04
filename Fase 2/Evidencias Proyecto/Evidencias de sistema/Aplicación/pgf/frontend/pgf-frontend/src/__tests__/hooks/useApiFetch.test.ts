/**
 * Tests para el hook useApiFetch
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useApiFetch } from '@/hooks/useApiFetch'

// Mock de useToast
vi.mock('@/components/ToastContainer', () => ({
  useToast: () => ({
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  }),
}))

// Mock de useRouter
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
  }),
}))

// Mock de useAuth - debe incluir todos los métodos que usa RoleGuard
vi.mock('@/store/auth', () => ({
  useAuth: () => ({
    user: { id: '1', username: 'test', rol: 'ADMIN' },
    setUser: vi.fn(),
    allowed: vi.fn(() => true),
    hasRole: vi.fn(() => true),
    isLogged: () => true,  // Función que retorna boolean
    refreshMe: vi.fn(() => Promise.resolve()),
  }),
}))

// Mock de fetch
global.fetch = vi.fn()

describe('useApiFetch', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('debe inicializar con valores por defecto', () => {
    const { result } = renderHook(() => useApiFetch())
    
    expect(result.current.data).toBeNull()
    expect(result.current.error).toBeNull()
    expect(result.current.loading).toBe(false)
    expect(typeof result.current.fetchData).toBe('function')
  })

  it('debe manejar petición exitosa', async () => {
    const mockData = { id: '1', name: 'Test' }
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify(mockData),
    })

    const { result } = renderHook(() => useApiFetch())
    
    await result.current.fetchData('/api/test')
    
    await waitFor(() => {
      expect(result.current.data).toEqual(mockData)
      expect(result.current.error).toBeNull()
      expect(result.current.loading).toBe(false)
    })
  })

  it('debe manejar errores HTTP', async () => {
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 400,
      text: async () => JSON.stringify({ detail: 'Error de validación' }),
    })

    const { result } = renderHook(() => useApiFetch())
    
    await result.current.fetchData('/api/test', { showErrorToast: true })
    
    await waitFor(() => {
      expect(result.current.error).toBe('Error de validación')
      expect(result.current.data).toBeNull()
    })
  })

  it('debe manejar respuestas HTML (errores del servidor)', async () => {
    const htmlResponse = '<!DOCTYPE html><html><head><title>Error 500</title></head></html>'
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 500,
      text: async () => htmlResponse,
    })

    const { result } = renderHook(() => useApiFetch())
    
    await result.current.fetchData('/api/test')
    
    await waitFor(() => {
      expect(result.current.error).toBeTruthy()
      expect(result.current.data).toBeNull()
    })
  })

  it('debe manejar errores de red', async () => {
    ;(global.fetch as any).mockRejectedValueOnce(new Error('Network error'))

    const { result } = renderHook(() => useApiFetch())
    
    await result.current.fetchData('/api/test')
    
    await waitFor(() => {
      expect(result.current.error).toBe('Network error')
      expect(result.current.data).toBeNull()
    })
  })
})

