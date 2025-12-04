# 🌐 Guía de Túneles Cloudflare - PGF

Esta guía explica cómo usar los scripts PowerShell para gestionar túneles de Cloudflare y obtener las URLs de acceso.

## 📋 Requisitos Previos

- Docker y Docker Compose instalados
- Cloudflare Tunnel instalado (incluido en `docker-compose.prod.yml`)
- Archivo `.env.prod` configurado

## 🚀 Scripts Disponibles

### 1. Iniciar Docker Compose en Producción

**Script**: `docker-compose-prod-up.ps1`

Inicia todos los servicios en modo producción y obtiene automáticamente la URL del túnel.

```powershell
# Modo detached (background)
.\docker-compose-prod-up.ps1 -d

# Con reconstrucción de imágenes
.\docker-compose-prod-up.ps1 -d -build

# Detener servicios existentes antes de iniciar
.\docker-compose-prod-up.ps1 -d -stop

# Modo interactivo (ver logs en tiempo real)
.\docker-compose-prod-up.ps1
```

**Parámetros:**
- `-d`: Modo detached (en background)
- `-build`: Reconstruir imágenes antes de iniciar
- `-stop`: Detener servicios existentes antes de iniciar

**Ejemplo completo:**
```powershell
.\docker-compose-prod-up.ps1 -d -build -stop
```

### 2. Obtener URL del Túnel

**Script**: `get-tunnel-url.ps1`

Obtiene la URL del túnel de Cloudflare desde los logs del contenedor.

```powershell
.\get-tunnel-url.ps1
```

**Características:**
- Espera hasta 2 minutos para que el túnel esté listo
- Extrae la URL de los logs automáticamente
- Guarda la URL en:
  - Variable de entorno: `$env:CLOUDFLARE_TUNNEL_URL`
  - Archivo: `.tunnel-url.txt`

**Ejemplo de salida:**
```
========================================
  URL DEL TÚNEL CLOUDFLARE
========================================

  https://nombre-aleatorio.trycloudflare.com

========================================
```

### 3. Iniciar con URL (Script Consolidado)

**Script**: `docker-compose-up-with-url.ps1`

Inicia Docker Compose y muestra la URL automáticamente.

```powershell
.\docker-compose-up-with-url.ps1
```

Este script combina:
1. Inicio de servicios con `docker-compose-prod-up.ps1`
2. Obtención de URL con `get-tunnel-url.ps1`

### 4. Reiniciar con URL

**Script**: `docker-compose-restart-with-url.ps1`

Reinicia los servicios y muestra la URL.

```powershell
.\docker-compose-restart-with-url.ps1
```

## 📝 Uso Paso a Paso

### Escenario 1: Primera vez

```powershell
# 1. Asegúrate de tener .env.prod configurado
# 2. Inicia los servicios
.\docker-compose-prod-up.ps1 -d -build

# 3. Espera a que los servicios estén listos (el script lo hace automáticamente)
# 4. La URL se mostrará automáticamente
```

### Escenario 2: Reiniciar servicios

```powershell
# Opción 1: Reiniciar y obtener URL
.\docker-compose-restart-with-url.ps1

# Opción 2: Manual
docker-compose -f docker-compose.prod.yml restart
.\get-tunnel-url.ps1
```

### Escenario 3: Solo obtener URL (servicios ya corriendo)

```powershell
.\get-tunnel-url.ps1
```

## 🔍 Verificar Estado del Túnel

### Ver logs del túnel

```powershell
docker-compose -f docker-compose.prod.yml logs tunnel
```

### Ver logs en tiempo real

```powershell
docker-compose -f docker-compose.prod.yml logs -f tunnel
```

### Verificar que el túnel esté corriendo

```powershell
docker-compose -f docker-compose.prod.yml ps tunnel
```

### Buscar URL en logs manualmente

```powershell
docker-compose -f docker-compose.prod.yml logs tunnel | Select-String "trycloudflare"
```

## 📁 Archivos Generados

### `.tunnel-url.txt`

Contiene la última URL del túnel obtenida. Útil para scripts automatizados.

```powershell
# Leer la URL
Get-Content .tunnel-url.txt

# Usar en scripts
$url = Get-Content .tunnel-url.txt
Write-Host "La URL es: $url"
```

### Variable de Entorno

La URL también se guarda en `$env:CLOUDFLARE_TUNNEL_URL`:

```powershell
# Ver la URL
$env:CLOUDFLARE_TUNNEL_URL

# Usar en scripts
Write-Host "Accede a: $env:CLOUDFLARE_TUNNEL_URL"
```

## 🐛 Solución de Problemas

### El túnel no genera URL

**Causa**: El túnel puede tardar en inicializarse.

**Solución**:
```powershell
# Esperar más tiempo
Start-Sleep -Seconds 10
.\get-tunnel-url.ps1

# Ver logs para diagnosticar
docker-compose -f docker-compose.prod.yml logs tunnel
```

### Error: "Container not found"

**Causa**: Los servicios no están corriendo.

**Solución**:
```powershell
# Verificar estado
docker-compose -f docker-compose.prod.yml ps

# Iniciar si es necesario
.\docker-compose-prod-up.ps1 -d
```

### La URL cambia cada vez

**Causa**: Cloudflare genera URLs aleatorias para túneles temporales.

**Solución**: Esto es normal. Para URLs permanentes, configura un túnel con nombre en Cloudflare Dashboard.

### El túnel se desconecta

**Causa**: Problemas de red o configuración.

**Solución**:
```powershell
# Reiniciar el túnel
docker-compose -f docker-compose.prod.yml restart tunnel

# Ver logs para diagnosticar
docker-compose -f docker-compose.prod.yml logs tunnel
```

## 🔐 Configuración Avanzada

### Túnel Permanente con Nombre

Para un túnel con URL fija, configura un túnel con nombre en Cloudflare:

1. Ve a Cloudflare Dashboard → Zero Trust → Networks → Tunnels
2. Crea un nuevo túnel con nombre
3. Obtén el token
4. Actualiza `docker-compose.prod.yml` con el token

### Múltiples Túneles

Para múltiples servicios, puedes crear varios túneles:

```yaml
services:
  tunnel-api:
    # Túnel para API
  tunnel-web:
    # Túnel para Frontend
```

## 📚 Referencias

- [Documentación de Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Docker Compose Production](./DOCKER_PRODUCCION.md)

---

**Última actualización**: Enero 2025

