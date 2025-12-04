# Script para generar reportes de cobertura de backend y frontend
# Uso: .\scripts\coverage-all.ps1 [--open]

param(
    [switch]$Open = $false
)

Write-Host "========================================" -ForegroundColor Magenta
Write-Host "  PGF - Full Coverage Report" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

# Crear directorio para reportes consolidados
$reportDir = "coverage-reports"
if (-not (Test-Path $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir | Out-Null
}

# Ejecutar cobertura del backend
Write-Host "1. Ejecutando cobertura del backend..." -ForegroundColor Yellow
& ".\scripts\coverage-backend.ps1" -All

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error en la cobertura del backend" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "2. Ejecutando cobertura del frontend..." -ForegroundColor Yellow
if ($Open) {
    & ".\scripts\coverage-frontend.ps1" -Open
} else {
    & ".\scripts\coverage-frontend.ps1"
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error en la cobertura del frontend" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "3. Generando dashboard consolidado..." -ForegroundColor Yellow
& ".\scripts\generate-coverage-dashboard.ps1"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Reportes de cobertura completados" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Reportes disponibles en:" -ForegroundColor Yellow
Write-Host "  - Dashboard: $reportDir\dashboard\index.html" -ForegroundColor Cyan
Write-Host "  - Backend HTML: $reportDir\html\index.html" -ForegroundColor Cyan
Write-Host "  - Frontend HTML: $reportDir\frontend\index.html" -ForegroundColor Cyan
Write-Host "  - Backend XML:  $reportDir\coverage.xml" -ForegroundColor Cyan
Write-Host "  - Backend JSON: $reportDir\coverage.json" -ForegroundColor Cyan

if ($Open) {
    Write-Host ""
    Write-Host "Abriendo dashboard..." -ForegroundColor Yellow
    if (Test-Path "$reportDir\dashboard\index.html") {
        Start-Process "$reportDir\dashboard\index.html"
    } elseif (Test-Path "$reportDir\html\index.html") {
        Start-Process "$reportDir\html\index.html"
    }
    Start-Sleep -Seconds 2
    if (Test-Path "$reportDir\frontend\index.html") {
        Start-Process "$reportDir\frontend\index.html"
    }
}

