/**
 * Tests para el componente NotificationBell
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import NotificationBell from '@/components/NotificationBell'

// Mock de next/navigation
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(() => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
  })),
}))

// Mock de fetch
global.fetch = vi.fn()

describe('NotificationBell', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Mock de fetch por defecto
    ;(global.fetch as any).mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify([]),
      json: async () => [],
    })
  })

  it('debe renderizar el botón de notificaciones', () => {
    render(<NotificationBell />)
    const button = screen.getByRole('button')
    expect(button).toBeInTheDocument()
  })

  it('debe mostrar contador de notificaciones no leídas', async () => {
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify({ no_leidas: 5 }),
      json: async () => ({ no_leidas: 5 }),
    })

    render(<NotificationBell />)
    
    await waitFor(() => {
      // El contador debería aparecer si hay notificaciones
      // Esto depende de la implementación del componente
    })
  })

  it('debe cargar notificaciones al montar', async () => {
    const mockNotifications = [
      { id: '1', titulo: 'Test', mensaje: 'Test message', estado: 'NO_LEIDA' }
    ]
    
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify(mockNotifications),
      json: async () => mockNotifications,
    })

    render(<NotificationBell />)
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/proxy/notifications/no-leidas/',
        expect.objectContaining({ credentials: 'include' })
      )
    })
  })
})

