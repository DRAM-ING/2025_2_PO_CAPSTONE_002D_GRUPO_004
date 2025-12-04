# Script para obtener la URL del túnel de Cloudflare
# Uso: .\get-tunnel-url.ps1

Write-Host "Esperando a que el túnel de Cloudflare esté listo..." -ForegroundColor Yellow

$maxAttempts = 60  # 2 minutos máximo
$attempt = 0
$url = $null

while ($attempt -lt $maxAttempts -and -not $url) {
    Start-Sleep -Seconds 2
    $attempt++
    
    # Buscar la URL en los logs del túnel
    # El patrón en los logs es: "INF |  https://nombre.trycloudflare.com"
    $logs = docker-compose -f docker-compose.prod.yml logs tunnel 2>&1 | Select-String -Pattern "https://.*\.trycloudflare\.com"
    
    if ($logs) {
        # Extraer la última URL encontrada (la más reciente)
        $lastLine = $logs | Select-Object -Last 1
        
        # El formato puede ser: "INF |  https://nombre.trycloudflare.com" o solo "https://nombre.trycloudflare.com"
        if ($lastLine -match "https://([a-z0-9-]+)\.trycloudflare\.com") {
            $url = $matches[0]
            break
        }
    }
    
    Write-Host "." -NoNewline -ForegroundColor Gray
}

Write-Host ""

if ($url) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  URL DEL TÚNEL CLOUDFLARE" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  $url" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    # Guardar en variable de entorno para uso posterior
    $env:CLOUDFLARE_TUNNEL_URL = $url
    Write-Host "URL guardada en variable de entorno: CLOUDFLARE_TUNNEL_URL" -ForegroundColor Gray
    Write-Host ""
    
    # También guardar en un archivo para referencia
    $url | Out-File -FilePath ".tunnel-url.txt" -Encoding utf8 -NoNewline
    Write-Host "URL guardada en archivo: .tunnel-url.txt" -ForegroundColor Gray
    Write-Host ""
    
    return $url
} else {
    Write-Host ""
    Write-Host "No se pudo obtener la URL del túnel después de $($maxAttempts * 2) segundos" -ForegroundColor Red
    Write-Host "Verifica que el túnel esté corriendo: docker-compose -f docker-compose.prod.yml ps tunnel" -ForegroundColor Yellow
    Write-Host "Ver logs: docker-compose -f docker-compose.prod.yml logs tunnel | Select-String 'trycloudflare'" -ForegroundColor Yellow
    return $null
}

