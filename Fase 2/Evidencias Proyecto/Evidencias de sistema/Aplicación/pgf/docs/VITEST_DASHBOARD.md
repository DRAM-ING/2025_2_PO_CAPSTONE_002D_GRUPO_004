# Guía: Vitest Dashboard en PGF

Esta guía explica cómo usar el dashboard interactivo de Vitest en el proyecto PGF.

## 📋 Estado Actual

El proyecto **ya tiene Vitest configurado** con todas las dependencias necesarias:

- ✅ `vitest` - Framework de testing
- ✅ `@vitest/ui` - Dashboard interactivo
- ✅ `@vitest/coverage-v8` - Cobertura de código
- ✅ `@testing-library/react` - Utilidades para testear componentes React
- ✅ `@testing-library/jest-dom` - Matchers adicionales
- ✅ `@testing-library/user-event` - Simular interacciones del usuario
- ✅ `jsdom` - Simula el navegador para tests de React
- ✅ `@vitejs/plugin-react` - Plugin de React para Vite/Vitest

## 🚀 Comandos Disponibles

### Ejecutar Tests

```powershell
# Ejecutar tests una vez
npm run test

# Ejecutar tests en modo watch (se actualiza automáticamente)
npm run test:watch

# Abrir dashboard interactivo
npm run test:ui

# Generar reporte de cobertura
npm run test:coverage

# Dashboard con cobertura
npm run test:coverage:ui
```

### Usando Scripts PowerShell

```powershell
# Cobertura del frontend
.\scripts\coverage-frontend.ps1

# Cobertura del frontend y abrir reportes
.\scripts\coverage-frontend.ps1 -Open

# Abrir dashboard interactivo
.\scripts\coverage-frontend.ps1 -UI

# Modo watch
.\scripts\coverage-frontend.ps1 -Watch

# Cobertura completa (backend + frontend + dashboard)
.\scripts\coverage-all.ps1

# Cobertura completa y abrir reportes
.\scripts\coverage-all.ps1 -Open
```

## 🎯 Dashboard Interactivo

### Cómo Abrir el Dashboard

1. **Desde el directorio del frontend:**
   ```powershell
   cd frontend/pgf-frontend
   npm run test:ui
   ```

2. **Usando el script PowerShell:**
   ```powershell
   .\scripts\coverage-frontend.ps1 -UI
   ```

3. **El dashboard se abrirá automáticamente** en tu navegador en una URL como:
   ```
   http://localhost:51204/__vitest__/
   ```

### Funcionalidades del Dashboard

Una vez abierto, podrás:

- ✅ **Ver todos los tests organizados** por archivo y suite
- ✅ **Ejecutar tests individuales** haciendo clic en ellos
- ✅ **Ver resultados en tiempo real** mientras se ejecutan
- ✅ **Ver errores y stack traces detallados** con código resaltado
- ✅ **Filtrar por estado**: passed, failed, skipped, todo
- ✅ **Ver tiempo de ejecución** de cada test
- ✅ **Ver cobertura de código** (si está configurado)
- ✅ **Buscar tests** por nombre o contenido
- ✅ **Ver estadísticas** de ejecución

### Características Avanzadas

#### Modo Watch

El dashboard se actualiza automáticamente cuando:
- Guardas cambios en archivos de test
- Guardas cambios en archivos fuente
- Agregas nuevos tests

#### Cobertura en Tiempo Real

Si ejecutas con `--coverage`, el dashboard mostrará:
- Porcentaje de cobertura por archivo
- Líneas cubiertas vs no cubiertas
- Funciones y ramas cubiertas

## 📁 Estructura de Archivos

```
frontend/pgf-frontend/
├── vitest.config.ts          # Configuración de Vitest
├── src/
│   ├── __tests__/
│   │   ├── setup.ts          # Configuración inicial de tests
│   │   ├── components/       # Tests de componentes
│   │   ├── hooks/            # Tests de hooks
│   │   ├── lib/              # Tests de utilidades
│   │   └── ...
│   └── ...
└── coverage/                 # Reportes de cobertura (generados)
    ├── index.html
    ├── coverage-final.json
    └── lcov.info
```

## ⚙️ Configuración Actual

### `vitest.config.ts`

```typescript
export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,           // Permite usar describe, it, expect sin importar
    environment: 'jsdom',    // Simula el navegador para React
    setupFiles: ['./src/__tests__/setup.ts'],
    css: true,               // Procesa archivos CSS en los tests
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'json-summary', 'lcov'],
      reportsDirectory: './coverage',
      // ... más configuración
    },
  },
})
```

### `src/__tests__/setup.ts`

Este archivo configura:
- ✅ Extensión de `expect` con matchers de `jest-dom`
- ✅ Limpieza automática después de cada test
- ✅ Mocks de Next.js router
- ✅ Mocks de `fetch` y `localStorage`
- ✅ Mocks del store de autenticación

## 📊 Reportes de Cobertura

Los reportes se generan en:

- **HTML**: `coverage/index.html` - Reporte visual interactivo
- **JSON**: `coverage/coverage-final.json` - Datos estructurados
- **LCOV**: `coverage/lcov.info` - Formato estándar para CI/CD
- **Consolidado**: `coverage-reports/frontend/` - Copia centralizada

### Ver Reportes

```powershell
# Abrir reporte HTML automáticamente
.\scripts\coverage-frontend.ps1 -Open

# O abrir manualmente
Start-Process "frontend/pgf-frontend/coverage/index.html"
```

## 🔧 Solución de Problemas

### El dashboard no se abre

1. Verifica que el puerto no esté en uso:
   ```powershell
   netstat -ano | findstr :51204
   ```

2. Verifica que las dependencias estén instaladas:
   ```powershell
   cd frontend/pgf-frontend
   npm install
   ```

3. Verifica que Vitest esté instalado:
   ```powershell
   npm list vitest @vitest/ui
   ```

### Los tests no se ejecutan

1. Verifica la configuración en `vitest.config.ts`
2. Verifica que `src/__tests__/setup.ts` exista
3. Revisa los errores en la consola del dashboard

### La cobertura no se muestra

1. Asegúrate de ejecutar con `--coverage`:
   ```powershell
   npm run test:coverage
   ```

2. Verifica que `@vitest/coverage-v8` esté instalado:
   ```powershell
   npm list @vitest/coverage-v8
   ```

## 📚 Recursos Adicionales

- [Documentación oficial de Vitest](https://vitest.dev/)
- [Documentación del Dashboard UI](https://vitest.dev/guide/ui.html)
- [Testing Library para React](https://testing-library.com/react)
- [Guía de Jest DOM Matchers](https://github.com/testing-library/jest-dom)

## 🎓 Ejemplo de Test

```typescript
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Button from '@/components/Button'

describe('Button', () => {
  it('debería renderizar el texto', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('debería ejecutar la función al hacer click', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Click</Button>)
    
    screen.getByText('Click').click()
    expect(handleClick).toHaveBeenCalledTimes(1)
  })
})
```

## ✅ Checklist de Configuración

- [x] Vitest instalado
- [x] Dashboard UI instalado
- [x] Configuración en `vitest.config.ts`
- [x] Archivo de setup en `src/__tests__/setup.ts`
- [x] Scripts en `package.json`
- [x] Scripts PowerShell para automatización
- [x] Reportes de cobertura configurados
- [x] Dashboard consolidado con backend

¡Todo está listo para usar! 🎉

