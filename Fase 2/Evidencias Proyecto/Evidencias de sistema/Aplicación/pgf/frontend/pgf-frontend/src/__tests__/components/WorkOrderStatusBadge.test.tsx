import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { WorkOrderStatusBadge } from '@/components/WorkOrderStatusBadge'

describe('WorkOrderStatusBadge', () => {
  it('debe mostrar estado ABIERTA con clase correcta', () => {
    render(<WorkOrderStatusBadge estado="ABIERTA" />)
    const badge = screen.getByText('ABIERTA')
    expect(badge).toBeInTheDocument()
    // Verificar que las clases estén presentes (pueden estar en cualquier orden)
    expect(badge.className).toMatch(/bg-blue-500\/15/)
    expect(badge.className).toMatch(/text-blue-300/)
  })

  it('debe mostrar estado EN_EJECUCION con clase correcta', () => {
    render(<WorkOrderStatusBadge estado="EN_EJECUCION" />)
    const badge = screen.getByText('EN_EJECUCION')
    expect(badge).toBeInTheDocument()
    expect(badge.className).toMatch(/bg-amber-500\/15/)
    expect(badge.className).toMatch(/text-amber-300/)
  })

  it('debe mostrar estado EN_QA con clase correcta', () => {
    render(<WorkOrderStatusBadge estado="EN_QA" />)
    const badge = screen.getByText('EN_QA')
    expect(badge).toBeInTheDocument()
    expect(badge.className).toMatch(/bg-cyan-500\/15/)
    expect(badge.className).toMatch(/text-cyan-300/)
  })

  it('debe mostrar estado CERRADA con clase correcta', () => {
    render(<WorkOrderStatusBadge estado="CERRADA" />)
    const badge = screen.getByText('CERRADA')
    expect(badge).toBeInTheDocument()
    expect(badge.className).toMatch(/bg-emerald-500\/15/)
    expect(badge.className).toMatch(/text-emerald-300/)
  })

  it('debe mostrar estado ANULADA con clase correcta', () => {
    render(<WorkOrderStatusBadge estado="ANULADA" />)
    const badge = screen.getByText('ANULADA')
    expect(badge).toBeInTheDocument()
    expect(badge.className).toMatch(/bg-rose-500\/15/)
    expect(badge.className).toMatch(/text-rose-300/)
  })

  it('debe usar clase por defecto para estado desconocido', () => {
    render(<WorkOrderStatusBadge estado="ESTADO_DESCONOCIDO" />)
    const badge = screen.getByText('ESTADO_DESCONOCIDO')
    expect(badge).toBeInTheDocument()
    expect(badge.className).toMatch(/bg-neutral-700/)
    expect(badge.className).toMatch(/text-neutral-200/)
  })

  it('debe tener clases comunes para todos los estados', () => {
    const { rerender } = render(<WorkOrderStatusBadge estado="ABIERTA" />)
    const badge = screen.getByText('ABIERTA')
    
    expect(badge.className).toContain('px-2')
    expect(badge.className).toContain('py-1')
    expect(badge.className).toContain('text-xs')
    expect(badge.className).toContain('rounded-full')
    
    rerender(<WorkOrderStatusBadge estado="CERRADA" />)
    const newBadge = screen.getByText('CERRADA')
    expect(newBadge.className).toContain('px-2')
    expect(newBadge.className).toContain('py-1')
    expect(newBadge.className).toContain('text-xs')
    expect(newBadge.className).toContain('rounded-full')
  })
})

