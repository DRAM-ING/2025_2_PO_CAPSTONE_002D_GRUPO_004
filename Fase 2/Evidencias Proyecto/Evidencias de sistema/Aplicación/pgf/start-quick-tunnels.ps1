# Script para iniciar Quick Tunnels de Cloudflare
# Este script inicia dos túneles: uno para el frontend y otro para la API

Write-Host "🚀 Iniciando Cloudflare Quick Tunnels..." -ForegroundColor Green
Write-Host ""

# Verificar que cloudflared está instalado
$cloudflaredPath = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cloudflaredPath) {
    Write-Host "❌ Error: cloudflared no está instalado" -ForegroundColor Red
    Write-Host "Ejecuta primero: .\setup-cloudflare.ps1" -ForegroundColor Yellow
    exit 1
}

# Verificar que Docker esté corriendo
$dockerRunning = docker ps 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Advertencia: Docker no parece estar corriendo" -ForegroundColor Yellow
    Write-Host "Asegúrate de que Docker Desktop esté iniciado" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "📋 Este script iniciará dos túneles:" -ForegroundColor Cyan
Write-Host "   1. Frontend (puerto 3000)" -ForegroundColor White
Write-Host "   2. API (puerto 8000)" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  IMPORTANTE:" -ForegroundColor Yellow
Write-Host "   - Las URLs cambiarán cada vez que reinicies los túneles" -ForegroundColor Yellow
Write-Host "   - Anota las URLs que te da Cloudflare" -ForegroundColor Yellow
Write-Host "   - Actualiza .env con las nuevas URLs" -ForegroundColor Yellow
Write-Host ""

$response = Read-Host "¿Deseas continuar? (s/n)"
if ($response -ne "s" -and $response -ne "S") {
    Write-Host "Operación cancelada." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "🌐 Iniciando túnel para Frontend (puerto 3000)..." -ForegroundColor Cyan
Write-Host "   Abre otra terminal y ejecuta:" -ForegroundColor Yellow
Write-Host "   cloudflared tunnel --url http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "   O ejecuta este script dos veces en terminales diferentes" -ForegroundColor Yellow
Write-Host ""

# Iniciar túnel para frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host '🌐 Túnel Frontend (puerto 3000)' -ForegroundColor Green; Write-Host 'Anota la URL que aparece abajo:' -ForegroundColor Yellow; Write-Host ''; cloudflared tunnel --url http://localhost:3000"

Write-Host "✅ Túnel de Frontend iniciado en nueva ventana" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Próximos pasos:" -ForegroundColor Cyan
Write-Host "   1. Anota la URL del túnel de Frontend (aparece en la nueva ventana)" -ForegroundColor White
Write-Host "   2. Abre otra terminal PowerShell" -ForegroundColor White
Write-Host "   3. Ejecuta: cloudflared tunnel --url http://localhost:8000" -ForegroundColor White
Write-Host "   4. Anota la URL del túnel de API" -ForegroundColor White
Write-Host "   5. Actualiza .env con ambas URLs" -ForegroundColor White
Write-Host "   6. Reinicia Docker: docker-compose restart" -ForegroundColor White
Write-Host ""

