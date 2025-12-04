# Script para generar reporte de cobertura de un módulo específico del backend usando Docker
# Uso: .\scripts\coverage-backend-module.ps1 -Module workorders [--open]

param(
    [Parameter(Mandatory=$true)]
    [string]$Module,
    [switch]$Open = $false
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PGF - Backend Coverage: $Module" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que Docker está corriendo
$dockerRunning = docker ps 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Docker no está corriendo. Por favor inicia Docker Desktop." -ForegroundColor Red
    exit 1
}

# Verificar que el contenedor api está corriendo
$apiContainer = docker-compose ps api 2>&1 | Select-String "Up"
if (-not $apiContainer) {
    Write-Host "El contenedor 'api' no está corriendo. Iniciando contenedores..." -ForegroundColor Yellow
    docker-compose up -d api
    Start-Sleep -Seconds 5
}

# Asegurar que las dependencias de desarrollo están instaladas
Write-Host "Verificando dependencias de desarrollo en el contenedor..." -ForegroundColor Yellow
docker-compose exec -T api poetry install --no-interaction --no-root 2>&1 | Out-Null

# Verificar que el módulo existe
$modulePath = "apps\$Module"
if (-not (Test-Path $modulePath)) {
    Write-Host "Error: El módulo '$Module' no existe en apps/" -ForegroundColor Red
    Write-Host "Módulos disponibles:" -ForegroundColor Yellow
    Get-ChildItem -Path apps -Directory | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Cyan }
    exit 1
}

# Crear directorio para reportes
$reportDir = "coverage-reports\modules\$Module"
if (-not (Test-Path $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
}

# Crear subdirectorio html si no existe
$htmlDir = "$reportDir\html"
if (-not (Test-Path $htmlDir)) {
    New-Item -ItemType Directory -Path $htmlDir -Force | Out-Null
}

Write-Host "Ejecutando tests del módulo: $Module en Docker..." -ForegroundColor Green
Write-Host "Ruta: $modulePath" -ForegroundColor Gray
Write-Host ""

# Ejecutar pytest con cobertura específica del módulo dentro del contenedor Docker
# Nota: Sobrescribimos --cov-fail-under porque cuando se ejecuta por módulo,
# pytest calcula la cobertura de todos los módulos, no solo del módulo específico
docker-compose exec -T api poetry run pytest `
    "apps/$Module" `
    --cov="apps.$Module" `
    --cov-report=html:/app/coverage-reports/modules/$Module/html `
    --cov-report=xml:/app/coverage-reports/modules/$Module/coverage.xml `
    --cov-report=json:/app/coverage-reports/modules/$Module/coverage.json `
    --cov-report=term-missing `
    --cov-report=lcov:/app/coverage-reports/modules/$Module/coverage.lcov `
    --cov-fail-under=0 `
    -v

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Coverage report generado exitosamente" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    # Los reportes ya están en el volumen compartido, solo verificar que existan
    Write-Host "Reportes generados en:" -ForegroundColor Yellow
    $htmlPath = "$reportDir\html\index.html"
    $xmlPath = "$reportDir\coverage.xml"
    $jsonPath = "$reportDir\coverage.json"
    $lcovPath = "$reportDir\coverage.lcov"
    
    Write-Host "  - HTML: $htmlPath" -ForegroundColor Cyan
    Write-Host "  - XML:  $xmlPath" -ForegroundColor Cyan
    Write-Host "  - JSON: $jsonPath" -ForegroundColor Cyan
    Write-Host "  - LCOV: $lcovPath" -ForegroundColor Cyan
    
    if ($Open -and (Test-Path $htmlPath)) {
        Start-Process $htmlPath
    }
} else {
    Write-Host ""
    Write-Host "Error al ejecutar los tests" -ForegroundColor Red
    exit $LASTEXITCODE
}

