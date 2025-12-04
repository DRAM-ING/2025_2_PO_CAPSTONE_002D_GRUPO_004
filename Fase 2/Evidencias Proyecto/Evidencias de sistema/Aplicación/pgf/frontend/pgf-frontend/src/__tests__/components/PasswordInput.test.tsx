/**
 * Tests para el componente PasswordInput
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import PasswordInput from '@/components/PasswordInput';

describe('PasswordInput', () => {
  const mockOnChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('debe renderizar el input de contraseña', () => {
    render(<PasswordInput value="" onChange={mockOnChange} />);
    
    const input = screen.getByPlaceholderText(/ingresa tu contraseña/i);
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute('type', 'password');
  });

  it('debe mostrar/ocultar contraseña al hacer click en el botón', () => {
    render(<PasswordInput value="test123" onChange={mockOnChange} />);
    
    const input = screen.getByPlaceholderText(/ingresa tu contraseña/i) as HTMLInputElement;
    const toggleButton = screen.getByRole('button', { name: /mostrar contraseña/i });
    
    // Inicialmente debe estar oculta
    expect(input.type).toBe('password');
    
    // Click para mostrar
    fireEvent.click(toggleButton);
    expect(input.type).toBe('text');
    expect(screen.getByRole('button', { name: /ocultar contraseña/i })).toBeInTheDocument();
    
    // Click para ocultar
    fireEvent.click(screen.getByRole('button', { name: /ocultar contraseña/i }));
    expect(input.type).toBe('password');
  });

  it('debe mostrar el label si se proporciona', () => {
    render(<PasswordInput value="" onChange={mockOnChange} label="Contraseña" />);
    
    const label = screen.getByText(/contraseña/i);
    expect(label).toBeInTheDocument();
    expect(label.tagName).toBe('LABEL');
  });

  it('debe mostrar mensaje de error si se proporciona', () => {
    render(<PasswordInput value="" onChange={mockOnChange} error="Contraseña requerida" />);
    
    expect(screen.getByText(/contraseña requerida/i)).toBeInTheDocument();
    const input = screen.getByPlaceholderText(/ingresa tu contraseña/i);
    expect(input).toHaveClass('border-red-500');
  });

  it('debe aplicar className personalizada', () => {
    render(<PasswordInput value="" onChange={mockOnChange} className="custom-class" />);
    
    const input = screen.getByPlaceholderText(/ingresa tu contraseña/i);
    expect(input).toHaveClass('custom-class');
  });

  it('debe respetar el atributo required', () => {
    render(<PasswordInput value="" onChange={mockOnChange} required />);
    
    const input = screen.getByPlaceholderText(/ingresa tu contraseña/i);
    expect(input).toBeRequired();
  });

  it('debe respetar el minLength', () => {
    render(<PasswordInput value="" onChange={mockOnChange} minLength={8} />);
    
    const input = screen.getByPlaceholderText(/ingresa tu contraseña/i);
    expect(input).toHaveAttribute('minLength', '8');
  });

  it('debe llamar onChange cuando se escribe', () => {
    render(<PasswordInput value="" onChange={mockOnChange} />);
    
    const input = screen.getByPlaceholderText(/ingresa tu contraseña/i);
    fireEvent.change(input, { target: { value: 'nueva contraseña' } });
    
    expect(mockOnChange).toHaveBeenCalledTimes(1);
  });

  it('debe usar placeholder personalizado', () => {
    render(<PasswordInput value="" onChange={mockOnChange} placeholder="Escribe aquí" />);
    
    expect(screen.getByPlaceholderText(/escribe aquí/i)).toBeInTheDocument();
  });

  it('debe usar id personalizado', () => {
    render(<PasswordInput id="custom-id" value="" onChange={mockOnChange} label="Password" />);
    
    const input = screen.getByLabelText(/password/i);
    expect(input).toHaveAttribute('id', 'custom-id');
  });
});

