import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ConfirmDialog from '@/components/ConfirmDialog'

describe('ConfirmDialog Component', () => {
  const mockOnConfirm = vi.fn()
  const mockOnCancel = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('no debe renderizar cuando isOpen es false', () => {
    render(
      <ConfirmDialog
        isOpen={false}
        title="Confirmar acción"
        message="¿Estás seguro?"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    )

    expect(screen.queryByText('Confirmar acción')).not.toBeInTheDocument()
  })

  it('debe renderizar cuando isOpen es true', () => {
    render(
      <ConfirmDialog
        isOpen={true}
        title="Confirmar acción"
        message="¿Estás seguro?"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    )

    expect(screen.getByText('Confirmar acción')).toBeInTheDocument()
    expect(screen.getByText('¿Estás seguro?')).toBeInTheDocument()
  })

  it('debe llamar onConfirm al hacer clic en confirmar', () => {
    render(
      <ConfirmDialog
        isOpen={true}
        title="Confirmar acción"
        message="Mensaje"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    )

    // Buscar el botón por su texto, no el título
    const confirmButtons = screen.getAllByText('Confirmar')
    // El botón es el último (el primero es el título si coincide)
    const confirmButton = confirmButtons[confirmButtons.length - 1]
    fireEvent.click(confirmButton)

    expect(mockOnConfirm).toHaveBeenCalledTimes(1)
  })

  it('debe llamar onCancel al hacer clic en cancelar', () => {
    render(
      <ConfirmDialog
        isOpen={true}
        title="Confirmar"
        message="Mensaje"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    )

    const cancelButton = screen.getByText('Cancelar')
    fireEvent.click(cancelButton)

    expect(mockOnCancel).toHaveBeenCalledTimes(1)
  })

  it('debe usar textos personalizados', () => {
    render(
      <ConfirmDialog
        isOpen={true}
        title="Eliminar"
        message="¿Eliminar este item?"
        confirmText="Sí, eliminar"
        cancelText="No, mantener"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    )

    expect(screen.getByText('Sí, eliminar')).toBeInTheDocument()
    expect(screen.getByText('No, mantener')).toBeInTheDocument()
    expect(screen.getByText('Eliminar')).toBeInTheDocument()
    expect(screen.getByText('¿Eliminar este item?')).toBeInTheDocument()
  })
})

