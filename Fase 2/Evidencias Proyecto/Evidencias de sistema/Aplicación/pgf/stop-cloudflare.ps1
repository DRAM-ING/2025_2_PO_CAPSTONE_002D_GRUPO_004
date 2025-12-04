# Script para detener Cloudflare Tunnel

Write-Host "🛑 Deteniendo Cloudflare Tunnel..." -ForegroundColor Yellow
Write-Host ""

# Verificar si está corriendo como servicio
$service = Get-Service cloudflared -ErrorAction SilentlyContinue

if ($service) {
    if ($service.Status -eq "Running") {
        Write-Host "Deteniendo servicio cloudflared..." -ForegroundColor Cyan
        Stop-Service cloudflared
        Write-Host "✅ Servicio detenido" -ForegroundColor Green
    } else {
        Write-Host "⚠️  El servicio cloudflared no está corriendo" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  El servicio cloudflared no está instalado" -ForegroundColor Yellow
    Write-Host "Si está corriendo manualmente, presiona Ctrl+C en la ventana donde lo iniciaste" -ForegroundColor Yellow
}

Write-Host ""

