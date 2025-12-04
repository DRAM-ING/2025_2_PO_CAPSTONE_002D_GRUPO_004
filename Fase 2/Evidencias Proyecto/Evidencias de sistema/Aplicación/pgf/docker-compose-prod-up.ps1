# Script para iniciar Docker Compose en modo producción y obtener la URL del túnel
# Uso: .\docker-compose-prod-up.ps1 [-d] [-build] [-stop]
#   -d: Modo detached (en background)
#   -build: Reconstruir imágenes antes de iniciar
#   -stop: Detener servicios antes de iniciar

param(
    [switch]$d,        # Detached mode
    [switch]$build,    # Rebuild images
    [switch]$stop      # Stop services first
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DOCKER COMPOSE - MODO PRODUCCIÓN" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que docker-compose.prod.yml existe
if (-not (Test-Path "docker-compose.prod.yml")) {
    Write-Host "❌ Error: No se encontró docker-compose.prod.yml" -ForegroundColor Red
    exit 1
}

# Verificar que .env.prod existe
if (-not (Test-Path ".env.prod")) {
    Write-Host "⚠️  Advertencia: No se encontró .env.prod" -ForegroundColor Yellow
    Write-Host "   Asegúrate de tener el archivo .env.prod configurado" -ForegroundColor Yellow
    Write-Host ""
}

# Detener servicios si se solicita
if ($stop) {
    Write-Host "Deteniendo servicios existentes..." -ForegroundColor Yellow
    docker-compose -f docker-compose.prod.yml down
    Write-Host "✅ Servicios detenidos" -ForegroundColor Green
    Write-Host ""
}

# Construir imágenes si se solicita
if ($build) {
    Write-Host "🔨 Reconstruyendo imágenes..." -ForegroundColor Yellow
    docker-compose -f docker-compose.prod.yml build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error al reconstruir imágenes" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Imágenes reconstruidas" -ForegroundColor Green
    Write-Host ""
}

# Iniciar servicios
Write-Host "🚀 Iniciando servicios en modo producción..." -ForegroundColor Yellow
Write-Host ""

$composeArgs = @("-f", "docker-compose.prod.yml", "up")

if ($d) {
    $composeArgs += "-d"
    Write-Host "   Modo: Detached (background)" -ForegroundColor Gray
} else {
    Write-Host "   Modo: Interactivo (presiona Ctrl+C para detener)" -ForegroundColor Gray
}

Write-Host ""

if ($d) {
    # Modo detached - iniciar y luego obtener URL
    docker-compose $composeArgs
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "❌ Error al iniciar servicios" -ForegroundColor Red
        Write-Host "   Verifica los logs: docker-compose -f docker-compose.prod.yml logs" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host ""
    Write-Host "✅ Servicios iniciados correctamente" -ForegroundColor Green
    Write-Host ""
    
    # Esperar un poco para que los servicios se inicialicen
    Write-Host "⏳ Esperando a que los servicios estén listos..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Obtener URL del túnel
    Write-Host ""
    & .\get-tunnel-url.ps1
    
    Write-Host ""
    Write-Host "📋 Comandos útiles:" -ForegroundColor Cyan
    Write-Host "   Ver logs: docker-compose -f docker-compose.prod.yml logs -f" -ForegroundColor White
    Write-Host "   Detener: docker-compose -f docker-compose.prod.yml down" -ForegroundColor White
    Write-Host "   Estado: docker-compose -f docker-compose.prod.yml ps" -ForegroundColor White
    Write-Host ""
    
} else {
    # Modo interactivo - iniciar y mostrar logs
    Write-Host "⚠️  NOTA: En modo interactivo, la URL del túnel aparecerá en los logs" -ForegroundColor Yellow
    Write-Host "   Busca líneas que contengan 'https://*.trycloudflare.com'" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Presiona Ctrl+C para detener los servicios" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Iniciar docker-compose (bloquea hasta Ctrl+C)
    docker-compose $composeArgs
    
    if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 130) {
        Write-Host ""
        Write-Host "❌ Error al iniciar servicios" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "✅ Servicios detenidos" -ForegroundColor Green
}

Write-Host ""

