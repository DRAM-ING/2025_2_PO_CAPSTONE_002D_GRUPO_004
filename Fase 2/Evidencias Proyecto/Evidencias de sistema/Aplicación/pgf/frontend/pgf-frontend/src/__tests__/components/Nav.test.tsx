import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import Nav from '@/components/Nav'
import { useAuth } from '@/store/auth'

// Mock del store de auth
vi.mock('@/store/auth', () => ({
  useAuth: vi.fn(),
}))

describe('Nav Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('debe renderizar enlaces cuando el usuario tiene permisos', () => {
    ;(useAuth as any).mockReturnValue({
      allowed: (section: string) => {
        const allowedSections = ['dashboard', 'vehicles', 'workorders']
        return allowedSections.includes(section)
      },
    })

    render(<Nav />)

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Vehículos')).toBeInTheDocument()
    expect(screen.getByText('OT')).toBeInTheDocument()
  })

  it('no debe renderizar enlaces cuando el usuario no tiene permisos', () => {
    ;(useAuth as any).mockReturnValue({
      allowed: () => false,
    })

    render(<Nav />)

    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument()
    expect(screen.queryByText('Vehículos')).not.toBeInTheDocument()
  })

  it('debe renderizar solo los enlaces permitidos', () => {
    ;(useAuth as any).mockReturnValue({
      allowed: (section: string) => section === 'dashboard',
    })

    render(<Nav />)

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.queryByText('Vehículos')).not.toBeInTheDocument()
    expect(screen.queryByText('OT')).not.toBeInTheDocument()
  })
})

