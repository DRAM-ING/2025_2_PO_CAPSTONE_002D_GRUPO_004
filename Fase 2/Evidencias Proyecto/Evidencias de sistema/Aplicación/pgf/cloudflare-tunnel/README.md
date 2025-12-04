# Configuración de Cloudflare Tunnel (100% Gratuito - Sin Dominio)

Esta guía te ayudará a configurar Cloudflare Tunnel para exponer tu aplicación PGF de forma segura desde tu PC local **sin necesidad de dominio propio**.

## ¿Qué es Cloudflare Tunnel?

Cloudflare Tunnel (cloudflared) crea un túnel seguro entre tu PC y Cloudflare, permitiendo que tu aplicación sea accesible desde internet sin necesidad de:
- Abrir puertos en tu router
- Configurar port forwarding
- Exponer tu IP pública directamente
- **Tener un dominio propio** (usa URLs gratuitas de Cloudflare)

## Opciones Disponibles

### Opción 1: Quick Tunnel (Más Simple - Recomendado para empezar)

**Ventajas:**
- ✅ No requiere configuración
- ✅ No requiere cuenta de Cloudflare
- ✅ Funciona inmediatamente
- ✅ Completamente gratuito

**Desventajas:**
- ⚠️ Las URLs cambian cada vez que reinicias el túnel
- ⚠️ URLs aleatorias (ej: `https://random-name-1234.trycloudflare.com`)

**Cómo usar:**
```powershell
# Para Frontend (puerto 3000)
cloudflared tunnel --url http://localhost:3000

# Para API (puerto 8000) - en otra terminal
cloudflared tunnel --url http://localhost:8000
```

Cada comando te dará una URL única. Anota ambas URLs y configúralas en tu `.env`.

### Opción 2: Túnel Permanente (URLs Estables)

**Ventajas:**
- ✅ URLs más estables (aunque siguen siendo aleatorias)
- ✅ Mejor para producción
- ✅ Puedes configurar múltiples servicios en un solo túnel

**Desventajas:**
- ⚠️ Requiere cuenta en Cloudflare Zero Trust (gratuita)
- ⚠️ Requiere configuración inicial

**Cómo usar:**

1. **Crear cuenta en Cloudflare Zero Trust:**
   - Ve a: https://one.dash.cloudflare.com/
   - Crea una cuenta (es gratis)

2. **Iniciar sesión:**
   ```powershell
   cloudflared tunnel login
   ```

3. **Crear túnel:**
   ```powershell
   cloudflared tunnel create pgf
   ```
   
   Esto generará un ID y un archivo `credentials.json` en:
   `C:\Users\luxo_\.cloudflared\`

4. **Configurar túnel:**
   
   Edita `config.yml`:
   ```yaml
   tunnel: TU_TUNNEL_ID
   credentials-file: C:\Users\luxo_\.cloudflared\TU_TUNNEL_ID.json
   
   ingress:
     - service: http://localhost:3000
     - service: http://localhost:8000
     - service: http_status:404
   ```

5. **Iniciar túnel:**
   ```powershell
   cloudflared tunnel --config config.yml run
   ```

## Prerrequisitos

1. Windows 10/11 (o tu sistema operativo)
2. Docker y Docker Compose instalados
3. Para Quick Tunnel: Solo `cloudflared` instalado
4. Para Túnel Permanente: Cuenta en Cloudflare Zero Trust (gratuita)

**NO necesitas:**
- ❌ Dominio propio
- ❌ Configuración de DNS
- ❌ Abrir puertos en el router

## Paso 1: Instalar cloudflared

### Windows (PowerShell como Administrador)

```powershell
# Ejecutar script automático
.\setup-cloudflare.ps1
```

### O manualmente:

1. Ve a: https://github.com/cloudflare/cloudflared/releases/latest
2. Descarga `cloudflared-windows-amd64.exe`
3. Renómbralo a `cloudflared.exe`
4. Colócalo en una carpeta (ej: `C:\cloudflared\`)
5. Agrega esa carpeta al PATH de Windows

## Paso 2: Iniciar Túneles

### Quick Tunnel (Recomendado para empezar)

**Opción A: Script automático**
```powershell
.\start-quick-tunnels.ps1
```

**Opción B: Manual**
```powershell
# Terminal 1 - Frontend
cloudflared tunnel --url http://localhost:3000

# Terminal 2 - API
cloudflared tunnel --url http://localhost:8000
```

Anota las URLs que te da Cloudflare (algo como `https://random-name-1234.trycloudflare.com`).

### Túnel Permanente

Sigue los pasos de la Opción 2 arriba.

## Paso 3: Configurar Variables de Entorno

Una vez que tengas las URLs de Cloudflare, configura tu `.env`:

```env
# URLs de Cloudflare (reemplaza con tus URLs reales)
ALLOWED_HOSTS=random-name-1234.trycloudflare.com,random-name-5678.trycloudflare.com,localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=https://random-name-1234.trycloudflare.com
CSRF_TRUSTED_ORIGINS=https://random-name-1234.trycloudflare.com
FRONTEND_URL=https://random-name-1234.trycloudflare.com
PUBLIC_URL=https://random-name-5678.trycloudflare.com
NEXT_PUBLIC_API_BASE_URL=https://random-name-5678.trycloudflare.com
```

**Importante:** Reemplaza `random-name-1234` y `random-name-5678` con tus URLs reales.

## Paso 4: Reiniciar Aplicación

```powershell
docker-compose restart
```

## Verificar

1. Accede a la URL del Frontend en tu navegador
2. Verifica que la API responda en la URL de la API
3. Prueba hacer login

## Troubleshooting

### Las URLs cambian cada vez
- ✅ Esto es normal con Quick Tunnel
- ✅ Actualiza `.env` con las nuevas URLs
- ✅ Considera usar túnel permanente para URLs más estables

### Error 502 Bad Gateway
- ✅ Verifica que Docker esté corriendo: `docker-compose ps`
- ✅ Verifica que los servicios estén en los puertos correctos
- ✅ Asegúrate de que los túneles estén activos

### CORS errors
- ✅ Verifica que las URLs en `.env` empiecen con `https://`
- ✅ Reinicia Docker: `docker-compose restart`

## Seguridad

✅ **Ventajas:**
- Todo el tráfico pasa por HTTPS automáticamente
- Tu IP real nunca se expone
- Protección DDoS incluida
- No necesitas abrir puertos

⚠️ **Notas:**
- Las URLs de Quick Tunnel son públicas
- Comparte las URLs solo con quien confíes
- Considera usar Cloudflare Access para mayor seguridad

## Archivos de Configuración

- `config.yml` - Para túnel permanente (opcional)
- `config-quick.yml` - Referencia para Quick Tunnel (no se usa directamente)

## Más Información

Consulta `GUIA_CLOUDFLARE_TUNNEL.md` para la guía completa paso a paso.
