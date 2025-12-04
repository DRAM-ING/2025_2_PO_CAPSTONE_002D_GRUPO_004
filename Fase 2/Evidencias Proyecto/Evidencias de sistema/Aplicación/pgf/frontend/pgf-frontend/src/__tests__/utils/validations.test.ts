import { describe, it, expect } from 'vitest'
import {
  validatePassword,
  validateEmail,
  validateRequired,
  validateWorkOrder,
  validateVehicle,
  validatePatente,
  normalizarPatente,
  validateYear,
  validateNumber,
  validateMinLength,
  validateMaxLength,
} from '@/lib/validations'

describe('Validations', () => {
  describe('validatePassword', () => {
    it('should return null for valid password', () => {
      const validPassword = 'Password123!'
      expect(validatePassword(validPassword)).toBeNull()
    })

    it('should return error for password shorter than 8 characters', () => {
      const shortPassword = 'Pass1!'
      const error = validatePassword(shortPassword)
      expect(error).toContain('8 caracteres')
    })

    it('should return error for password without uppercase', () => {
      const noUpper = 'password123!'
      const error = validatePassword(noUpper)
      expect(error).toContain('mayúscula')
    })

    it('should return error for password without lowercase', () => {
      const noLower = 'PASSWORD123!'
      const error = validatePassword(noLower)
      expect(error).toContain('minúscula')
    })

    it('should return error for password without number', () => {
      const noNumber = 'Password!'
      const error = validatePassword(noNumber)
      expect(error).toContain('número')
    })

    it('should return error for password without special character', () => {
      const noSpecial = 'Password123'
      const error = validatePassword(noSpecial)
      expect(error).toContain('carácter especial')
    })

    it('should return null for empty password (handled by validateRequired)', () => {
      expect(validatePassword('')).toBeNull()
    })

    it('should handle multiple errors', () => {
      const badPassword = 'pass'
      const error = validatePassword(badPassword)
      expect(error).toContain('8 caracteres')
      expect(error).toContain('mayúscula')
      expect(error).toContain('número')
      expect(error).toContain('carácter especial')
    })
  })

  describe('validateEmail', () => {
    it('should return null for valid email', () => {
      expect(validateEmail('test@example.com')).toBeNull()
    })

    it('should return error for invalid email format', () => {
      const error = validateEmail('invalid-email')
      expect(error).toBeTruthy()
    })

    it('should return error for email without @', () => {
      const error = validateEmail('testexample.com')
      expect(error).toBeTruthy()
    })

    it('should return error for email without domain', () => {
      const error = validateEmail('test@')
      expect(error).toBeTruthy()
    })

    it('should return null for empty email', () => {
      expect(validateEmail('')).toBeNull()
    })
  })

  describe('validateRequired', () => {
    it('should return null for non-empty string', () => {
      expect(validateRequired('test', 'Field')).toBeNull()
    })

    it('should return error for empty string', () => {
      const error = validateRequired('', 'Field')
      expect(error).toContain('Field')
      expect(error).toContain('requerido')
    })

    it('should return error for null', () => {
      const error = validateRequired(null, 'Field')
      expect(error).toBeTruthy()
    })

    it('should return error for undefined', () => {
      const error = validateRequired(undefined, 'Field')
      expect(error).toBeTruthy()
    })

    it('should return error for whitespace-only string', () => {
      const error = validateRequired('   ', 'Field')
      expect(error).toBeTruthy()
    })
  })

  describe('validateWorkOrder', () => {
    it('should return error for empty form', () => {
      const result = validateWorkOrder({} as any)
      expect(result.isValid).toBe(false)
      expect(result.errors._general).toBeTruthy()
    })

    it('should return error for null form', () => {
      const result = validateWorkOrder(null as any)
      expect(result.isValid).toBe(false)
      expect(result.errors._general).toBeTruthy()
    })

    it('should validate required fields', () => {
      const result = validateWorkOrder({
        vehiculo: '',
        tipo: 'MANTENCION',
        prioridad: 'MEDIA',
        motivo: '',
        responsable: '',
        items: [],
      })
      expect(result.isValid).toBe(false)
      expect(result.errors.vehiculo).toBeTruthy()
      expect(result.errors.motivo).toBeTruthy()
      expect(result.errors.responsable).toBeTruthy()
      expect(result.errors.items).toBeTruthy()
    })

    it('should validate vehiculo cannot be "0"', () => {
      const result = validateWorkOrder({
        vehiculo: '0',
        tipo: 'MANTENCION',
        prioridad: 'MEDIA',
        motivo: 'Test',
        responsable: '1',
        items: [{ tipo: 'SERVICIO', descripcion: 'Test', cantidad: 1, costo_unitario: 100 }],
      })
      expect(result.isValid).toBe(false)
      expect(result.errors.vehiculo).toBeTruthy()
    })

    it('should validate responsable cannot be "0"', () => {
      const result = validateWorkOrder({
        vehiculo: '1',
        tipo: 'MANTENCION',
        prioridad: 'MEDIA',
        motivo: 'Test',
        responsable: '0',
        items: [{ tipo: 'SERVICIO', descripcion: 'Test', cantidad: 1, costo_unitario: 100 }],
      })
      expect(result.isValid).toBe(false)
      expect(result.errors.responsable).toBeTruthy()
    })

    it('should validate items - REPUESTO requires description or repuesto', () => {
      const result = validateWorkOrder({
        vehiculo: '1',
        tipo: 'MANTENCION',
        prioridad: 'MEDIA',
        motivo: 'Test',
        responsable: '1',
        items: [
          {
            tipo: 'REPUESTO',
            descripcion: '',
            cantidad: 1,
            costo_unitario: 100,
            repuesto: null,
          },
        ],
      })
      expect(result.isValid).toBe(false)
      expect(result.errors['items.0.descripcion']).toBeTruthy()
    })

    it('should accept REPUESTO with repuesto selected', () => {
      const result = validateWorkOrder({
        vehiculo: '1',
        tipo: 'MANTENCION',
        prioridad: 'MEDIA',
        motivo: 'Test',
        responsable: '1',
        items: [
          {
            tipo: 'REPUESTO',
            descripcion: '',
            cantidad: 1,
            costo_unitario: 100,
            repuesto: 'uuid-repuesto',
          },
        ],
      })
      expect(result.isValid).toBe(true)
    })

    it('should validate SERVICIO requires description', () => {
      const result = validateWorkOrder({
        vehiculo: '1',
        tipo: 'MANTENCION',
        prioridad: 'MEDIA',
        motivo: 'Test',
        responsable: '1',
        items: [
          {
            tipo: 'SERVICIO',
            descripcion: '',
            cantidad: 1,
            costo_unitario: 100,
          },
        ],
      })
      expect(result.isValid).toBe(false)
      expect(result.errors['items.0.descripcion']).toBeTruthy()
    })

    it('should validate cantidad must be greater than 0', () => {
      const result = validateWorkOrder({
        vehiculo: '1',
        tipo: 'MANTENCION',
        prioridad: 'MEDIA',
        motivo: 'Test',
        responsable: '1',
        items: [
          {
            tipo: 'SERVICIO',
            descripcion: 'Test',
            cantidad: 0,
            costo_unitario: 100,
          },
        ],
      })
      expect(result.isValid).toBe(false)
      expect(result.errors['items.0.cantidad']).toBeTruthy()
    })

    it('should validate costo_unitario cannot be negative', () => {
      const result = validateWorkOrder({
        vehiculo: '1',
        tipo: 'MANTENCION',
        prioridad: 'MEDIA',
        motivo: 'Test',
        responsable: '1',
        items: [
          {
            tipo: 'SERVICIO',
            descripcion: 'Test',
            cantidad: 1,
            costo_unitario: -10,
          },
        ],
      })
      expect(result.isValid).toBe(false)
      expect(result.errors['items.0.costo_unitario']).toBeTruthy()
    })

    it('should handle costo_unitario as string with comma', () => {
      const result = validateWorkOrder({
        vehiculo: '1',
        tipo: 'MANTENCION',
        prioridad: 'MEDIA',
        motivo: 'Test',
        responsable: '1',
        items: [
          {
            tipo: 'SERVICIO',
            descripcion: 'Test',
            cantidad: 1,
            costo_unitario: '100,50' as any,
          },
        ],
      })
      // Debe normalizar la coma y aceptar el valor
      expect(result.isValid).toBe(true)
    })

    it('should validate valid work order', () => {
      const result = validateWorkOrder({
        vehiculo: '1',
        tipo: 'MANTENCION',
        prioridad: 'MEDIA',
        motivo: 'Test motivo',
        responsable: '1',
        items: [
          {
            tipo: 'SERVICIO',
            descripcion: 'Servicio de prueba',
            cantidad: 1,
            costo_unitario: 100,
          },
        ],
      })
      expect(result.isValid).toBe(true)
      expect(Object.keys(result.errors).length).toBe(0)
    })
  })

  describe('validateVehicle', () => {
    it('should validate required fields', () => {
      const result = validateVehicle({
        patente: '',
        marca: '',
        modelo: '',
        anio: '',
      })
      expect(result.isValid).toBe(false)
      expect(result.errors.patente).toBeTruthy()
      expect(result.errors.marca).toBeTruthy()
      expect(result.errors.modelo).toBeTruthy()
      expect(result.errors.anio).toBeTruthy()
    })

    it('should validate valid vehicle', () => {
      const result = validateVehicle({
        patente: 'AB1234',
        marca: '1',
        modelo: 'Modelo Test',
        anio: 2020,
      })
      expect(result.isValid).toBe(true)
    })
  })

  describe('validatePatente', () => {
    it('should validate AA1234 format', () => {
      expect(validatePatente('AB1234')).toBeNull()
      expect(validatePatente('AB-1234')).toBeNull()
      expect(validatePatente('ab 1234')).toBeNull()
    })

    it('should validate AAAA12 format', () => {
      expect(validatePatente('ABCD12')).toBeNull()
    })

    it('should validate AAAB12 format', () => {
      expect(validatePatente('AAAB12')).toBeNull()
    })

    it('should reject invalid formats', () => {
      expect(validatePatente('ABC123')).toBeTruthy()
      expect(validatePatente('123456')).toBeTruthy()
      expect(validatePatente('ABCDEF')).toBeTruthy()
      expect(validatePatente('AB123')).toBeTruthy()
      expect(validatePatente('AB12345')).toBeTruthy()
    })

    it('should return null for empty patente', () => {
      expect(validatePatente('')).toBeNull()
    })
  })

  describe('normalizarPatente', () => {
    it('should normalize patente correctly', () => {
      expect(normalizarPatente('AB-1234')).toBe('AB1234')
      expect(normalizarPatente('ab 1234')).toBe('AB1234')
      expect(normalizarPatente('AB_1234')).toBe('AB1234')
      expect(normalizarPatente('ABCD12')).toBe('ABCD12')
    })

    it('should return null for invalid patente', () => {
      expect(normalizarPatente('ABC123')).toBeNull()
      expect(normalizarPatente('123456')).toBeNull()
      expect(normalizarPatente('')).toBeNull()
    })
  })

  describe('validateYear', () => {
    it('should validate valid year', () => {
      const currentYear = new Date().getFullYear()
      expect(validateYear(2020)).toBeNull()
      expect(validateYear(currentYear)).toBeNull()
      expect(validateYear('2020')).toBeNull()
    })

    it('should reject year before 1900', () => {
      expect(validateYear(1899)).toBeTruthy()
    })

    it('should reject year too far in future', () => {
      const currentYear = new Date().getFullYear()
      expect(validateYear(currentYear + 2)).toBeTruthy()
    })

    it('should reject invalid year string', () => {
      expect(validateYear('invalid')).toBeTruthy()
    })
  })

  describe('validateNumber', () => {
    it('should validate valid number', () => {
      expect(validateNumber(10, 'Field')).toBeNull()
      expect(validateNumber('10', 'Field')).toBeNull()
    })

    it('should validate number within range', () => {
      expect(validateNumber(10, 'Field', 5, 15)).toBeNull()
      expect(validateNumber(5, 'Field', 5, 15)).toBeNull()
      expect(validateNumber(15, 'Field', 5, 15)).toBeNull()
    })

    it('should reject number below min', () => {
      const error = validateNumber(4, 'Field', 5, 15)
      expect(error).toBeTruthy()
      expect(error).toContain('mayor o igual')
    })

    it('should reject number above max', () => {
      const error = validateNumber(16, 'Field', 5, 15)
      expect(error).toBeTruthy()
      expect(error).toContain('menor o igual')
    })

    it('should reject non-numeric value', () => {
      const error = validateNumber('abc', 'Field')
      expect(error).toBeTruthy()
      expect(error).toContain('número')
    })
  })

  describe('validateMinLength', () => {
    it('should validate string with sufficient length', () => {
      expect(validateMinLength('test', 3, 'Field')).toBeNull()
      expect(validateMinLength('test', 4, 'Field')).toBeNull()
    })

    it('should reject string below min length', () => {
      const error = validateMinLength('te', 3, 'Field')
      expect(error).toBeTruthy()
      expect(error).toContain('al menos')
    })

    it('should return null for empty string', () => {
      expect(validateMinLength('', 3, 'Field')).toBeNull()
    })
  })

  describe('validateMaxLength', () => {
    it('should validate string within max length', () => {
      expect(validateMaxLength('test', 10, 'Field')).toBeNull()
      expect(validateMaxLength('test', 4, 'Field')).toBeNull()
    })

    it('should reject string above max length', () => {
      const error = validateMaxLength('test123', 5, 'Field')
      expect(error).toBeTruthy()
      expect(error).toContain('más de')
    })

    it('should return null for empty string', () => {
      expect(validateMaxLength('', 5, 'Field')).toBeNull()
    })
  })
})


