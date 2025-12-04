# 🐳 Docker en Producción - PGF

Esta guía explica cómo desplegar y gestionar el proyecto PGF en producción usando Docker Compose.

## 📋 Requisitos Previos

- Docker y Docker Compose instalados
- Archivo `.env.prod` configurado con variables de producción
- Acceso a Cloudflare Tunnel (opcional, para acceso externo)

## 🚀 Inicio Rápido

### 1. Configurar Variables de Entorno

Copia y configura el archivo de producción:

```powershell
cp .env.example .env.prod
# Edita .env.prod con tus valores de producción
```

**Variables importantes:**
- `SECRET_KEY`: Clave secreta de Django (generar nueva para producción)
- `DEBUG=False`: Desactivar modo debug
- `DATABASE_URL`: URL de PostgreSQL
- `REDIS_PASSWORD`: Contraseña de Redis
- `AWS_*`: Credenciales de S3
- `CLOUDFLARE_TUNNEL_URL`: URL del túnel (se genera automáticamente)

### 2. Iniciar Servicios

**Opción A: Script Automático (Recomendado)**

```powershell
.\docker-compose-prod-up.ps1 -d -build
```

Este script:
- Inicia todos los servicios
- Espera a que estén listos
- Obtiene y muestra la URL del túnel automáticamente

**Opción B: Manual**

```powershell
# Construir imágenes
docker-compose -f docker-compose.prod.yml build

# Iniciar servicios
docker-compose -f docker-compose.prod.yml up -d

# Obtener URL del túnel
.\get-tunnel-url.ps1
```

### 3. Aplicar Migraciones

```powershell
docker-compose -f docker-compose.prod.yml exec api poetry run python manage.py migrate
```

### 4. Crear Superusuario

```powershell
docker-compose -f docker-compose.prod.yml exec api poetry run python manage.py createsuperuser
```

## 📊 Servicios Incluidos

El `docker-compose.prod.yml` incluye:

- **db**: PostgreSQL 16
- **redis**: Redis 7 (cache y Celery)
- **api**: Backend Django
- **web**: Frontend Next.js
- **worker**: Celery worker
- **beat**: Celery beat (tareas programadas)
- **localstack**: S3 local (o usar S3 real)
- **tunnel**: Cloudflare Tunnel (acceso externo)

## 🔧 Comandos Útiles

### Ver Estado de Servicios

```powershell
docker-compose -f docker-compose.prod.yml ps
```

### Ver Logs

```powershell
# Todos los servicios
docker-compose -f docker-compose.prod.yml logs -f

# Servicio específico
docker-compose -f docker-compose.prod.yml logs -f api
docker-compose -f docker-compose.prod.yml logs -f web
docker-compose -f docker-compose.prod.yml logs -f tunnel
```

### Reiniciar Servicios

```powershell
# Todos
docker-compose -f docker-compose.prod.yml restart

# Servicio específico
docker-compose -f docker-compose.prod.yml restart api
```

### Detener Servicios

```powershell
docker-compose -f docker-compose.prod.yml down
```

### Detener y Eliminar Volúmenes

```powershell
docker-compose -f docker-compose.prod.yml down -v
```

⚠️ **Advertencia**: Esto elimina todos los datos.

## 🔄 Actualizar Aplicación

### Actualizar Código

```powershell
# 1. Detener servicios
docker-compose -f docker-compose.prod.yml down

# 2. Actualizar código (git pull, etc.)

# 3. Reconstruir imágenes
docker-compose -f docker-compose.prod.yml build

# 4. Iniciar servicios
.\docker-compose-prod-up.ps1 -d -build

# 5. Aplicar migraciones si hay cambios
docker-compose -f docker-compose.prod.yml exec api poetry run python manage.py migrate
```

### Actualizar Solo un Servicio

```powershell
# Ejemplo: Solo actualizar API
docker-compose -f docker-compose.prod.yml build api
docker-compose -f docker-compose.prod.yml up -d api
```

## 🔍 Monitoreo y Diagnóstico

### Ver Uso de Recursos

```powershell
docker stats
```

### Acceder a Shell del Contenedor

```powershell
# Backend
docker-compose -f docker-compose.prod.yml exec api sh

# Frontend
docker-compose -f docker-compose.prod.yml exec web sh
```

### Ejecutar Comandos Django

```powershell
# Shell de Django
docker-compose -f docker-compose.prod.yml exec api poetry run python manage.py shell

# Crear migraciones
docker-compose -f docker-compose.prod.yml exec api poetry run python manage.py makemigrations

# Aplicar migraciones
docker-compose -f docker-compose.prod.yml exec api poetry run python manage.py migrate

# Crear superusuario
docker-compose -f docker-compose.prod.yml exec api poetry run python manage.py createsuperuser
```

### Verificar Salud de Servicios

```powershell
# Backend
docker-compose -f docker-compose.prod.yml exec api curl http://localhost:8000/api/v1/ping/

# Frontend
docker-compose -f docker-compose.prod.yml exec web curl http://localhost:3000/
```

## 🌐 Acceso y URLs

### URLs Locales

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/api/docs/
- **Admin**: http://localhost:8000/admin/

### URL del Túnel (Acceso Externo)

```powershell
# Obtener URL
.\get-tunnel-url.ps1

# O leer del archivo
Get-Content .tunnel-url.txt
```

La URL del túnel permite acceso externo a través de Cloudflare.

## 🔐 Seguridad

### Variables de Entorno

Nunca commitees `.env.prod` al repositorio. Usa:

```powershell
# .gitignore ya incluye .env.prod
```

### Secretos

Para producción real, considera usar:
- Docker Secrets
- Azure Key Vault
- AWS Secrets Manager
- HashiCorp Vault

### Firewall

Asegúrate de:
- Bloquear puertos innecesarios
- Usar HTTPS (configurar reverse proxy)
- Limitar acceso a la base de datos

## 📦 Backup y Restauración

### Backup de Base de Datos

```powershell
# Backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U pgf pgf > backup_$(Get-Date -Format "yyyyMMdd_HHmmss").sql

# Restaurar
docker-compose -f docker-compose.prod.yml exec -T db psql -U pgf pgf < backup.sql
```

### Backup de Volúmenes

```powershell
# Backup de volúmenes
docker run --rm -v pgf_postgres_data_prod:/data -v ${PWD}:/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

## 🐛 Solución de Problemas

### Servicios no inician

```powershell
# Ver logs
docker-compose -f docker-compose.prod.yml logs

# Verificar configuración
docker-compose -f docker-compose.prod.yml config
```

### Error de conexión a base de datos

```powershell
# Verificar que PostgreSQL esté corriendo
docker-compose -f docker-compose.prod.yml ps db

# Ver logs de PostgreSQL
docker-compose -f docker-compose.prod.yml logs db
```

### Error de permisos

```powershell
# En Linux, puede ser necesario ajustar permisos
docker-compose -f docker-compose.prod.yml exec api chmod -R 755 /app
```

### Túnel no funciona

Ver [Guía de Túneles](./TUNELES_CLOUDFLARE.md)

## 📚 Scripts Disponibles

- `docker-compose-prod-up.ps1`: Iniciar servicios y obtener URL
- `get-tunnel-url.ps1`: Obtener URL del túnel
- `docker-compose-up-with-url.ps1`: Iniciar y mostrar URL
- `docker-compose-restart-with-url.ps1`: Reiniciar y mostrar URL

## 🔗 Referencias

- [Guía de Túneles](./TUNELES_CLOUDFLARE.md)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

**Última actualización**: Enero 2025

