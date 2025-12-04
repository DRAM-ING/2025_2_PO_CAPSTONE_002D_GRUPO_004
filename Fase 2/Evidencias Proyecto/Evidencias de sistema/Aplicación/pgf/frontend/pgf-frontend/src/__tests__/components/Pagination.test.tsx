import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import Pagination from '@/components/Pagination'

describe('Pagination Component', () => {
  it('no debe renderizar cuando totalPages es 1', () => {
    const { container } = render(
      <Pagination
        currentPage={1}
        totalPages={1}
        onPageChange={vi.fn()}
      />
    )
    expect(container.firstChild).toBeNull()
  })

  it('debe renderizar botones de navegación', () => {
    const onPageChange = vi.fn()
    render(
      <Pagination
        currentPage={2}
        totalPages={5}
        onPageChange={onPageChange}
      />
    )

    // Hay dos botones (móvil y desktop), usar getAllByText
    const prevButtons = screen.getAllByText('Anterior')
    const nextButtons = screen.getAllByText('Siguiente')
    expect(prevButtons.length).toBeGreaterThan(0)
    expect(nextButtons.length).toBeGreaterThan(0)
  })

  it('debe deshabilitar botón Anterior en la primera página', () => {
    const onPageChange = vi.fn()
    render(
      <Pagination
        currentPage={1}
        totalPages={5}
        onPageChange={onPageChange}
      />
    )

    // Buscar todos los botones y verificar que al menos uno esté deshabilitado
    const prevButtons = screen.getAllByText('Anterior')
    const disabledButtons = prevButtons.filter(btn => btn.closest('button')?.hasAttribute('disabled'))
    expect(disabledButtons.length).toBeGreaterThan(0)
  })

  it('debe deshabilitar botón Siguiente en la última página', () => {
    const onPageChange = vi.fn()
    render(
      <Pagination
        currentPage={5}
        totalPages={5}
        onPageChange={onPageChange}
      />
    )

    const nextButtons = screen.getAllByText('Siguiente')
    const disabledButtons = nextButtons.filter(btn => btn.closest('button')?.hasAttribute('disabled'))
    expect(disabledButtons.length).toBeGreaterThan(0)
  })

  it('debe llamar onPageChange al hacer clic en Siguiente', () => {
    const onPageChange = vi.fn()
    render(
      <Pagination
        currentPage={2}
        totalPages={5}
        onPageChange={onPageChange}
      />
    )

    // Hacer clic en el primer botón "Siguiente" (puede ser móvil o desktop)
    const nextButtons = screen.getAllByText('Siguiente')
    fireEvent.click(nextButtons[0].closest('button')!)
    expect(onPageChange).toHaveBeenCalledWith(3)
  })

  it('debe llamar onPageChange al hacer clic en Anterior', () => {
    const onPageChange = vi.fn()
    render(
      <Pagination
        currentPage={3}
        totalPages={5}
        onPageChange={onPageChange}
      />
    )

    const prevButtons = screen.getAllByText('Anterior')
    fireEvent.click(prevButtons[0].closest('button')!)
    expect(onPageChange).toHaveBeenCalledWith(2)
  })

  it('debe mostrar información de items cuando se proporciona', () => {
    render(
      <Pagination
        currentPage={2}
        totalPages={5}
        totalItems={50}
        itemsPerPage={10}
        onPageChange={vi.fn()}
      />
    )

    expect(screen.getByText(/Mostrando/)).toBeInTheDocument()
    expect(screen.getByText(/11/)).toBeInTheDocument()
    expect(screen.getByText(/20/)).toBeInTheDocument()
    expect(screen.getByText(/50/)).toBeInTheDocument()
  })

  it('debe renderizar números de página correctamente', () => {
    const onPageChange = vi.fn()
    render(
      <Pagination
        currentPage={3}
        totalPages={10}
        onPageChange={onPageChange}
      />
    )

    // Debe mostrar la página actual
    expect(screen.getByText('3')).toBeInTheDocument()
  })
})

