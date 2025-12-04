# Script para hacer docker-compose up y mostrar la URL del túnel automáticamente
# Uso: .\docker-compose-up-with-url.ps1 [-d] [-build]
#   -d: Modo detached (en background)
#   -build: Reconstruir imágenes

param(
    [switch]$d,  # Detached mode
    [switch]$build  # Rebuild images
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INICIANDO SERVICIOS DOCKER COMPOSE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Construir comando docker-compose
$composeArgs = @("-f", "docker-compose.prod.yml")
if ($build) {
    $composeArgs += "--build"
}
$composeArgs += "up"

if ($d) {
    $composeArgs += "-d"
}

# Ejecutar docker-compose
if ($d) {
    # Modo detached - ejecutar y luego obtener URL
    Write-Host "Iniciando servicios en modo detached..." -ForegroundColor Yellow
    docker-compose $composeArgs
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error al iniciar servicios" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "Servicios iniciados." -ForegroundColor Green
    Write-Host ""
    
    # Obtener URL del túnel
    & .\get-tunnel-url.ps1
} else {
    # Modo interactivo - ejecutar en background y mostrar URL cuando esté lista
    Write-Host "Iniciando servicios..." -ForegroundColor Yellow
    
    # Iniciar docker-compose en background
    $job = Start-Job -ScriptBlock {
        param($composeArgs)
        docker-compose $composeArgs 2>&1
    } -ArgumentList $composeArgs
    
    # Esperar un poco para que los servicios se inicien
    Start-Sleep -Seconds 8
    
    # Obtener URL del túnel en paralelo
    Write-Host ""
    & .\get-tunnel-url.ps1
    
    # Mostrar logs de docker-compose
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  LOGS DE DOCKER COMPOSE" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Presiona Ctrl+C para detener los servicios" -ForegroundColor Yellow
    Write-Host ""
    
    # Esperar a que termine docker-compose o mostrar logs
    while ($job.State -eq "Running") {
        $output = Receive-Job $job -ErrorAction SilentlyContinue
        if ($output) {
            Write-Host $output
        }
        Start-Sleep -Seconds 1
    }
    
    # Obtener salida final
    $finalOutput = Receive-Job $job
    if ($finalOutput) {
        Write-Host $finalOutput
    }
    Remove-Job $job
}

