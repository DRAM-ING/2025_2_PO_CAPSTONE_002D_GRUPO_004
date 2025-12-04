# Script para generar un reporte HTML visual de cobertura del backend
# Uso: .\scripts\generate-backend-coverage-report.ps1 [--open]

param(
    [switch]$Open = $false
)

Write-Host "========================================" -ForegroundColor Magenta
Write-Host "  PGF - Backend Coverage Report Generator" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

$reportDir = "coverage-reports"
$outputDir = "$reportDir\dashboard"
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

# Leer reporte principal
$mainReport = $null
$mainReportPath = "$reportDir\coverage.json"
if (Test-Path $mainReportPath) {
    try {
        $jsonContent = Get-Content $mainReportPath -Raw -ErrorAction Stop -Encoding UTF8
        $mainReport = $jsonContent | ConvertFrom-Json -ErrorAction Stop
        if ($mainReport) {
            Write-Host "[OK] Reporte principal cargado" -ForegroundColor Green
        } else {
            Write-Host "[WARN] El reporte principal esta vacio" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[WARN] Error al leer reporte principal: $($_.Exception.Message)" -ForegroundColor Yellow
    }
} else {
    Write-Host "[WARN] No se encontro el reporte principal en: $mainReportPath" -ForegroundColor Yellow
}

# Leer reportes por módulo
$moduleReports = @{}
$modulesDir = "$reportDir\modules"
if (Test-Path $modulesDir) {
    $modules = Get-ChildItem -Path $modulesDir -Directory -ErrorAction SilentlyContinue
    if ($modules) {
        foreach ($module in $modules) {
            $moduleJsonPath = Join-Path $module.FullName "coverage.json"
            if (Test-Path $moduleJsonPath) {
                try {
                $jsonContent = Get-Content $moduleJsonPath -Raw -ErrorAction Stop -Encoding UTF8
                $moduleData = $jsonContent | ConvertFrom-Json -ErrorAction Stop
                if ($moduleData) {
                    $moduleReports[$module.Name] = $moduleData
                    Write-Host "[OK] Modulo $($module.Name) cargado" -ForegroundColor Green
                } else {
                    Write-Host "[WARN] El modulo $($module.Name) esta vacio" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "[WARN] Error al leer modulo $($module.Name): $($_.Exception.Message)" -ForegroundColor Yellow
            }
            }
        }
    }
} else {
    Write-Host "[WARN] No se encontro el directorio de modulos: $modulesDir" -ForegroundColor Yellow
}

# Extraer datos del reporte principal
$totalCoverage = @{
    lines = 0
    statements = 0
    branches = 0
    functions = 0
    covered_lines = 0
    total_lines = 0
    covered_statements = 0
    total_statements = 0
}

if ($mainReport) {
    if ($mainReport.PSObject.Properties.Name -contains 'totals') {
        $totals = $mainReport.totals
        if ($totals) {
            if ($totals.PSObject.Properties.Name -contains 'percent_covered_lines') {
                $totalCoverage.lines = [math]::Round($totals.percent_covered_lines, 2)
            }
            if ($totals.PSObject.Properties.Name -contains 'percent_covered') {
                $totalCoverage.statements = [math]::Round($totals.percent_covered, 2)
            }
            if ($totals.PSObject.Properties.Name -contains 'percent_covered_branches') {
                $totalCoverage.branches = [math]::Round($totals.percent_covered_branches, 2)
            }
            if ($totals.PSObject.Properties.Name -contains 'percent_covered_functions') {
                $totalCoverage.functions = [math]::Round($totals.percent_covered_functions, 2)
            }
            if ($totals.PSObject.Properties.Name -contains 'covered_lines') {
                $totalCoverage.covered_lines = $totals.covered_lines
            }
            if ($totals.PSObject.Properties.Name -contains 'num_statements') {
                $totalCoverage.total_lines = $totals.num_statements
                $totalCoverage.total_statements = $totals.num_statements
                $totalCoverage.covered_statements = $totals.covered_lines
            }
        }
    }
}

# Extraer datos por módulo
$moduleData = @()
foreach ($moduleName in $moduleReports.Keys) {
    $moduleReport = $moduleReports[$moduleName]
    if ($moduleReport -and $moduleReport.PSObject.Properties.Name -contains 'totals') {
        $totals = $moduleReport.totals
        if ($totals) {
            $branches = 0
            $functions = 0
            $lines = 0
            $statements = 0
            $coveredLines = 0
            $totalLines = 0
            
            if ($totals.PSObject.Properties.Name -contains 'percent_covered_lines') {
                $lines = [math]::Round($totals.percent_covered_lines, 2)
            }
            if ($totals.PSObject.Properties.Name -contains 'percent_covered') {
                $statements = [math]::Round($totals.percent_covered, 2)
            }
            if ($totals.PSObject.Properties.Name -contains 'percent_covered_branches') {
                $branches = [math]::Round($totals.percent_covered_branches, 2)
            }
            if ($totals.PSObject.Properties.Name -contains 'percent_covered_functions') {
                $functions = [math]::Round($totals.percent_covered_functions, 2)
            }
            if ($totals.PSObject.Properties.Name -contains 'covered_lines') {
                $coveredLines = $totals.covered_lines
            }
            if ($totals.PSObject.Properties.Name -contains 'num_statements') {
                $totalLines = $totals.num_statements
            }
            
            $moduleData += [PSCustomObject]@{
                Name = $moduleName
                Lines = $lines
                Statements = $statements
                Branches = $branches
                Functions = $functions
                CoveredLines = $coveredLines
                TotalLines = $totalLines
                ReportUrl = "../modules/$moduleName/html/index.html"
            }
        }
    }
}

# Ordenar módulos por cobertura de líneas (descendente)
$moduleData = $moduleData | Sort-Object -Property Lines -Descending

# Calcular clases CSS para las tarjetas de resumen
$linesClass = if ($totalCoverage.lines -ge 80) { "high" } elseif ($totalCoverage.lines -ge 60) { "medium" } else { "low" }
$statementsClass = if ($totalCoverage.statements -ge 80) { "high" } elseif ($totalCoverage.statements -ge 60) { "medium" } else { "low" }
$branchesClass = if ($totalCoverage.branches -ge 80) { "high" } elseif ($totalCoverage.branches -ge 60) { "medium" } else { "low" }
$functionsClass = if ($totalCoverage.functions -ge 80) { "high" } elseif ($totalCoverage.functions -ge 60) { "medium" } else { "low" }

# Generar HTML usando StringBuilder
$htmlBuilder = New-Object System.Text.StringBuilder
$timestamp = Get-Date -Format "dd/MM/yyyy HH:mm:ss"

# Header HTML
$htmlBuilder.AppendLine('<!DOCTYPE html>') | Out-Null
$htmlBuilder.AppendLine('<html lang="es">') | Out-Null
$htmlBuilder.AppendLine('<head>') | Out-Null
$htmlBuilder.AppendLine('    <meta charset="UTF-8">') | Out-Null
$htmlBuilder.AppendLine('    <meta name="viewport" content="width=device-width, initial-scale=1.0">') | Out-Null
$htmlBuilder.AppendLine('    <title>PGF - Reporte de Cobertura Backend</title>') | Out-Null
$htmlBuilder.AppendLine('    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>') | Out-Null
$htmlBuilder.AppendLine('    <style>') | Out-Null

# CSS Styles
$css = @"
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
            padding: 40px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
        }
        .header h1 {
            color: #003DA5;
            font-size: 3em;
            margin-bottom: 10px;
            font-weight: 700;
        }
        .header p {
            color: #666;
            font-size: 1.2em;
        }
        .timestamp {
            color: #999;
            font-size: 0.9em;
            margin-top: 10px;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .summary-card {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
            transition: transform 0.3s ease;
        }
        .summary-card:hover {
            transform: translateY(-5px);
        }
        .summary-card h3 {
            color: #666;
            font-size: 1em;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .summary-card .value {
            font-size: 3em;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .summary-card .value.high { color: #4caf50; }
        .summary-card .value.medium { color: #ff9800; }
        .summary-card .value.low { color: #f44336; }
        .summary-card .progress-bar {
            width: 100%;
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 15px;
        }
        .summary-card .progress-fill {
            height: 100%;
            transition: width 0.5s ease;
            border-radius: 4px;
        }
        .summary-card .progress-fill.high { background: #4caf50; }
        .summary-card .progress-fill.medium { background: #ff9800; }
        .summary-card .progress-fill.low { background: #f44336; }
        .chart-container {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }
        .chart-container h2 {
            color: #003DA5;
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        .modules-table {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow-x: auto;
        }
        .modules-table h2 {
            color: #003DA5;
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th {
            background: #003DA5;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 0.5px;
        }
        td {
            padding: 15px;
            border-bottom: 1px solid #eee;
        }
        tr:hover {
            background: #f5f5f5;
        }
        .coverage-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9em;
        }
        .coverage-badge.high {
            background: #4caf50;
            color: white;
        }
        .coverage-badge.medium {
            background: #ff9800;
            color: white;
        }
        .coverage-badge.low {
            background: #f44336;
            color: white;
        }
        .module-link {
            color: #003DA5;
            text-decoration: none;
            font-weight: 600;
        }
        .module-link:hover {
            text-decoration: underline;
        }
        .footer {
            text-align: center;
            color: white;
            margin-top: 30px;
            padding: 20px;
        }
        .footer a {
            color: white;
            text-decoration: underline;
        }
"@

$htmlBuilder.AppendLine($css) | Out-Null
$htmlBuilder.AppendLine('    </style>') | Out-Null
$htmlBuilder.AppendLine('</head>') | Out-Null
$htmlBuilder.AppendLine('<body>') | Out-Null
$htmlBuilder.AppendLine('    <div class="container">') | Out-Null
$htmlBuilder.AppendLine('        <div class="header">') | Out-Null
$htmlBuilder.AppendLine('            <h1>Reporte de Cobertura Backend</h1>') | Out-Null
$htmlBuilder.AppendLine('            <p>Plataforma de Gestion de Flota - PGF</p>') | Out-Null
$htmlBuilder.AppendLine("            <div class=`"timestamp`">Generado el $timestamp</div>") | Out-Null
$htmlBuilder.AppendLine('        </div>') | Out-Null
$htmlBuilder.AppendLine('') | Out-Null
$htmlBuilder.AppendLine('        <div class="summary-grid">') | Out-Null

# Summary Cards
$htmlBuilder.AppendLine('            <div class="summary-card">') | Out-Null
$htmlBuilder.AppendLine('                <h3>Lineas</h3>') | Out-Null
$htmlBuilder.AppendLine("                <div class=`"value $linesClass`">$($totalCoverage.lines)%</div>") | Out-Null
$htmlBuilder.AppendLine('                <div class="progress-bar">') | Out-Null
$htmlBuilder.AppendLine("                    <div class=`"progress-fill $linesClass`" style=`"width: $($totalCoverage.lines)%`"></div>") | Out-Null
$htmlBuilder.AppendLine('                </div>') | Out-Null
$htmlBuilder.AppendLine("                <p style=`"color: #666; margin-top: 10px; font-size: 0.9em;`">$($totalCoverage.covered_lines) / $($totalCoverage.total_lines) lineas</p>") | Out-Null
$htmlBuilder.AppendLine('            </div>') | Out-Null

$htmlBuilder.AppendLine('            <div class="summary-card">') | Out-Null
$htmlBuilder.AppendLine('                <h3>Declaraciones</h3>') | Out-Null
$htmlBuilder.AppendLine("                <div class=`"value $statementsClass`">$($totalCoverage.statements)%</div>") | Out-Null
$htmlBuilder.AppendLine('                <div class="progress-bar">') | Out-Null
$htmlBuilder.AppendLine("                    <div class=`"progress-fill $statementsClass`" style=`"width: $($totalCoverage.statements)%`"></div>") | Out-Null
$htmlBuilder.AppendLine('                </div>') | Out-Null
$htmlBuilder.AppendLine("                <p style=`"color: #666; margin-top: 10px; font-size: 0.9em;`">$($totalCoverage.covered_statements) / $($totalCoverage.total_statements) declaraciones</p>") | Out-Null
$htmlBuilder.AppendLine('            </div>') | Out-Null

$htmlBuilder.AppendLine('            <div class="summary-card">') | Out-Null
$htmlBuilder.AppendLine('                <h3>Ramas</h3>') | Out-Null
$htmlBuilder.AppendLine("                <div class=`"value $branchesClass`">$($totalCoverage.branches)%</div>") | Out-Null
$htmlBuilder.AppendLine('                <div class="progress-bar">') | Out-Null
$htmlBuilder.AppendLine("                    <div class=`"progress-fill $branchesClass`" style=`"width: $($totalCoverage.branches)%`"></div>") | Out-Null
$htmlBuilder.AppendLine('                </div>') | Out-Null
$htmlBuilder.AppendLine('            </div>') | Out-Null

$htmlBuilder.AppendLine('            <div class="summary-card">') | Out-Null
$htmlBuilder.AppendLine('                <h3>Funciones</h3>') | Out-Null
$htmlBuilder.AppendLine("                <div class=`"value $functionsClass`">$($totalCoverage.functions)%</div>") | Out-Null
$htmlBuilder.AppendLine('                <div class="progress-bar">') | Out-Null
$htmlBuilder.AppendLine("                    <div class=`"progress-fill $functionsClass`" style=`"width: $($totalCoverage.functions)%`"></div>") | Out-Null
$htmlBuilder.AppendLine('                </div>') | Out-Null
$htmlBuilder.AppendLine('            </div>') | Out-Null
$htmlBuilder.AppendLine('        </div>') | Out-Null

# Chart Container
$htmlBuilder.AppendLine('        <div class="chart-container">') | Out-Null
$htmlBuilder.AppendLine('            <h2>Cobertura por Modulo</h2>') | Out-Null
$htmlBuilder.AppendLine('            <canvas id="moduleChart" style="max-height: 400px;"></canvas>') | Out-Null
$htmlBuilder.AppendLine('        </div>') | Out-Null

# Modules Table
$htmlBuilder.AppendLine('        <div class="modules-table">') | Out-Null
$htmlBuilder.AppendLine('            <h2>Detalle por Modulo</h2>') | Out-Null
$htmlBuilder.AppendLine('            <table>') | Out-Null
$htmlBuilder.AppendLine('                <thead>') | Out-Null
$htmlBuilder.AppendLine('                    <tr>') | Out-Null
$htmlBuilder.AppendLine('                        <th>Modulo</th>') | Out-Null
$htmlBuilder.AppendLine('                        <th>Lineas</th>') | Out-Null
$htmlBuilder.AppendLine('                        <th>Declaraciones</th>') | Out-Null
$htmlBuilder.AppendLine('                        <th>Ramas</th>') | Out-Null
$htmlBuilder.AppendLine('                        <th>Funciones</th>') | Out-Null
$htmlBuilder.AppendLine('                        <th>Cobertura</th>') | Out-Null
$htmlBuilder.AppendLine('                        <th>Reporte</th>') | Out-Null
$htmlBuilder.AppendLine('                    </tr>') | Out-Null
$htmlBuilder.AppendLine('                </thead>') | Out-Null
$htmlBuilder.AppendLine('                <tbody>') | Out-Null

# Module Rows
foreach ($module in $moduleData) {
    $avgCoverage = ($module.Lines + $module.Statements + $module.Branches + $module.Functions) / 4
    $badgeClass = if ($avgCoverage -ge 80) { "high" } elseif ($avgCoverage -ge 60) { "medium" } else { "low" }
    $avgCoverageRounded = [math]::Round($avgCoverage, 1)
    
    $htmlBuilder.AppendLine('                    <tr>') | Out-Null
    $htmlBuilder.AppendLine("                        <td><strong>$($module.Name)</strong></td>") | Out-Null
    $htmlBuilder.AppendLine("                        <td>$($module.Lines)%</td>") | Out-Null
    $htmlBuilder.AppendLine("                        <td>$($module.Statements)%</td>") | Out-Null
    $htmlBuilder.AppendLine("                        <td>$($module.Branches)%</td>") | Out-Null
    $htmlBuilder.AppendLine("                        <td>$($module.Functions)%</td>") | Out-Null
    $htmlBuilder.AppendLine("                        <td><span class=`"coverage-badge $badgeClass`">$avgCoverageRounded%</span></td>") | Out-Null
    $htmlBuilder.AppendLine("                        <td><a href=`"$($module.ReportUrl)`" target=`"_blank`" class=`"module-link`">Ver Detalle</a></td>") | Out-Null
    $htmlBuilder.AppendLine('                    </tr>') | Out-Null
}

$htmlBuilder.AppendLine('                </tbody>') | Out-Null
$htmlBuilder.AppendLine('            </table>') | Out-Null
$htmlBuilder.AppendLine('        </div>') | Out-Null

# Footer
$htmlBuilder.AppendLine('        <div class="footer">') | Out-Null
$htmlBuilder.AppendLine('            <p>Reporte generado automaticamente por PGF Coverage System</p>') | Out-Null
$htmlBuilder.AppendLine('            <p><a href="../html/index.html" target="_blank">Ver Reporte Completo HTML</a> | <a href="../coverage.xml" target="_blank">Descargar XML</a> | <a href="../coverage.json" target="_blank">Descargar JSON</a></p>') | Out-Null
$htmlBuilder.AppendLine('        </div>') | Out-Null
$htmlBuilder.AppendLine('    </div>') | Out-Null

# JavaScript for Chart
$htmlBuilder.AppendLine('    <script>') | Out-Null
$htmlBuilder.AppendLine('        const moduleData = [') | Out-Null

foreach ($module in $moduleData) {
    $htmlBuilder.AppendLine("            { name: '$($module.Name)', lines: $($module.Lines), statements: $($module.Statements), branches: $($module.Branches), functions: $($module.Functions) },") | Out-Null
}

$htmlBuilder.AppendLine('        ];') | Out-Null
$htmlBuilder.AppendLine('') | Out-Null
$htmlBuilder.AppendLine('        const ctx = document.getElementById("moduleChart").getContext("2d");') | Out-Null
$htmlBuilder.AppendLine('        new Chart(ctx, {') | Out-Null
$htmlBuilder.AppendLine("            type: 'bar',") | Out-Null
$htmlBuilder.AppendLine('            data: {') | Out-Null
$htmlBuilder.AppendLine('                labels: moduleData.map(m => m.name),') | Out-Null
$htmlBuilder.AppendLine('                datasets: [') | Out-Null
$htmlBuilder.AppendLine('                    {') | Out-Null
$htmlBuilder.AppendLine("                        label: 'Lineas',") | Out-Null
$htmlBuilder.AppendLine('                        data: moduleData.map(m => m.lines),') | Out-Null
$htmlBuilder.AppendLine("                        backgroundColor: 'rgba(76, 175, 80, 0.7)',") | Out-Null
$htmlBuilder.AppendLine("                        borderColor: 'rgba(76, 175, 80, 1)',") | Out-Null
$htmlBuilder.AppendLine('                        borderWidth: 1') | Out-Null
$htmlBuilder.AppendLine('                    },') | Out-Null
$htmlBuilder.AppendLine('                    {') | Out-Null
$htmlBuilder.AppendLine("                        label: 'Declaraciones',") | Out-Null
$htmlBuilder.AppendLine('                        data: moduleData.map(m => m.statements),') | Out-Null
$htmlBuilder.AppendLine("                        backgroundColor: 'rgba(33, 150, 243, 0.7)',") | Out-Null
$htmlBuilder.AppendLine("                        borderColor: 'rgba(33, 150, 243, 1)',") | Out-Null
$htmlBuilder.AppendLine('                        borderWidth: 1') | Out-Null
$htmlBuilder.AppendLine('                    },') | Out-Null
$htmlBuilder.AppendLine('                    {') | Out-Null
$htmlBuilder.AppendLine("                        label: 'Ramas',") | Out-Null
$htmlBuilder.AppendLine('                        data: moduleData.map(m => m.branches),') | Out-Null
$htmlBuilder.AppendLine("                        backgroundColor: 'rgba(255, 152, 0, 0.7)',") | Out-Null
$htmlBuilder.AppendLine("                        borderColor: 'rgba(255, 152, 0, 1)',") | Out-Null
$htmlBuilder.AppendLine('                        borderWidth: 1') | Out-Null
$htmlBuilder.AppendLine('                    },') | Out-Null
$htmlBuilder.AppendLine('                    {') | Out-Null
$htmlBuilder.AppendLine("                        label: 'Funciones',") | Out-Null
$htmlBuilder.AppendLine('                        data: moduleData.map(m => m.functions),') | Out-Null
$htmlBuilder.AppendLine("                        backgroundColor: 'rgba(156, 39, 176, 0.7)',") | Out-Null
$htmlBuilder.AppendLine("                        borderColor: 'rgba(156, 39, 176, 1)',") | Out-Null
$htmlBuilder.AppendLine('                        borderWidth: 1') | Out-Null
$htmlBuilder.AppendLine('                    }') | Out-Null
$htmlBuilder.AppendLine('                ]') | Out-Null
$htmlBuilder.AppendLine('            },') | Out-Null
$htmlBuilder.AppendLine('            options: {') | Out-Null
$htmlBuilder.AppendLine('                responsive: true,') | Out-Null
$htmlBuilder.AppendLine('                maintainAspectRatio: true,') | Out-Null
$htmlBuilder.AppendLine('                scales: {') | Out-Null
$htmlBuilder.AppendLine('                    y: {') | Out-Null
$htmlBuilder.AppendLine('                        beginAtZero: true,') | Out-Null
$htmlBuilder.AppendLine('                        max: 100,') | Out-Null
$htmlBuilder.AppendLine('                        ticks: {') | Out-Null
$htmlBuilder.AppendLine('                            callback: function(value) {') | Out-Null
$htmlBuilder.AppendLine("                                return value + '%';") | Out-Null
$htmlBuilder.AppendLine('                            }') | Out-Null
$htmlBuilder.AppendLine('                        }') | Out-Null
$htmlBuilder.AppendLine('                    }') | Out-Null
$htmlBuilder.AppendLine('                },') | Out-Null
$htmlBuilder.AppendLine('                plugins: {') | Out-Null
$htmlBuilder.AppendLine('                    legend: {') | Out-Null
$htmlBuilder.AppendLine("                        position: 'top',") | Out-Null
$htmlBuilder.AppendLine('                    },') | Out-Null
$htmlBuilder.AppendLine('                    title: {') | Out-Null
$htmlBuilder.AppendLine('                        display: false') | Out-Null
$htmlBuilder.AppendLine('                    }') | Out-Null
$htmlBuilder.AppendLine('                }') | Out-Null
$htmlBuilder.AppendLine('            }') | Out-Null
$htmlBuilder.AppendLine('        });') | Out-Null
$htmlBuilder.AppendLine('    </script>') | Out-Null
$htmlBuilder.AppendLine('</body>') | Out-Null
$htmlBuilder.AppendLine('</html>') | Out-Null

# Guardar archivo
$htmlPath = "$outputDir\backend-coverage-report.html"
$htmlBuilder.ToString() | Set-Content $htmlPath -Encoding UTF8

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Reporte generado exitosamente" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Ubicación: $htmlPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "Resumen de cobertura:" -ForegroundColor Yellow
Write-Host "  - Líneas: $($totalCoverage.lines)%" -ForegroundColor White
Write-Host "  - Declaraciones: $($totalCoverage.statements)%" -ForegroundColor White
Write-Host "  - Ramas: $($totalCoverage.branches)%" -ForegroundColor White
Write-Host "  - Funciones: $($totalCoverage.functions)%" -ForegroundColor White
Write-Host ""
Write-Host "Módulos procesados: $($moduleData.Count)" -ForegroundColor Yellow

if ($Open) {
    Write-Host ""
    Write-Host "Abriendo reporte..." -ForegroundColor Yellow
    Start-Process $htmlPath
}

