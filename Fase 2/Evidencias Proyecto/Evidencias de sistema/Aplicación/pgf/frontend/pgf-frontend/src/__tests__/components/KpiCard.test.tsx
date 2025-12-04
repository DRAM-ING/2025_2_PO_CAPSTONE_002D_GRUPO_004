/**
 * Tests para el componente KpiCard
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { KpiCard } from '@/components/ui/KpiCard';

describe('KpiCard', () => {
  it('debe renderizar título y valor', () => {
    render(<KpiCard title="Total OTs" value="150" />);
    
    expect(screen.getByText('Total OTs')).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument();
  });

  it('debe mostrar hint si se proporciona', () => {
    render(<KpiCard title="Total OTs" value="150" hint="Último mes" />);
    
    expect(screen.getByText('Último mes')).toBeInTheDocument();
  });

  it('debe mostrar icono si se proporciona', () => {
    const icon = <span data-testid="icon">📊</span>;
    render(<KpiCard title="Total OTs" value="150" icon={icon} />);
    
    expect(screen.getByTestId('icon')).toBeInTheDocument();
  });

  it('debe renderizar valor como ReactNode', () => {
    const value = <span data-testid="custom-value">Custom Value</span>;
    render(<KpiCard title="Test" value={value} />);
    
    expect(screen.getByTestId('custom-value')).toBeInTheDocument();
  });

  it('debe aplicar clases CSS correctas', () => {
    const { container } = render(<KpiCard title="Test" value="100" />);
    
    const card = container.firstChild as HTMLElement;
    expect(card).toHaveClass('rounded-2xl', 'border', 'border-neutral-800', 'p-4');
  });
});

