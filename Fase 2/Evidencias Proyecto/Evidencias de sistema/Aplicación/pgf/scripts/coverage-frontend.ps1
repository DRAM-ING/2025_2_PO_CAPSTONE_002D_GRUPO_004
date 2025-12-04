# Script para generar reporte de cobertura del frontend (vitest)
# Uso: .\scripts\coverage-frontend.ps1 [--open] [--ui] [--watch]

param(
    [switch]$Open = $false,
    [switch]$Watch = $false,
    [switch]$UI = $false
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PGF - Frontend Coverage Report (Vitest)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$frontendPath = "frontend\pgf-frontend"

if (-not (Test-Path $frontendPath)) {
    Write-Host "Error: No se encuentra el directorio frontend/pgf-frontend" -ForegroundColor Red
    exit 1
}

Push-Location $frontendPath

# Verificar que node_modules existe
if (-not (Test-Path "node_modules")) {
    Write-Host "Instalando dependencias..." -ForegroundColor Yellow
    npm install
}

# Verificar que Vitest está instalado
$vitestInstalled = npm list vitest 2>&1 | Select-String "vitest@"
if (-not $vitestInstalled) {
    Write-Host "Instalando Vitest y dependencias..." -ForegroundColor Yellow
    npm install -D vitest @vitest/ui @vitest/coverage-v8 @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom @vitejs/plugin-react
}

# Crear directorio para reportes
$reportDir = "..\..\coverage-reports\frontend"
if (-not (Test-Path $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
}

if ($UI) {
    Write-Host "Abriendo dashboard interactivo de Vitest..." -ForegroundColor Green
    Write-Host "El dashboard se abrirá automáticamente en tu navegador" -ForegroundColor Yellow
    Write-Host "Presiona Ctrl+C para cerrar el dashboard" -ForegroundColor Yellow
    npm run test:ui
} elseif ($Watch) {
    Write-Host "Ejecutando tests en modo watch..." -ForegroundColor Green
    npm run test:watch
} else {
    Write-Host "Ejecutando tests con cobertura..." -ForegroundColor Green
    npm run test:coverage
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  Coverage report generado exitosamente" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Reportes generados en:" -ForegroundColor Yellow
        Write-Host "  - HTML: coverage\index.html" -ForegroundColor Cyan
        Write-Host "  - JSON: coverage\coverage-final.json" -ForegroundColor Cyan
        Write-Host "  - LCOV: coverage\lcov.info" -ForegroundColor Cyan
        
        # Copiar reportes al directorio centralizado
        if (Test-Path "coverage") {
            Copy-Item -Path "coverage\*" -Destination $reportDir -Recurse -Force
            Write-Host "  - Reportes copiados a: $reportDir" -ForegroundColor Cyan
        }
        
        if ($Open) {
            if (Test-Path "coverage\index.html") {
                Start-Process "coverage\index.html"
            } elseif (Test-Path "$reportDir\index.html") {
                Start-Process "$reportDir\index.html"
            }
        }
    } else {
        Write-Host ""
        Write-Host "Error al ejecutar los tests" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

Pop-Location

