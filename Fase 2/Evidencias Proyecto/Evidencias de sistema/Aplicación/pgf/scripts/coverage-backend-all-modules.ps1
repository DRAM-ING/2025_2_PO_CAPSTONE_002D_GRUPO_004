# Script para generar reportes de cobertura de todos los módulos del backend
# Uso: .\scripts\coverage-backend-all-modules.ps1 [--open]

param(
    [switch]$Open = $false
)

Write-Host "========================================" -ForegroundColor Magenta
Write-Host "  PGF - Backend Coverage: All Modules" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

# Obtener todos los módulos
$modules = Get-ChildItem -Path apps -Directory | Where-Object { 
    $_.Name -ne "__pycache__" -and 
    (Test-Path "$($_.FullName)\tests") -or 
    (Get-ChildItem -Path $_.FullName -Filter "test_*.py" -Recurse -ErrorAction SilentlyContinue)
} | Select-Object -ExpandProperty Name

if ($modules.Count -eq 0) {
    Write-Host "No se encontraron módulos con tests" -ForegroundColor Yellow
    exit 0
}

Write-Host "Módulos encontrados: $($modules -join ', ')" -ForegroundColor Cyan
Write-Host ""

$reportDir = "coverage-reports\modules"
if (-not (Test-Path $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
}

$results = @()

foreach ($module in $modules) {
    Write-Host "Procesando módulo: $module" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Gray
    
    & ".\scripts\coverage-backend-module.ps1" -Module $module
    
    if ($LASTEXITCODE -eq 0) {
        # Leer el reporte JSON para obtener el porcentaje de cobertura
        $jsonPath = "$reportDir\$module\coverage.json"
        if (Test-Path $jsonPath) {
            $coverage = Get-Content $jsonPath | ConvertFrom-Json
            $total = $coverage.totals
            $results += [PSCustomObject]@{
                Module = $module
                Lines = $total.percent_covered_lines
                Statements = $total.percent_covered
                Branches = $total.percent_covered_branches
                Functions = $total.percent_covered_functions
            }
        }
    }
    
    Write-Host ""
}

# Generar resumen
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Resumen de Cobertura" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

if ($results.Count -gt 0) {
    $results | Format-Table -AutoSize
    
    # Calcular promedio
    $avgLines = ($results | Measure-Object -Property Lines -Average).Average
    $avgStatements = ($results | Measure-Object -Property Statements -Average).Average
    $avgBranches = ($results | Measure-Object -Property Branches -Average).Average
    $avgFunctions = ($results | Measure-Object -Property Functions -Average).Average
    
    Write-Host ""
    Write-Host "Promedio General:" -ForegroundColor Cyan
    Write-Host "  Líneas:      $([math]::Round($avgLines, 2))%" -ForegroundColor White
    Write-Host "  Declaraciones: $([math]::Round($avgStatements, 2))%" -ForegroundColor White
    Write-Host "  Ramas:        $([math]::Round($avgBranches, 2))%" -ForegroundColor White
    Write-Host "  Funciones:    $([math]::Round($avgFunctions, 2))%" -ForegroundColor White
    
    # Guardar resumen en JSON
    $summaryPath = "$reportDir\summary.json"
    $results | ConvertTo-Json -Depth 10 | Set-Content $summaryPath
    Write-Host ""
    Write-Host "Resumen guardado en: $summaryPath" -ForegroundColor Cyan
}

if ($Open) {
    Write-Host ""
    Write-Host "Abriendo reportes..." -ForegroundColor Yellow
    foreach ($module in $modules) {
        $htmlPath = "$reportDir\$module\html\index.html"
        if (Test-Path $htmlPath) {
            Start-Process $htmlPath
            Start-Sleep -Seconds 1
        }
    }
}

