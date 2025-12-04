import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import ToastComponent, { Toast } from '@/components/Toast'

describe('Toast Component', () => {
  const mockOnClose = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('debe renderizar mensaje de éxito', () => {
    const toast: Toast = {
      id: '1',
      message: 'Operación exitosa',
      type: 'success',
    }

    render(<ToastComponent toast={toast} onClose={mockOnClose} />)
    expect(screen.getByText('Operación exitosa')).toBeInTheDocument()
  })

  it('debe renderizar mensaje de error', () => {
    const toast: Toast = {
      id: '2',
      message: 'Error al guardar',
      type: 'error',
    }

    render(<ToastComponent toast={toast} onClose={mockOnClose} />)
    expect(screen.getByText('Error al guardar')).toBeInTheDocument()
  })

  it('debe renderizar mensaje de advertencia', () => {
    const toast: Toast = {
      id: '3',
      message: 'Advertencia importante',
      type: 'warning',
    }

    render(<ToastComponent toast={toast} onClose={mockOnClose} />)
    expect(screen.getByText('Advertencia importante')).toBeInTheDocument()
  })

  it('debe renderizar mensaje de información', () => {
    const toast: Toast = {
      id: '4',
      message: 'Información útil',
      type: 'info',
    }

    render(<ToastComponent toast={toast} onClose={mockOnClose} />)
    expect(screen.getByText('Información útil')).toBeInTheDocument()
  })

  it('debe cerrar automáticamente después de 5 segundos por defecto', () => {
    const toast: Toast = {
      id: '5',
      message: 'Mensaje temporal',
      type: 'info',
    }

    render(<ToastComponent toast={toast} onClose={mockOnClose} />)

    // Avanzar timers y verificar que se llamó onClose
    vi.advanceTimersByTime(5000)
    
    expect(mockOnClose).toHaveBeenCalledWith('5')
  })

  it('debe cerrar automáticamente después de duración personalizada', () => {
    const toast: Toast = {
      id: '6',
      message: 'Mensaje con duración',
      type: 'info',
      duration: 3000,
    }

    render(<ToastComponent toast={toast} onClose={mockOnClose} />)

    vi.advanceTimersByTime(3000)

    expect(mockOnClose).toHaveBeenCalledWith('6')
  })

  it('no debe cerrar automáticamente si duration es 0', () => {
    const toast: Toast = {
      id: '7',
      message: 'Mensaje persistente',
      type: 'info',
      duration: 0,
    }

    render(<ToastComponent toast={toast} onClose={mockOnClose} />)

    // Avanzar tiempo pero no debería cerrarse
    vi.advanceTimersByTime(10000)

    // Verificar que no se llamó onClose
    expect(mockOnClose).not.toHaveBeenCalled()
  })

  it('debe cerrar al hacer clic en el botón de cerrar', () => {
    const toast: Toast = {
      id: '8',
      message: 'Mensaje cerrable',
      type: 'info',
    }

    render(<ToastComponent toast={toast} onClose={mockOnClose} />)

    const closeButton = screen.getByRole('button')
    closeButton.click()

    expect(mockOnClose).toHaveBeenCalledWith('8')
  })
})

