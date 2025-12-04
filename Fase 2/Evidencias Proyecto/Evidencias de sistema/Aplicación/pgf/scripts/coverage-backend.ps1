# Script para generar reporte de cobertura del backend (pytest) usando Docker
# Uso: .\scripts\coverage-backend.ps1 [modulo]
# Ejemplo: .\scripts\coverage-backend.ps1 workorders

param(
    [string]$Module = "",
    [switch]$Open = $false,
    [switch]$All = $false
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PGF - Backend Coverage Report (Docker)" -ForegroundColor Cyan
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

# Crear directorio para reportes (tanto en host como en contenedor)
$reportDir = "coverage-reports"
if (-not (Test-Path $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir | Out-Null
}

# Crear subdirectorio html si no existe
$htmlDir = "$reportDir\html"
if (-not (Test-Path $htmlDir)) {
    New-Item -ItemType Directory -Path $htmlDir | Out-Null
}

# Ejecutar tests dentro del contenedor Docker
if ($All) {
    Write-Host "Ejecutando tests de todos los módulos en Docker..." -ForegroundColor Green
    docker-compose exec -T api poetry run pytest `
        --cov=apps `
        --cov-report=html:/app/coverage-reports/html `
        --cov-report=xml:/app/coverage-reports/coverage.xml `
        --cov-report=json:/app/coverage-reports/coverage.json `
        --cov-report=term-missing
} elseif ($Module) {
    Write-Host "Ejecutando tests del módulo: $Module en Docker..." -ForegroundColor Green
    $modulePath = "apps\$Module"
    if (-not (Test-Path $modulePath)) {
        Write-Host "Error: El módulo '$Module' no existe en apps/" -ForegroundColor Red
        exit 1
    }
    docker-compose exec -T api poetry run pytest `
        "apps/$Module" `
        --cov="apps.$Module" `
        --cov-report=html:/app/coverage-reports/html-$Module `
        --cov-report=xml:/app/coverage-reports/coverage-$Module.xml `
        --cov-report=json:/app/coverage-reports/coverage-$Module.json `
        --cov-report=term-missing
} else {
    Write-Host "Ejecutando tests de todos los módulos en Docker..." -ForegroundColor Green
    docker-compose exec -T api poetry run pytest `
        --cov=apps `
        --cov-report=html:/app/coverage-reports/html `
        --cov-report=xml:/app/coverage-reports/coverage.xml `
        --cov-report=json:/app/coverage-reports/coverage.json `
        --cov-report=term-missing
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Coverage report generado exitosamente" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    # Los reportes ya están en el volumen compartido, solo verificar que existan
    Write-Host "Reportes generados en:" -ForegroundColor Yellow
    if ($Module) {
        $htmlPath = "$reportDir\html-$Module\index.html"
        $xmlPath = "$reportDir\coverage-$Module.xml"
        $jsonPath = "$reportDir\coverage-$Module.json"
        
        Write-Host "  - HTML: $htmlPath" -ForegroundColor Cyan
        Write-Host "  - XML:  $xmlPath" -ForegroundColor Cyan
        Write-Host "  - JSON: $jsonPath" -ForegroundColor Cyan
        
        if ($Open -and (Test-Path $htmlPath)) {
            Start-Process $htmlPath
        }
    } else {
        $htmlPath = "$reportDir\html\index.html"
        $xmlPath = "$reportDir\coverage.xml"
        $jsonPath = "$reportDir\coverage.json"
        
        Write-Host "  - HTML: $htmlPath" -ForegroundColor Cyan
        Write-Host "  - XML:  $xmlPath" -ForegroundColor Cyan
        Write-Host "  - JSON: $jsonPath" -ForegroundColor Cyan
        
        if ($Open -and (Test-Path $htmlPath)) {
            Start-Process $htmlPath
        }
    }
} else {
    Write-Host ""
    Write-Host "Error al ejecutar los tests" -ForegroundColor Red
    exit $LASTEXITCODE
}

