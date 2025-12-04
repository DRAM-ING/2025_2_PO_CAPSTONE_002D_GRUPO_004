/**
 * Tests para la página de creación de órdenes de trabajo
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import CreateWorkOrder from '@/app/workorders/create/page'

// Mock de next/navigation
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(() => ({
    push: vi.fn(),
    back: vi.fn(),
  })),
}))

// Mock de fetch
global.fetch = vi.fn()

// Mock de useAuth - debe incluir todos los métodos que usa RoleGuard
vi.mock('@/store/auth', () => ({
  useAuth: () => ({
    user: { id: '1', username: 'test', rol: 'JEFE_TALLER' },
    setUser: vi.fn(),
    allowed: vi.fn(() => true),
    hasRole: (roles: string | string[]) => {
      const roleList = Array.isArray(roles) ? roles : [roles];
      return roleList.includes('JEFE_TALLER');
    },
    isLogged: () => true,  // Función que retorna boolean
    refreshMe: vi.fn(() => Promise.resolve()),
  }),
}))

// Mock de useToast
const mockSuccess = vi.fn()
const mockError = vi.fn()
const mockInfo = vi.fn()

vi.mock('@/components/ToastContainer', () => ({
  useToast: () => ({
    success: mockSuccess,
    error: mockError,
    info: mockInfo,
  }),
}))

describe('CreateWorkOrder', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockSuccess.mockClear()
    mockError.mockClear()
    mockInfo.mockClear()
    
    // Mock de fetch para cargar vehículos, usuarios y repuestos
    ;(global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          results: [
            { id: '1', patente: 'ABC123', marca: 'Toyota', modelo: 'Hilux' }
          ],
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          results: [
            { id: '7', username: 'jefe_taller', get_full_name: 'Jefe Taller', rol: 'JEFE_TALLER', is_active: true }
          ],
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          results: [
            { id: 'repuesto-1', nombre: 'Repuesto Test', codigo: 'R001', activo: true }
          ],
        }),
      })
  })

  it('debe renderizar el formulario de creación', async () => {
    render(<CreateWorkOrder />)
    
    await waitFor(() => {
      // Buscar el título (h1) en lugar del botón
      const title = screen.getByRole('heading', { name: /crear orden de trabajo/i })
      expect(title).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('debe validar campos obligatorios', async () => {
    render(<CreateWorkOrder />)
    
    await waitFor(() => {
      // Buscar el botón de submit por su rol y nombre
      const submitButton = screen.getByRole('button', { name: /crear orden de trabajo/i })
      expect(submitButton).toBeInTheDocument()
    }, { timeout: 3000 })
    
    const submitButton = screen.getByRole('button', { name: /crear orden de trabajo/i })
    fireEvent.click(submitButton)

    // Debe mostrar error si falta vehículo o motivo
    await waitFor(() => {
      // Verificar que se muestra error de validación
      const errorMessages = screen.queryAllByText(/requerido|obligatorio|debe seleccionar/i)
      expect(errorMessages.length).toBeGreaterThan(0)
    }, { timeout: 3000 })
  })

  it('debe manejar errores del servidor correctamente', async () => {
    vi.clearAllMocks()
    
    // Mock de fetch para cargar vehículos
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        results: [
          { id: '1', patente: 'ABC123', marca: 'Toyota', modelo: 'Hilux' }
        ],
      }),
    })
    
    // Mock de fetch para cargar usuarios/responsables
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        results: [
          { id: '7', username: 'jefe_taller', get_full_name: 'Jefe Taller', rol: 'JEFE_TALLER', is_active: true }
        ],
      }),
    })
    
    // Mock de fetch para cargar repuestos
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        results: [
          { id: 'repuesto-1', nombre: 'Repuesto Test', codigo: 'R001', activo: true }
        ],
      }),
    })

    render(<CreateWorkOrder />)
    
    // Esperar a que el formulario esté cargado
    await waitFor(() => {
      const title = screen.getByRole('heading', { name: /crear orden de trabajo/i })
      expect(title).toBeInTheDocument()
    }, { timeout: 3000 })
    
    // El formulario tiene validación, así que primero necesitamos llenarlo
    // Buscar los campos por su valor o placeholder
    await waitFor(() => {
      // Verificar que los selects están cargados
      const selects = screen.getAllByRole('combobox')
      expect(selects.length).toBeGreaterThan(0)
    }, { timeout: 3000 })
    
    // Llenar el formulario con datos válidos usando los selects
    const selects = screen.getAllByRole('combobox')
    if (selects.length > 0) {
      // Primer select es vehículo
      fireEvent.change(selects[0], { target: { value: '1' } })
    }
    
    // Buscar el textarea de motivo
    const motivoTextarea = screen.getByPlaceholderText(/describe el motivo/i)
    fireEvent.change(motivoTextarea, { target: { value: 'Motivo de prueba' } })
    
    // Buscar el select de responsable (puede ser el segundo o tercer select)
    if (selects.length > 2) {
      fireEvent.change(selects[2], { target: { value: '7' } })
    }
    
    // Llenar el item con una descripción válida
    const descripcionInput = screen.getByPlaceholderText(/descripción del item/i)
    fireEvent.change(descripcionInput, { target: { value: 'Descripción válida' } })
    
    // Mock de error del servidor para el POST
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 400,
      text: async () => JSON.stringify({ detail: 'Error de validación' }),
      json: async () => ({ detail: 'Error de validación' }),
    })
    
    // Simular envío de formulario
    const submitButton = screen.getByRole('button', { name: /crear orden de trabajo/i })
    fireEvent.click(submitButton)

    // Debe manejar el error correctamente
    await waitFor(() => {
      // Verificar que se mostró el error
      expect(mockError).toHaveBeenCalled()
    }, { timeout: 5000 })
  })
})

