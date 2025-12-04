# Scripts de Pruebas

Este directorio contiene scripts para ejecutar pruebas y generar reportes detallados.

## Scripts Disponibles

### `run_tests_with_reports.py`

Script principal para ejecutar todas las pruebas y generar reportes detallados por módulo.

**Uso:**
```bash
# Desde el contenedor Docker
docker-compose exec api poetry run python scripts/run_tests_with_reports.py

# O directamente (si tienes las dependencias instaladas)
python scripts/run_tests_with_reports.py
```

**Características:**
- Ejecuta pruebas para cada módulo por separado
- Genera reportes en múltiples formatos (HTML, JSON, TXT, JUnit XML)
- Crea un resumen general con estadísticas
- Organiza los reportes por módulo en `test-results/reports/`

**Estructura de Reportes:**
```
test-results/
├── reports/
│   ├── validators/
│   │   ├── report_YYYYMMDD_HHMMSS.html
│   │   ├── report_YYYYMMDD_HHMMSS.json
│   │   ├── report_YYYYMMDD_HHMMSS.txt
│   │   ├── junit_YYYYMMDD_HHMMSS.xml
│   │   └── summary_YYYYMMDD_HHMMSS.json
│   ├── users_models/
│   ├── users_serializers/
│   ├── users_views/
│   ├── vehicles_models/
│   ├── vehicles_serializers/
│   ├── workorders_models/
│   ├── workorders_serializers/
│   ├── summary_all_YYYYMMDD_HHMMSS.json
│   └── summary_all_YYYYMMDD_HHMMSS.html
└── junit.xml
```

## Otros Scripts

### `dump_schema_simple.sh`
Script para generar dump del esquema SQL desde PostgreSQL.

**Uso:**
```bash
# Generar dump con nombre por defecto (docs/ESQUEMA_SQL_FROM_DB.sql)
./scripts/dump_schema_simple.sh

# Especificar archivo de salida
./scripts/dump_schema_simple.sh docs/mi_esquema.sql
```

**Características:**
- Lee configuración desde `.env` o variables de entorno
- Detecta automáticamente si la BD está en Docker
- Genera solo el esquema (sin datos)
- Listo para usar en dbdiagram.io

**Si la BD está en Docker:**
```bash
# Alternativa usando Docker directamente
docker exec pgf-db pg_dump -U pgf -d pgf -s --no-owner --no-privileges > docs/ESQUEMA_SQL_FROM_DB.sql
```

### `dump_schema.py`
Versión Python que usa Django settings (requiere entorno Django configurado).

### `run_tests.sh` (Linux/Mac)
Script bash para ejecutar pruebas con opciones.

### `run_tests.bat` (Windows)
Script batch para ejecutar pruebas en Windows.

## Visualizar Reportes

Los reportes HTML se pueden abrir directamente en el navegador:
- Reporte general: `test-results/reports/summary_all_*.html`
- Reporte por módulo: `test-results/reports/{modulo}/report_*.html`
- Cobertura: `test-results/reports/{modulo}/coverage/index.html`

