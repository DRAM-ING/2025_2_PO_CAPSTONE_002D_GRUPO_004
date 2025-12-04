# 📊 Guía de Cobertura de Código - PGF

Esta guía explica cómo generar y visualizar reportes de cobertura de código para el proyecto PGF.

> **💡 Dashboard Interactivo**: Para información detallada sobre el dashboard interactivo de Vitest, consulta [VITEST_DASHBOARD.md](./VITEST_DASHBOARD.md)

## 📋 Requisitos Previos

### Backend (Python/Django)
- `pytest` - Framework de testing
- `pytest-cov` - Plugin para cobertura
- `pytest-django` - Plugin para Django

Instalación:
```powershell
pip install pytest pytest-cov pytest-django
```

### Frontend (Next.js/React)
- `vitest` - Framework de testing
- `@vitest/coverage-v8` - Plugin para cobertura

Instalación:
```powershell
cd frontend/pgf-frontend
npm install
```

## 🚀 Scripts Disponibles

### Backend

#### 1. Cobertura de Todos los Módulos
```powershell
.\scripts\coverage-backend.ps1
```

Genera reportes de cobertura para todos los módulos del backend.

**Opciones:**
- `-Open` - Abre el reporte HTML automáticamente
- `-All` - Ejecuta todos los tests (equivalente a sin parámetros)

**Ejemplo:**
```powershell
.\scripts\coverage-backend.ps1 -Open
```

#### 2. Cobertura de un Módulo Específico
```powershell
.\scripts\coverage-backend-module.ps1 -Module workorders
```

Genera reporte de cobertura para un módulo específico.

**Parámetros:**
- `-Module` (requerido) - Nombre del módulo (workorders, vehicles, inventory, etc.)
- `-Open` - Abre el reporte HTML automáticamente

**Ejemplo:**
```powershell
.\scripts\coverage-backend-module.ps1 -Module workorders -Open
```

**Módulos disponibles:**
- `workorders` - Órdenes de trabajo
- `vehicles` - Vehículos
- `inventory` - Inventario
- `drivers` - Choferes
- `users` - Usuarios
- `notifications` - Notificaciones
- `reports` - Reportes
- `scheduling` - Programación
- `core` - Core
- `emergencies` - Emergencias

#### 3. Cobertura de Todos los Módulos (Individual)
```powershell
.\scripts\coverage-backend-all-modules.ps1
```

Genera reportes individuales para cada módulo y un resumen consolidado.

**Opciones:**
- `-Open` - Abre todos los reportes HTML automáticamente

**Ejemplo:**
```powershell
.\scripts\coverage-backend-all-modules.ps1 -Open
```

### Frontend

#### 1. Cobertura del Frontend
```powershell
.\scripts\coverage-frontend.ps1
```

Genera reporte de cobertura para el frontend.

**Opciones:**
- `-Open` - Abre el reporte HTML automáticamente
- `-UI` - Abre el dashboard interactivo de Vitest
- `-Watch` - Ejecuta tests en modo watch

**Ejemplos:**
```powershell
# Generar cobertura y abrir reporte
.\scripts\coverage-frontend.ps1 -Open

# Abrir dashboard interactivo de Vitest
.\scripts\coverage-frontend.ps1 -UI

# Modo watch (se actualiza automáticamente)
.\scripts\coverage-frontend.ps1 -Watch
```

> **💡 Dashboard Interactivo**: El dashboard de Vitest permite ver y ejecutar tests en tiempo real. Ver [VITEST_DASHBOARD.md](./VITEST_DASHBOARD.md) para más detalles.

**Opciones:**
- `-Open` - Abre el reporte HTML automáticamente
- `-Watch` - Ejecuta tests en modo watch

**Ejemplo:**
```powershell
.\scripts\coverage-frontend.ps1 -Open
```

### Consolidado

#### 1. Cobertura Completa (Backend + Frontend)
```powershell
.\scripts\coverage-all.ps1
```

Genera reportes de cobertura para backend y frontend.

**Opciones:**
- `-Open` - Abre todos los reportes HTML automáticamente

**Ejemplo:**
```powershell
.\scripts\coverage-all.ps1 -Open
```

#### 2. Dashboard Consolidado
```powershell
.\scripts\generate-coverage-dashboard.ps1
```

Genera un dashboard HTML consolidado con todos los reportes de cobertura.

**Opciones:**
- `-Open` - Abre el dashboard automáticamente

**Ejemplo:**
```powershell
.\scripts\generate-coverage-dashboard.ps1 -Open
```

## 📁 Estructura de Reportes

Los reportes se generan en el directorio `coverage-reports/`:

```
coverage-reports/
├── html/                          # Reporte HTML general del backend
├── coverage.xml                   # Reporte XML (para CI/CD)
├── coverage.json                  # Reporte JSON
├── modules/                       # Reportes por módulo
│   ├── workorders/
│   │   ├── html/
│   │   ├── coverage.xml
│   │   ├── coverage.json
│   │   └── coverage.lcov
│   ├── vehicles/
│   └── ...
├── frontend/                      # Reportes del frontend
│   ├── index.html
│   └── coverage-final.json
└── dashboard/                     # Dashboard consolidado
    └── index.html
```

## 📊 Visualización de Reportes

### Reportes HTML

Los reportes HTML se pueden abrir directamente en el navegador:

1. **Backend General:**
   ```
   coverage-reports/html/index.html
   ```

2. **Módulo Específico:**
   ```
   coverage-reports/modules/workorders/html/index.html
   ```

3. **Frontend:**
   ```
   coverage-reports/frontend/index.html
   ```

4. **Dashboard Consolidado:**
   ```
   coverage-reports/dashboard/index.html
   ```

### Dashboard

El dashboard consolidado muestra:
- Resumen general de backend y frontend
- Métricas por módulo
- Enlaces a reportes detallados
- Gráficos de progreso visuales

## 🎯 Umbrales de Cobertura

### Backend
- **Mínimo requerido:** 60%
- **Objetivo:** 80%+
- **Ideal:** 90%+

### Frontend
- **Mínimo requerido:** 60%
- **Objetivo:** 80%+
- **Ideal:** 90%+

Los umbrales se pueden ajustar en:
- Backend: `pytest.ini` (línea `--cov-fail-under`)
- Frontend: `frontend/pgf-frontend/vitest.config.ts` (sección `thresholds`)

## 🔧 Configuración

### pytest.ini

Configuración principal de pytest:

```ini
[pytest]
testpaths = apps
addopts = 
    --cov=apps
    --cov-report=html:htmlcov
    --cov-report=xml:coverage.xml
    --cov-report=term-missing
    --cov-fail-under=60
```

### vitest.config.ts

Configuración de Vitest para el frontend:

```typescript
coverage: {
  provider: 'v8',
  reporter: ['text', 'json', 'html', 'lcov'],
  thresholds: {
    lines: 60,
    functions: 60,
    branches: 60,
    statements: 60,
  },
}
```

## 📈 Integración con CI/CD

Los reportes XML y JSON pueden ser utilizados por herramientas de CI/CD:

- **XML:** Compatible con herramientas como SonarQube, Codecov
- **JSON:** Para procesamiento programático
- **LCOV:** Compatible con servicios como Coveralls

### Ejemplo para GitHub Actions

```yaml
- name: Run tests with coverage
  run: |
    .\scripts\coverage-backend.ps1
    .\scripts\coverage-frontend.ps1

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    files: coverage-reports/coverage.xml,coverage-reports/frontend/coverage-final.json
```

## 🐛 Solución de Problemas

### Backend

**Error: "pytest no se reconoce como comando"**
```powershell
pip install pytest pytest-cov pytest-django
```

**Error: "No module named 'apps'"**
Asegúrate de estar en el directorio raíz del proyecto.

**Error: "No tests found"**
Verifica que los archivos de test sigan el patrón `test_*.py` o `*_test.py`.

### Frontend

**Error: "vitest no se reconoce como comando"**
```powershell
cd frontend/pgf-frontend
npm install
```

**Error: "Cannot find module"**
Ejecuta `npm install` en el directorio del frontend.

## 📝 Mejores Prácticas

1. **Ejecuta cobertura regularmente** - Al menos antes de cada commit importante
2. **Aumenta la cobertura gradualmente** - No intentes llegar al 100% de una vez
3. **Enfócate en código crítico** - Prioriza tests para lógica de negocio importante
4. **Revisa reportes regularmente** - Identifica áreas con baja cobertura
5. **Integra en CI/CD** - Asegura que la cobertura no disminuya

## 🔗 Recursos Adicionales

- [Documentación de pytest-cov](https://pytest-cov.readthedocs.io/)
- [Documentación de Vitest Coverage](https://vitest.dev/guide/coverage.html)
- [Guía de Testing en Django](https://docs.djangoproject.com/en/stable/topics/testing/)

---

**Última actualización:** $(Get-Date -Format "yyyy-MM-dd")

