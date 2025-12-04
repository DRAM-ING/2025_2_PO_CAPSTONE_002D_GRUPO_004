import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import RoleGate from '@/components/RoleGate'
import { useAuth } from '@/store/auth'

// Mock del store de auth
vi.mock('@/store/auth', () => ({
  useAuth: vi.fn(),
}))

describe('RoleGate Component', () => {
  it('debe renderizar children cuando el usuario tiene el rol permitido', () => {
    ;(useAuth as any).mockReturnValue({
      hasRole: (roles: string[]) => roles.includes('ADMIN'),
    })

    render(
      <RoleGate allow={['ADMIN']}>
        <div>Contenido protegido</div>
      </RoleGate>
    )

    expect(screen.getByText('Contenido protegido')).toBeInTheDocument()
  })

  it('debe renderizar fallback cuando el usuario no tiene el rol permitido', () => {
    ;(useAuth as any).mockReturnValue({
      hasRole: () => false,
    })

    render(
      <RoleGate allow={['ADMIN']} fallback={<div>Sin acceso</div>}>
        <div>Contenido protegido</div>
      </RoleGate>
    )

    expect(screen.getByText('Sin acceso')).toBeInTheDocument()
    expect(screen.queryByText('Contenido protegido')).not.toBeInTheDocument()
  })

  it('debe renderizar children cuando allow está vacío (solo requiere autenticación)', () => {
    ;(useAuth as any).mockReturnValue({
      hasRole: () => false,
    })

    render(
      <RoleGate allow={[]}>
        <div>Contenido público</div>
      </RoleGate>
    )

    expect(screen.getByText('Contenido público')).toBeInTheDocument()
  })

  it('debe renderizar children cuando el usuario tiene uno de los roles permitidos', () => {
    ;(useAuth as any).mockReturnValue({
      hasRole: (roles: string[]) => roles.includes('SUPERVISOR'),
    })

    render(
      <RoleGate allow={['ADMIN', 'SUPERVISOR']}>
        <div>Contenido para admin o supervisor</div>
      </RoleGate>
    )

    expect(screen.getByText('Contenido para admin o supervisor')).toBeInTheDocument()
  })
})

