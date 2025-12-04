# 🚛 PGF - Plataforma de Gestión de Flota PepsiCo

Sistema completo de gestión de flota vehicular desarrollado para PepsiCo, con gestión de órdenes de trabajo, programación de mantenimientos, emergencias en ruta, choferes, reportes ejecutivos y más.

## 📚 Documentación

### 📖 Manuales de Usuario
- [Manual de Usuario General](./MANUAL_USUARIO_GENERAL.md) - Guía completa para todos los usuarios
- [Manuales por Rol](./MANUALES_USUARIO_POR_ROLES.md) - Guías específicas por rol de usuario

### 🗄️ Base de Datos
- [Modelo de Datos](./MODELO_DATOS.md) - Documentación completa del modelo de datos
- [Diagrama MER](./MER_DIAGRAMA.md) - Diagrama Entidad-Relación
- [Esquema SQL Completo](./ESQUEMA_SQL_COMPLETO.sql) - Script SQL completo de la base de datos

### 🧪 Pruebas y Cobertura
- [Pruebas con Docker](./PRUEBAS_DOCKER.md) - Guía de pruebas usando Docker
- [Cobertura de Código](./README-COVERAGE.md) - Guía de cobertura con pytest y vitest

### 🐳 Docker y Producción
- [Docker en Producción](./DOCKER_PRODUCCION.md) - Guía de despliegue en producción
- [Túneles Cloudflare](./TUNELES_CLOUDFLARE.md) - Guía de uso de túneles Cloudflare

## 🚀 Inicio Rápido

### Con Docker Compose (Recomendado)

```powershell
# 1. Clonar el repositorio
git clone <tu-repo-url>
cd pgf

# 2. Crear archivo .env
cp .env.example .env
# Editar .env con tus configuraciones

# 3. Iniciar todos los servicios
docker-compose up -d

# 4. Aplicar migraciones
docker-compose exec api poetry run python manage.py migrate

# 5. Crear superusuario
docker-compose exec api poetry run python manage.py createsuperuser

# 6. Acceder a la aplicación
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Swagger Docs: http://localhost:8000/api/docs/
```

### Producción

```powershell
# 1. Configurar .env.prod
cp .env.example .env.prod
# Editar .env.prod con valores de producción

# 2. Iniciar servicios en producción
.\docker-compose-prod-up.ps1 -d -build

# 3. Obtener URL del túnel
.\get-tunnel-url.ps1
```

Ver [Docker en Producción](./DOCKER_PRODUCCION.md) para más detalles.

## 🧪 Ejecutar Pruebas

### Backend (Pytest)

```powershell
# Todas las pruebas
docker-compose exec api poetry run pytest apps/ -v

# Con cobertura
.\scripts\coverage-backend.ps1

# Módulo específico
.\scripts\coverage-backend-module.ps1 -Module workorders
```

### Frontend (Vitest)

```powershell
# Todas las pruebas
docker-compose exec web sh -c "cd /app && npm run test"

# Con cobertura
.\scripts\coverage-frontend.ps1
```

### Cobertura Completa

```powershell
# Backend + Frontend
.\scripts\coverage-all.ps1

# Dashboard consolidado
.\scripts\generate-coverage-dashboard.ps1
```

Ver [Pruebas con Docker](./PRUEBAS_DOCKER.md) para más detalles.

## 📁 Estructura del Proyecto

```
pgf/
├── apps/                          # Aplicaciones Django
│   ├── users/                     # Usuarios y autenticación
│   ├── vehicles/                  # Gestión de vehículos
│   ├── workorders/                # Órdenes de trabajo
│   ├── drivers/                   # Choferes
│   ├── inventory/                 # Inventario
│   ├── scheduling/                # Programación
│   ├── emergencies/               # Emergencias
│   ├── reports/                   # Reportes
│   └── notifications/              # Notificaciones
├── frontend/pgf-frontend/         # Aplicación Next.js
├── docs/                          # Documentación
├── scripts/                       # Scripts de utilidad
├── docker-compose.yml             # Desarrollo
├── docker-compose.prod.yml        # Producción
└── README.md                      # Este archivo
```

## 🔧 Comandos Útiles

```powershell
# Ver logs
docker-compose logs -f api
docker-compose logs -f web

# Reiniciar servicios
docker-compose restart api web

# Acceder a shell del backend
docker-compose exec api poetry run python manage.py shell

# Aplicar migraciones
docker-compose exec api poetry run python manage.py migrate

# Crear migraciones
docker-compose exec api poetry run python manage.py makemigrations
```

## 📊 Características Principales

- ✅ Gestión completa de vehículos y órdenes de trabajo
- ✅ Sistema de roles y permisos (10 roles diferentes)
- ✅ Notificaciones en tiempo real (WebSocket)
- ✅ Reportes PDF completos (7 tipos)
- ✅ Sistema de evidencias con versionado
- ✅ Programación de mantenimientos
- ✅ Gestión de emergencias en ruta
- ✅ Inventario y solicitudes de repuestos
- ✅ Auditoría completa de acciones

## 🔗 Enlaces Rápidos

- **API Docs**: http://localhost:8000/api/docs/
- **Admin Panel**: http://localhost:8000/admin/
- **Frontend**: http://localhost:3000

## 📝 Licencia

Este proyecto es privado y propiedad de PepsiCo.

## 👥 Autores

- **Diego Alvarez** - dr.alvarez@duocuc.cl
- **Luis Diaz** - lu.diaza@duocuc.cl

---

**Versión**: 2.1.0  
**Última actualización**: Enero 2025

