# Script para hacer docker-compose restart y mostrar la URL del túnel
# Uso: .\docker-compose-restart-with-url.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  REINICIANDO SERVICIOS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Reiniciando servicios..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml restart

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error al reiniciar servicios" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Servicios reiniciados." -ForegroundColor Green
Write-Host "Esperando a que los servicios estén listos..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

Write-Host ""
& .\get-tunnel-url.ps1

