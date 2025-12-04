/**
 * Tests para el componente PepsiCoLogo
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import PepsiCoLogo from '@/components/PepsiCoLogo';

describe('PepsiCoLogo', () => {
  it('debe renderizar el logo por defecto', () => {
    const { container } = render(<PepsiCoLogo />);
    
    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
    expect(svg).toHaveClass('h-10'); // tamaño md por defecto
  });

  it('debe aplicar diferentes tamaños', () => {
    const { container: containerSm } = render(<PepsiCoLogo size="sm" />);
    expect(containerSm.querySelector('svg')).toHaveClass('h-6');
    
    const { container: containerLg } = render(<PepsiCoLogo size="lg" />);
    expect(containerLg.querySelector('svg')).toHaveClass('h-16');
    
    const { container: containerXl } = render(<PepsiCoLogo size="xl" />);
    expect(containerXl.querySelector('svg')).toHaveClass('h-24');
  });

  it('debe mostrar texto cuando showText es true', () => {
    render(<PepsiCoLogo showText={true} />);
    
    expect(screen.getByText('pepsico')).toBeInTheDocument();
  });

  it('debe usar texto personalizado', () => {
    render(<PepsiCoLogo showText={true} text="PGF" />);
    
    expect(screen.getByText('PGF')).toBeInTheDocument();
    expect(screen.queryByText('pepsico')).not.toBeInTheDocument();
  });

  it('debe aplicar variante white', () => {
    const { container } = render(<PepsiCoLogo variant="white" showText={true} />);
    
    const svg = container.querySelector('svg');
    expect(svg).toHaveStyle({ filter: 'brightness(0) invert(1)' });
    
    const text = screen.getByText('pepsico');
    expect(text).toHaveClass('text-white');
  });

  it('debe aplicar variante dark', () => {
    render(<PepsiCoLogo variant="dark" showText={true} />);
    
    const text = screen.getByText('pepsico');
    expect(text).toHaveClass('text-gray-900', 'dark:text-white');
  });

  it('debe aplicar className personalizada', () => {
    const { container } = render(<PepsiCoLogo className="custom-class" />);
    
    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass('custom-class');
  });

  it('debe no mostrar texto por defecto', () => {
    render(<PepsiCoLogo />);
    
    expect(screen.queryByText('pepsico')).not.toBeInTheDocument();
  });
});

