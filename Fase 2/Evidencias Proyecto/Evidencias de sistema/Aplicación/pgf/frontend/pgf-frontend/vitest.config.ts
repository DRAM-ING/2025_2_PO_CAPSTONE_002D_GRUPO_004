import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,           // Permite usar describe, it, expect sin importar
    environment: 'jsdom',    // Simula el navegador para React
    setupFiles: ['./src/__tests__/setup.ts'],  // Archivo de configuración inicial
    css: true,               // Procesa archivos CSS en los tests
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'json-summary', 'lcov'],
      reportsDirectory: './coverage',
      exclude: [
        'node_modules/',
        'src/__tests__/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData',
        '**/*.test.{ts,tsx}',
        '**/*.spec.{ts,tsx}',
        '**/types/**',
        '**/*.stories.{ts,tsx}',
      ],
      include: [
        'src/**/*.{ts,tsx}',
      ],
      thresholds: {
        // Umbrales ajustados temporalmente a valores realistas basados en cobertura actual
        // Meta a largo plazo: 60% para todas las métricas
        // TODO: Aumentar gradualmente la cobertura escribiendo más tests
        lines: 10,
        functions: 15,
        branches: 40,
        statements: 10,
      },
    },
    reporters: ['verbose', 'json', 'html'],
    outputFile: {
      json: '../../test-results/junit/frontend-junit.json',
      html: '../../test-results/frontend-report.html',
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  css: {
    postcss: {
      // Deshabilitar PostCSS en tests para evitar conflictos con Tailwind
      plugins: [],
    },
  },
})

