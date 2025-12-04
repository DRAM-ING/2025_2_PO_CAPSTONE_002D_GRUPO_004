/**
 * Tests para el componente ConditionalLayout
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { usePathname } from 'next/navigation';
import ConditionalLayout from '@/components/ConditionalLayout';

// Mock de next/navigation
vi.mock('next/navigation', () => ({
  usePathname: vi.fn(),
}));

// Mock de componentes complejos
vi.mock('@/components/Sidebar', () => ({
  default: () => <div data-testid="sidebar">Sidebar</div>,
}));

vi.mock('@/components/Topbar', () => ({
  default: () => <div data-testid="topbar">Topbar</div>,
}));

vi.mock('@/components/ToastContainer', () => ({
  default: () => <div data-testid="toast-container">ToastContainer</div>,
}));

describe('ConditionalLayout', () => {
  it('debe mostrar layout completo para páginas no-auth', () => {
    (usePathname as any).mockReturnValue('/dashboard');
    
    render(
      <ConditionalLayout>
        <div>Test Content</div>
      </ConditionalLayout>
    );
    
    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
    expect(screen.getByTestId('topbar')).toBeInTheDocument();
    expect(screen.getByText('Test Content')).toBeInTheDocument();
    expect(screen.getByTestId('toast-container')).toBeInTheDocument();
  });

  it('debe mostrar solo contenido y toast para páginas auth', () => {
    (usePathname as any).mockReturnValue('/auth/login');
    
    render(
      <ConditionalLayout>
        <div>Login Content</div>
      </ConditionalLayout>
    );
    
    expect(screen.queryByTestId('sidebar')).not.toBeInTheDocument();
    expect(screen.queryByTestId('topbar')).not.toBeInTheDocument();
    expect(screen.getByText('Login Content')).toBeInTheDocument();
    expect(screen.getByTestId('toast-container')).toBeInTheDocument();
  });

  it('debe detectar páginas auth correctamente', () => {
    (usePathname as any).mockReturnValue('/auth/reset-password');
    
    render(
      <ConditionalLayout>
        <div>Reset Password</div>
      </ConditionalLayout>
    );
    
    expect(screen.queryByTestId('sidebar')).not.toBeInTheDocument();
    expect(screen.getByText('Reset Password')).toBeInTheDocument();
  });
});

