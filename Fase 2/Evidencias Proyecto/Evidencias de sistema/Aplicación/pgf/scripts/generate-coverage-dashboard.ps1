# Script para generar un dashboard HTML consolidado de cobertura
# Uso: .\scripts\generate-coverage-dashboard.ps1

param(
    [switch]$Open = $false
)

Write-Host "========================================" -ForegroundColor Magenta
Write-Host "  PGF - Coverage Dashboard Generator" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

$dashboardDir = "coverage-reports\dashboard"
if (-not (Test-Path $dashboardDir)) {
    New-Item -ItemType Directory -Path $dashboardDir -Force | Out-Null
}

# Recopilar datos de backend desde el JSON de cobertura
$backendData = @{
    modules = @()
    summary = @{
        total_lines = 0
        total_statements = 0
        total_branches = 0
        total_functions = 0
        modules_count = 0
    }
}

$backendJsonPath = "coverage-reports\coverage.json"
if (Test-Path $backendJsonPath) {
    try {
        $coverageJson = Get-Content $backendJsonPath -Raw | ConvertFrom-Json
        
        # pytest-cov genera JSON con estructura específica
        if ($coverageJson.meta -or $coverageJson.totals) {
            $totals = $coverageJson.totals
            
            # Datos generales del backend
            $backendData.summary.total_lines = [math]::Round($totals.percent_covered_lines, 2)
            $backendData.summary.total_statements = [math]::Round($totals.percent_covered, 2)
            $backendData.summary.total_branches = [math]::Round($totals.percent_covered_branches, 2)
            $backendData.summary.total_functions = [math]::Round($totals.percent_covered_functions, 2)
            
            # Extraer datos por módulo desde files
            if ($coverageJson.files) {
                $moduleStats = @{}
                foreach ($fileProp in $coverageJson.files.PSObject.Properties) {
                    $filePath = $fileProp.Name
                    $fileData = $fileProp.Value
                    
                    # Normalizar path (puede ser con / o \)
                    $filePathNormalized = $filePath -replace '/', '\'
                    
                    # Extraer nombre del módulo (primera parte del path después de apps/)
                    if ($filePathNormalized -match "apps[\\/]([^\\/]+)") {
                        $moduleName = $matches[1]
                        
                        if (-not $moduleStats.ContainsKey($moduleName)) {
                            $moduleStats[$moduleName] = @{
                                lines_covered = 0
                                lines_total = 0
                                statements_covered = 0
                                statements_total = 0
                                branches_covered = 0
                                branches_total = 0
                                functions_covered = 0
                                functions_total = 0
                            }
                        }
                        
                        $summary = $fileData.summary
                        if ($summary) {
                            $moduleStats[$moduleName].lines_covered += $summary.covered_lines
                            $moduleStats[$moduleName].lines_total += $summary.num_statements
                            $moduleStats[$moduleName].statements_covered += $summary.covered_lines
                            $moduleStats[$moduleName].statements_total += $summary.num_statements
                            $moduleStats[$moduleName].branches_covered += $summary.covered_branches
                            $moduleStats[$moduleName].branches_total += $summary.num_branches
                            $moduleStats[$moduleName].functions_covered += $summary.covered_functions
                            $moduleStats[$moduleName].functions_total += $summary.num_functions
                        }
                    }
                }
                
                # Calcular porcentajes por módulo
                foreach ($moduleName in $moduleStats.Keys) {
                    $stats = $moduleStats[$moduleName]
                    $moduleData = @{
                        name = $moduleName
                        lines = if ($stats.lines_total -gt 0) { [math]::Round(($stats.lines_covered / $stats.lines_total) * 100, 2) } else { 0 }
                        statements = if ($stats.statements_total -gt 0) { [math]::Round(($stats.statements_covered / $stats.statements_total) * 100, 2) } else { 0 }
                        branches = if ($stats.branches_total -gt 0) { [math]::Round(($stats.branches_covered / $stats.branches_total) * 100, 2) } else { 0 }
                        functions = if ($stats.functions_total -gt 0) { [math]::Round(($stats.functions_covered / $stats.functions_total) * 100, 2) } else { 0 }
                        report_url = "html\index.html"
                    }
                    $backendData.modules += $moduleData
                    $backendData.summary.modules_count++
                }
            }
        } else {
            Write-Host "Formato de JSON de cobertura no reconocido" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Error al leer datos de backend: $_" -ForegroundColor Yellow
        Write-Host "Detalles: $($_.Exception.Message)" -ForegroundColor Yellow
    }
} else {
    Write-Host "No se encontró el archivo de cobertura del backend: $backendJsonPath" -ForegroundColor Yellow
    Write-Host "Ejecuta primero: .\scripts\coverage-backend.ps1 -All" -ForegroundColor Yellow
}

# Recopilar datos de frontend
$frontendData = $null
$frontendCoveragePath = "coverage-reports\frontend\coverage-final.json"
if (Test-Path $frontendCoveragePath) {
    $frontendCoverage = Get-Content $frontendCoveragePath | ConvertFrom-Json
    $frontendTotal = $frontendCoverage.total
    
    $frontendData = @{
        lines = [math]::Round($frontendTotal.lines.pct, 2)
        statements = [math]::Round($frontendTotal.statements.pct, 2)
        branches = [math]::Round($frontendTotal.branches.pct, 2)
        functions = [math]::Round($frontendTotal.functions.pct, 2)
        report_url = "frontend\index.html"
    }
}

# Generar HTML del dashboard
$html = @"
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PGF - Coverage Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 {
            color: #003DA5;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header p {
            color: #666;
            font-size: 1.1em;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .card h2 {
            color: #003DA5;
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 0;
            border-bottom: 1px solid #eee;
        }
        .metric:last-child {
            border-bottom: none;
        }
        .metric-label {
            font-weight: 600;
            color: #333;
        }
        .metric-value {
            font-size: 1.3em;
            font-weight: bold;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 10px;
        }
        .progress-fill {
            height: 100%;
            transition: width 0.3s ease;
            border-radius: 10px;
        }
        .high { background: #4caf50; }
        .medium { background: #ff9800; }
        .low { background: #f44336; }
        .module-item {
            padding: 15px;
            margin: 10px 0;
            background: #f5f5f5;
            border-radius: 8px;
            border-left: 4px solid #003DA5;
        }
        .module-item h3 {
            color: #003DA5;
            margin-bottom: 10px;
        }
        .module-metrics {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-top: 10px;
        }
        .module-metric {
            font-size: 0.9em;
        }
        .module-link {
            display: inline-block;
            margin-top: 10px;
            padding: 8px 16px;
            background: #003DA5;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-size: 0.9em;
        }
        .module-link:hover {
            background: #002D7A;
        }
        .timestamp {
            text-align: center;
            color: #666;
            margin-top: 20px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 PGF Coverage Dashboard</h1>
            <p>Reporte consolidado de cobertura de código - Backend y Frontend</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>🎯 Backend Summary</h2>
                <a href="../html/index.html" class="module-link" target="_blank" style="margin-bottom: 15px; display: inline-block;">Ver Reporte Completo →</a>
                <div class="metric">
                    <span class="metric-label">Líneas</span>
                    <span class="metric-value">$($backendData.summary.total_lines)%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill $(if($backendData.summary.total_lines -ge 80){'high'}elseif($backendData.summary.total_lines -ge 60){'medium'}else{'low'})" style="width: $($backendData.summary.total_lines)%"></div>
                </div>
                <div class="metric">
                    <span class="metric-label">Declaraciones</span>
                    <span class="metric-value">$($backendData.summary.total_statements)%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill $(if($backendData.summary.total_statements -ge 80){'high'}elseif($backendData.summary.total_statements -ge 60){'medium'}else{'low'})" style="width: $($backendData.summary.total_statements)%"></div>
                </div>
                <div class="metric">
                    <span class="metric-label">Ramas</span>
                    <span class="metric-value">$($backendData.summary.total_branches)%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill $(if($backendData.summary.total_branches -ge 80){'high'}elseif($backendData.summary.total_branches -ge 60){'medium'}else{'low'})" style="width: $($backendData.summary.total_branches)%"></div>
                </div>
                <div class="metric">
                    <span class="metric-label">Funciones</span>
                    <span class="metric-value">$($backendData.summary.total_functions)%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill $(if($backendData.summary.total_functions -ge 80){'high'}elseif($backendData.summary.total_functions -ge 60){'medium'}else{'low'})" style="width: $($backendData.summary.total_functions)%"></div>
                </div>
            </div>
            
            $(if ($frontendData) {
                @"
            <div class="card">
                <h2>🎨 Frontend Summary</h2>
                <div class="metric">
                    <span class="metric-label">Líneas</span>
                    <span class="metric-value">$($frontendData.lines)%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill $(if($frontendData.lines -ge 80){'high'}elseif($frontendData.lines -ge 60){'medium'}else{'low'})" style="width: $($frontendData.lines)%"></div>
                </div>
                <div class="metric">
                    <span class="metric-label">Declaraciones</span>
                    <span class="metric-value">$($frontendData.statements)%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill $(if($frontendData.statements -ge 80){'high'}elseif($frontendData.statements -ge 60){'medium'}else{'low'})" style="width: $($frontendData.statements)%"></div>
                </div>
                <div class="metric">
                    <span class="metric-label">Ramas</span>
                    <span class="metric-value">$($frontendData.branches)%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill $(if($frontendData.branches -ge 80){'high'}elseif($frontendData.branches -ge 60){'medium'}else{'low'})" style="width: $($frontendData.branches)%"></div>
                </div>
                <div class="metric">
                    <span class="metric-label">Funciones</span>
                    <span class="metric-value">$($frontendData.functions)%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill $(if($frontendData.functions -ge 80){'high'}elseif($frontendData.functions -ge 60){'medium'}else{'low'})" style="width: $($frontendData.functions)%"></div>
                </div>
                <a href="../frontend/index.html" class="module-link" target="_blank">Ver Reporte Completo →</a>
            </div>
"@
            })
        </div>
        
        <div class="card">
            <h2>📦 Módulos del Backend</h2>
            <a href="../html/index.html" class="module-link" target="_blank" style="margin-bottom: 20px; display: inline-block;">Ver Reporte Completo del Backend →</a>
            $(if ($backendData.modules.Count -eq 0) {
                "<p style='color: #666; padding: 20px; text-align: center;'>No hay datos de módulos disponibles. Ejecuta primero los scripts de cobertura.</p>"
            } else {
                $backendData.modules | ForEach-Object {
                    $module = $_
                    $avg = ($module.lines + $module.statements + $module.branches + $module.functions) / 4
                    @"
            <div class="module-item">
                <h3>$($module.name)</h3>
                <div class="module-metrics">
                    <div class="module-metric"><strong>Líneas:</strong> $($module.lines)%</div>
                    <div class="module-metric"><strong>Declaraciones:</strong> $($module.statements)%</div>
                    <div class="module-metric"><strong>Ramas:</strong> $($module.branches)%</div>
                    <div class="module-metric"><strong>Funciones:</strong> $($module.functions)%</div>
                </div>
                <div class="progress-bar" style="margin-top: 10px;">
                    <div class="progress-fill $(if($avg -ge 80){'high'}elseif($avg -ge 60){'medium'}else{'low'})" style="width: $avg%"></div>
                </div>
            </div>
"@
                } | Out-String
            })
        </div>
        
        <div class="timestamp">
            Generado el $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        </div>
    </div>
</body>
</html>
"@

$htmlPath = "$dashboardDir\index.html"
$html | Set-Content $htmlPath -Encoding UTF8

Write-Host "Dashboard generado exitosamente!" -ForegroundColor Green
Write-Host "Ubicación: $htmlPath" -ForegroundColor Cyan

if ($Open) {
    Start-Process $htmlPath
}

