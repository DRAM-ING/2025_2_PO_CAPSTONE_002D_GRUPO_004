# 🧪 Guía de Pruebas con Docker - PGF

Esta guía explica cómo ejecutar todas las pruebas (backend con pytest y frontend con vitest) utilizando Docker.

## 📋 Requisitos Previos

- Docker y Docker Compose instalados
- El proyecto debe estar configurado con `docker-compose.yml`
- Los servicios deben estar corriendo

## 🚀 Inicio Rápido

### Verificar que los servicios estén corriendo

```powershell
docker-compose ps
```

Si no están corriendo, inícialos:

```powershell
docker-compose up -d
```

## 🔧 Pruebas del Backend (Pytest)

### Ejecutar todas las pruebas

```powershell
docker-compose exec api poetry run pytest apps/ -v
```

### Ejecutar pruebas con cobertura

```powershell
docker-compose exec api poetry run pytest apps/ --cov=apps --cov-report=html --cov-report=term-missing
```

### Ejecutar pruebas de un módulo específico

```powershell
# Ejemplo: Módulo workorders
docker-compose exec api poetry run pytest apps/workorders/ -v

# Ejemplo: Módulo vehicles
docker-compose exec api poetry run pytest apps/vehicles/ -v
```

### Ejecutar un archivo de prueba específico

```powershell
docker-compose exec api poetry run pytest apps/core/tests/test_validators.py -v
```

### Ejecutar pruebas con marcadores

```powershell
# Solo pruebas unitarias
docker-compose exec api poetry run pytest apps/ -m unit -v

# Solo pruebas de integración
docker-compose exec api poetry run pytest apps/ -m integration -v

# Excluir pruebas lentas
docker-compose exec api poetry run pytest apps/ -m "not slow" -v
```

### Ver reporte de cobertura HTML

Después de ejecutar pruebas con cobertura, el reporte HTML se genera en `htmlcov/index.html` dentro del contenedor. Para acceder:

```powershell
# Copiar el reporte al host
docker-compose exec api poetry run pytest apps/ --cov=apps --cov-report=html
docker cp $(docker-compose ps -q api):/app/htmlcov ./coverage-reports/backend-html
```

O mejor aún, usar el script:

```powershell
.\scripts\coverage-backend.ps1
```

## 🎨 Pruebas del Frontend (Vitest)

### Ejecutar todas las pruebas

```powershell
docker-compose exec web sh -c "cd /app && npm run test"
```

### Ejecutar pruebas en modo watch

```powershell
docker-compose exec web sh -c "cd /app && npm run test:watch"
```

### Ejecutar pruebas con cobertura

```powershell
docker-compose exec web sh -c "cd /app && npm run test:coverage"
```

### Ver reporte de cobertura HTML

Después de ejecutar pruebas con cobertura:

```powershell
# El reporte se genera en coverage/ dentro del contenedor
docker cp $(docker-compose ps -q web):/app/coverage ./coverage-reports/frontend
```

O usar el script:

```powershell
.\scripts\coverage-frontend.ps1
```

## 📊 Scripts Consolidados

### Cobertura completa (Backend + Frontend)

```powershell
.\scripts\coverage-all.ps1
```

Este script:
1. Ejecuta todas las pruebas del backend con cobertura
2. Ejecuta todas las pruebas del frontend con cobertura
3. Genera reportes HTML, XML y JSON
4. Consolida los reportes en `coverage-reports/`

### Cobertura de un módulo específico

```powershell
.\scripts\coverage-backend-module.ps1 -Module workorders
```

### Cobertura de todos los módulos

```powershell
.\scripts\coverage-backend-all-modules.ps1
```

### Dashboard consolidado

```powershell
.\scripts\generate-coverage-dashboard.ps1
```

Genera un dashboard HTML con todas las métricas de cobertura.

## 🔍 Comandos Útiles

### Ver logs de pruebas

```powershell
# Logs del backend
docker-compose logs api | Select-String "test"

# Logs del frontend
docker-compose logs web | Select-String "test"
```

### Ejecutar pruebas en modo verbose

```powershell
docker-compose exec api poetry run pytest apps/ -vv
```

### Ejecutar pruebas y detener en el primer fallo

```powershell
docker-compose exec api poetry run pytest apps/ -x
```

### Ejecutar pruebas y mostrar output completo

```powershell
docker-compose exec api poetry run pytest apps/ -s
```

### Ejecutar pruebas con timeout

```powershell
docker-compose exec api poetry run pytest apps/ --timeout=30
```

### Ejecutar pruebas paralelas

```powershell
docker-compose exec api poetry run pytest apps/ -n auto
```

(Requiere `pytest-xdist` instalado)

## 📁 Estructura de Reportes

Los reportes se generan en:

```
coverage-reports/
├── html/                    # Backend HTML
├── coverage.xml             # Backend XML
├── coverage.json            # Backend JSON
├── modules/                 # Por módulo
│   ├── workorders/
│   ├── vehicles/
│   └── ...
├── frontend/                # Frontend
│   ├── index.html
│   └── coverage-final.json
└── dashboard/               # Dashboard consolidado
    └── index.html
```

## 🐛 Solución de Problemas

### Error: "Container not found"

Asegúrate de que los servicios estén corriendo:

```powershell
docker-compose up -d
docker-compose ps
```

### Error: "pytest not found"

El contenedor debe tener pytest instalado. Verifica:

```powershell
docker-compose exec api poetry run pytest --version
```

### Error: "vitest not found"

El contenedor debe tener vitest instalado. Verifica:

```powershell
docker-compose exec web sh -c "cd /app && npm list vitest"
```

### Los reportes no se generan

Verifica que los directorios de salida existan:

```powershell
# Crear directorio si no existe
if (-not (Test-Path "coverage-reports")) {
    New-Item -ItemType Directory -Path "coverage-reports"
}
```

### Problemas de permisos

Si hay problemas de permisos al copiar archivos:

```powershell
# En Linux/Mac
docker-compose exec api chmod -R 755 htmlcov

# En Windows, generalmente no hay problemas
```

## 🎯 Mejores Prácticas

1. **Ejecuta pruebas antes de commit**
   ```powershell
   docker-compose exec api poetry run pytest apps/ -v
   ```

2. **Verifica cobertura regularmente**
   ```powershell
   .\scripts\coverage-all.ps1
   ```

3. **Usa marcadores para organizar pruebas**
   ```python
   @pytest.mark.unit
   def test_validator():
       ...
   ```

4. **Mantén umbrales de cobertura**
   - Backend: Mínimo 60%, objetivo 80%
   - Frontend: Mínimo 60%, objetivo 80%

5. **Revisa reportes HTML regularmente**
   - Identifica áreas con baja cobertura
   - Prioriza tests para código crítico

## 📚 Referencias

- [Documentación de pytest](https://docs.pytest.org/)
- [Documentación de Vitest](https://vitest.dev/)
- [README de Cobertura](./README-COVERAGE.md)

---

**Última actualización**: Enero 2025

