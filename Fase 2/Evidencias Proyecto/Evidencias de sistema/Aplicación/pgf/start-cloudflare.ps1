# Script para iniciar Cloudflare Tunnel
# Asegúrate de haber configurado cloudflare-tunnel/config.yml primero

Write-Host "🚀 Iniciando Cloudflare Tunnel..." -ForegroundColor Green
Write-Host ""

# Verificar que existe el archivo de configuración
if (-not (Test-Path "cloudflare-tunnel\config.yml")) {
    Write-Host "❌ Error: No se encontró cloudflare-tunnel\config.yml" -ForegroundColor Red
    Write-Host "Ejecuta primero: .\setup-cloudflare.ps1" -ForegroundColor Yellow
    exit 1
}

# Verificar que existe el archivo de credenciales
if (-not (Test-Path "cloudflare-tunnel\credentials.json")) {
    Write-Host "❌ Error: No se encontró cloudflare-tunnel\credentials.json" -ForegroundColor Red
    Write-Host "Descarga el archivo desde el dashboard de Cloudflare" -ForegroundColor Yellow
    exit 1
}

# Verificar que cloudflared está instalado
$cloudflaredPath = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cloudflaredPath) {
    Write-Host "❌ Error: cloudflared no está instalado" -ForegroundColor Red
    Write-Host "Ejecuta primero: .\setup-cloudflare.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Archivos de configuración encontrados" -ForegroundColor Green
Write-Host ""

# Preguntar si quiere ejecutar como servicio o manualmente
Write-Host "¿Cómo deseas ejecutar el túnel?" -ForegroundColor Cyan
Write-Host "1. Como servicio de Windows (recomendado para producción)" -ForegroundColor White
Write-Host "2. Manualmente (para pruebas)" -ForegroundColor White
Write-Host ""
$choice = Read-Host "Selecciona una opción (1 o 2)"

if ($choice -eq "1") {
    Write-Host ""
    Write-Host "📦 Instalando como servicio..." -ForegroundColor Cyan
    
    # Instalar como servicio
    $configPath = (Resolve-Path "cloudflare-tunnel\config.yml").Path
    cloudflared service install --config $configPath
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Servicio instalado" -ForegroundColor Green
        Write-Host "Iniciando servicio..." -ForegroundColor Cyan
        Start-Service cloudflared
        Write-Host "✅ Servicio iniciado" -ForegroundColor Green
        Write-Host ""
        Write-Host "Para ver los logs:" -ForegroundColor Yellow
        Write-Host "  Get-Content `"C:\ProgramData\cloudflared\logs\cloudflared.log`" -Tail 50" -ForegroundColor White
        Write-Host ""
        Write-Host "Para detener:" -ForegroundColor Yellow
        Write-Host "  Stop-Service cloudflared" -ForegroundColor White
    } else {
        Write-Host "❌ Error al instalar el servicio" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host ""
    Write-Host "🚀 Iniciando túnel manualmente..." -ForegroundColor Cyan
    Write-Host "Presiona Ctrl+C para detener" -ForegroundColor Yellow
    Write-Host ""
    
    # Iniciar el túnel
    $configPath = (Resolve-Path "cloudflare-tunnel\config.yml").Path
    cloudflared tunnel --config $configPath run
}

