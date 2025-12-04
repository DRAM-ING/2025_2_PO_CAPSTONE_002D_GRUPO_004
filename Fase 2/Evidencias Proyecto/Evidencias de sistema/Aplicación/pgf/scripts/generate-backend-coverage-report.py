#!/usr/bin/env python3
"""
Script para generar un dashboard HTML visual de cobertura del backend
Uso: python scripts/generate-backend-coverage-report.py [--open]
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

def load_json_safe(filepath):
    """Carga un archivo JSON de forma segura"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Error al leer {filepath}: {e}")
        return None

def extract_totals(data):
    """Extrae la sección totals del JSON"""
    if not data:
        return None
    if isinstance(data, dict) and 'totals' in data:
        return data['totals']
    return None

def get_coverage_class(value):
    """Determina la clase CSS según el valor de cobertura"""
    if value >= 80:
        return "high"
    elif value >= 60:
        return "medium"
    else:
        return "low"

def get_coverage_color(value):
    """Obtiene el color según el valor de cobertura"""
    if value >= 80:
        return "#4caf50"
    elif value >= 60:
        return "#ff9800"
    else:
        return "#f44336"

def main():
    open_report = '--open' in sys.argv or '-open' in sys.argv
    
    print("=" * 50)
    print("  PGF - Backend Coverage Dashboard Generator")
    print("=" * 50)
    print()
    
    report_dir = Path("coverage-reports")
    output_dir = report_dir / "dashboard"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Leer reporte principal
    main_report_path = report_dir / "coverage.json"
    main_report = None
    if main_report_path.exists():
        main_data = load_json_safe(main_report_path)
        if main_data:
            main_report = extract_totals(main_data)
            if main_report:
                print("[OK] Reporte principal cargado")
            else:
                print("[WARN] No se encontro totals en el reporte principal")
        else:
            print("[WARN] No se pudo leer el reporte principal")
    else:
        print(f"[WARN] No se encontro el reporte principal en: {main_report_path}")
    
    # Leer reportes por módulo
    module_reports = {}
    modules_dir = report_dir / "modules"
    if modules_dir.exists():
        for module_dir in modules_dir.iterdir():
            if module_dir.is_dir():
                module_json_path = module_dir / "coverage.json"
                if module_json_path.exists():
                    module_data = load_json_safe(module_json_path)
                    if module_data:
                        totals = extract_totals(module_data)
                        if totals:
                            module_reports[module_dir.name] = totals
                            print(f"[OK] Modulo {module_dir.name} cargado")
                        else:
                            print(f"[WARN] No se encontro totals en modulo {module_dir.name}")
                    else:
                        print(f"[WARN] No se pudo leer modulo {module_dir.name}")
    else:
        print(f"[WARN] No se encontro el directorio de modulos: {modules_dir}")
    
    # Extraer datos del reporte principal
    total_coverage = {
        'lines': 0,
        'statements': 0,
        'branches': 0,
        'functions': 0,
        'covered_lines': 0,
        'total_lines': 0,
        'covered_statements': 0,
        'total_statements': 0,
        'missing_lines': 0
    }
    
    if main_report:
        total_lines = main_report.get('num_statements', 0)
        covered_lines = main_report.get('covered_lines', 0)
        missing_lines = main_report.get('missing_lines', 0)
        
        if total_lines > 0:
            total_coverage['lines'] = round((covered_lines / total_lines) * 100, 2)
        else:
            total_coverage['lines'] = round(main_report.get('percent_covered', 0), 2)
        
        total_coverage['statements'] = round(main_report.get('percent_covered', 0), 2)
        total_coverage['branches'] = round(main_report.get('percent_covered_branches', total_coverage['statements']), 2)
        total_coverage['functions'] = round(main_report.get('percent_covered_functions', total_coverage['statements']), 2)
        total_coverage['covered_lines'] = covered_lines
        total_coverage['total_lines'] = total_lines
        total_coverage['covered_statements'] = covered_lines
        total_coverage['total_statements'] = total_lines
        total_coverage['missing_lines'] = missing_lines
    
    # Calcular cobertura promedio total
    avg_coverage = (total_coverage['lines'] + total_coverage['statements'] + 
                   total_coverage['branches'] + total_coverage['functions']) / 4
    
    # Extraer datos por módulo
    module_data = []
    for module_name, totals in module_reports.items():
        total_lines = totals.get('num_statements', 0)
        covered_lines = totals.get('covered_lines', 0)
        if total_lines > 0:
            lines_coverage = round((covered_lines / total_lines) * 100, 2)
        else:
            lines_coverage = round(totals.get('percent_covered', 0), 2)
        
        statements_coverage = round(totals.get('percent_covered', 0), 2)
        branches_coverage = round(totals.get('percent_covered_branches', statements_coverage), 2)
        functions_coverage = round(totals.get('percent_covered_functions', statements_coverage), 2)
        
        module_avg = (lines_coverage + statements_coverage + branches_coverage + functions_coverage) / 4
        
        module_data.append({
            'name': module_name,
            'lines': lines_coverage,
            'statements': statements_coverage,
            'branches': branches_coverage,
            'functions': functions_coverage,
            'average': module_avg,
            'covered_lines': covered_lines,
            'total_lines': total_lines,
            'report_url': f"../modules/{module_name}/html/index.html"
        })
    
    # Ordenar módulos por cobertura promedio (descendente)
    module_data.sort(key=lambda x: x['average'], reverse=True)
    
    # Calcular estadísticas adicionales
    modules_count = len(module_data)
    modules_high = len([m for m in module_data if m['average'] >= 80])
    modules_medium = len([m for m in module_data if 60 <= m['average'] < 80])
    modules_low = len([m for m in module_data if m['average'] < 60])
    
    total_covered_all = sum(m['covered_lines'] for m in module_data)
    total_lines_all = sum(m['total_lines'] for m in module_data)
    
    # Calcular clases CSS
    lines_class = get_coverage_class(total_coverage['lines'])
    statements_class = get_coverage_class(total_coverage['statements'])
    branches_class = get_coverage_class(total_coverage['branches'])
    functions_class = get_coverage_class(total_coverage['functions'])
    avg_class = get_coverage_class(avg_coverage)
    
    # Generar HTML
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PGF - Dashboard de Cobertura Backend</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1600px;
            margin: 0 auto;
        }}
        .header {{
            background: white;
            padding: 40px;
            border-radius: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.15);
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 5px;
            background: linear-gradient(90deg, #003DA5, #00A8E8);
        }}
        .header h1 {{
            color: #003DA5;
            font-size: 3.5em;
            margin-bottom: 10px;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }}
        .header p {{
            color: #666;
            font-size: 1.3em;
            margin-bottom: 15px;
        }}
        .timestamp {{
            color: #999;
            font-size: 0.95em;
            margin-top: 10px;
        }}
        .main-kpi {{
            background: linear-gradient(135deg, #003DA5 0%, #00A8E8 100%);
            color: white;
            padding: 50px;
            border-radius: 20px;
            margin-bottom: 30px;
            box-shadow: 0 15px 40px rgba(0,0,0,0.2);
            text-align: center;
        }}
        .main-kpi h2 {{
            font-size: 1.2em;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 20px;
            opacity: 0.9;
        }}
        .main-kpi .big-value {{
            font-size: 6em;
            font-weight: 700;
            margin: 20px 0;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.2);
        }}
        .main-kpi .subtitle {{
            font-size: 1.3em;
            opacity: 0.95;
            margin-top: 15px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .stat-card:hover {{
            transform: translateY(-8px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.2);
        }}
        .stat-card .stat-value {{
            font-size: 2.5em;
            font-weight: 700;
            margin: 10px 0;
            color: #003DA5;
        }}
        .stat-card .stat-label {{
            color: #666;
            font-size: 0.95em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: white;
            padding: 35px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        .summary-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #003DA5, #00A8E8);
        }}
        .summary-card:hover {{
            transform: translateY(-8px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.2);
        }}
        .summary-card h3 {{
            color: #666;
            font-size: 1.1em;
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            font-weight: 600;
        }}
        .summary-card .value {{
            font-size: 3.5em;
            font-weight: 700;
            margin-bottom: 15px;
            transition: transform 0.3s ease;
        }}
        .summary-card:hover .value {{
            transform: scale(1.1);
        }}
        .summary-card .value.high {{ color: #4caf50; }}
        .summary-card .value.medium {{ color: #ff9800; }}
        .summary-card .value.low {{ color: #f44336; }}
        .summary-card .progress-bar {{
            width: 100%;
            height: 12px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 20px;
            position: relative;
        }}
        .summary-card .progress-fill {{
            height: 100%;
            transition: width 1s ease;
            border-radius: 10px;
            position: relative;
            overflow: hidden;
        }}
        .summary-card .progress-fill::after {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            animation: shimmer 2s infinite;
        }}
        @keyframes shimmer {{
            0% {{ transform: translateX(-100%); }}
            100% {{ transform: translateX(100%); }}
        }}
        .summary-card .progress-fill.high {{ background: linear-gradient(90deg, #4caf50, #66bb6a); }}
        .summary-card .progress-fill.medium {{ background: linear-gradient(90deg, #ff9800, #ffb74d); }}
        .summary-card .progress-fill.low {{ background: linear-gradient(90deg, #f44336, #e57373); }}
        .summary-card .details {{
            color: #666;
            margin-top: 15px;
            font-size: 0.95em;
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }}
        .chart-container {{
            background: white;
            padding: 35px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            position: relative;
        }}
        .chart-container::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #003DA5, #00A8E8);
            border-radius: 20px 20px 0 0;
        }}
        .chart-container h2 {{
            color: #003DA5;
            margin-bottom: 25px;
            font-size: 1.8em;
            font-weight: 600;
        }}
        .modules-table {{
            background: white;
            padding: 35px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            overflow-x: auto;
        }}
        .modules-table h2 {{
            color: #003DA5;
            margin-bottom: 25px;
            font-size: 1.8em;
            font-weight: 600;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            background: linear-gradient(135deg, #003DA5 0%, #00A8E8 100%);
            color: white;
            padding: 18px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 1px;
        }}
        th:first-child {{
            border-radius: 10px 0 0 0;
        }}
        th:last-child {{
            border-radius: 0 10px 0 0;
        }}
        td {{
            padding: 18px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        tr:last-child td:first-child {{
            border-radius: 0 0 0 10px;
        }}
        tr:last-child td:last-child {{
            border-radius: 0 0 10px 0;
        }}
        .coverage-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 25px;
            font-weight: 600;
            font-size: 0.95em;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .coverage-badge.high {{
            background: linear-gradient(135deg, #4caf50, #66bb6a);
            color: white;
        }}
        .coverage-badge.medium {{
            background: linear-gradient(135deg, #ff9800, #ffb74d);
            color: white;
        }}
        .coverage-badge.low {{
            background: linear-gradient(135deg, #f44336, #e57373);
            color: white;
        }}
        .module-link {{
            color: #003DA5;
            text-decoration: none;
            font-weight: 600;
            padding: 8px 16px;
            border-radius: 20px;
            background: #f0f4ff;
            transition: all 0.3s ease;
            display: inline-block;
        }}
        .module-link:hover {{
            background: #003DA5;
            color: white;
            transform: translateX(5px);
        }}
        .footer {{
            text-align: center;
            color: white;
            margin-top: 40px;
            padding: 30px;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }}
        .footer a {{
            color: white;
            text-decoration: underline;
            margin: 0 10px;
        }}
        .footer a:hover {{
            text-decoration: none;
        }}
        .metric-comparison {{
            display: flex;
            justify-content: space-around;
            margin-top: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }}
        .metric-item {{
            text-align: center;
            flex: 1;
            min-width: 120px;
        }}
        .metric-item .metric-label {{
            font-size: 0.85em;
            color: rgba(255,255,255,0.8);
            margin-bottom: 5px;
        }}
        .metric-item .metric-value {{
            font-size: 1.5em;
            font-weight: 700;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Dashboard de Cobertura Backend</h1>
            <p>Plataforma de Gestión de Flota - PGF</p>
            <div class="timestamp">Generado el {timestamp}</div>
        </div>

        <div class="main-kpi">
            <h2>Cobertura Total del Proyecto</h2>
            <div class="big-value" style="color: {get_coverage_color(avg_coverage)}">{round(avg_coverage, 1)}%</div>
            <div class="subtitle">Cobertura promedio de todas las pruebas</div>
            <div class="metric-comparison">
                <div class="metric-item">
                    <div class="metric-label">Líneas Cubiertas</div>
                    <div class="metric-value">{total_coverage['covered_lines']:,}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Total de Líneas</div>
                    <div class="metric-value">{total_coverage['total_lines']:,}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Líneas Sin Cubrir</div>
                    <div class="metric-value">{total_coverage['missing_lines']:,}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Módulos Analizados</div>
                    <div class="metric-value">{modules_count}</div>
                </div>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Módulos con Alta Cobertura</div>
                <div class="stat-value" style="color: #4caf50;">{modules_high}</div>
                <div class="stat-label">≥ 80%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Módulos con Cobertura Media</div>
                <div class="stat-value" style="color: #ff9800;">{modules_medium}</div>
                <div class="stat-label">60% - 79%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Módulos con Baja Cobertura</div>
                <div class="stat-value" style="color: #f44336;">{modules_low}</div>
                <div class="stat-label">&lt; 60%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total de Módulos</div>
                <div class="stat-value" style="color: #003DA5;">{modules_count}</div>
                <div class="stat-label">Analizados</div>
            </div>
        </div>

        <div class="summary-grid">
            <div class="summary-card">
                <h3>Líneas</h3>
                <div class="value {lines_class}">{total_coverage['lines']}%</div>
                <div class="progress-bar">
                    <div class="progress-fill {lines_class}" style="width: {total_coverage['lines']}%"></div>
                </div>
                <div class="details">{total_coverage['covered_lines']:,} / {total_coverage['total_lines']:,} líneas cubiertas</div>
            </div>
            <div class="summary-card">
                <h3>Declaraciones</h3>
                <div class="value {statements_class}">{total_coverage['statements']}%</div>
                <div class="progress-bar">
                    <div class="progress-fill {statements_class}" style="width: {total_coverage['statements']}%"></div>
                </div>
                <div class="details">{total_coverage['covered_statements']:,} / {total_coverage['total_statements']:,} declaraciones cubiertas</div>
            </div>
            <div class="summary-card">
                <h3>Ramas</h3>
                <div class="value {branches_class}">{total_coverage['branches']}%</div>
                <div class="progress-bar">
                    <div class="progress-fill {branches_class}" style="width: {total_coverage['branches']}%"></div>
                </div>
                <div class="details">Cobertura de ramas condicionales</div>
            </div>
            <div class="summary-card">
                <h3>Funciones</h3>
                <div class="value {functions_class}">{total_coverage['functions']}%</div>
                <div class="progress-bar">
                    <div class="progress-fill {functions_class}" style="width: {total_coverage['functions']}%"></div>
                </div>
                <div class="details">Cobertura de funciones y métodos</div>
            </div>
        </div>

        <div class="charts-grid">
            <div class="chart-container">
                <h2>📈 Cobertura por Módulo (Barras)</h2>
                <canvas id="moduleBarChart" style="max-height: 400px;"></canvas>
            </div>
            <div class="chart-container">
                <h2>🥧 Distribución de Cobertura (Pastel)</h2>
                <canvas id="coveragePieChart" style="max-height: 400px;"></canvas>
            </div>
        </div>

        <div class="chart-container">
            <h2>📊 Comparativa de Métricas por Módulo</h2>
            <canvas id="moduleComparisonChart" style="max-height: 500px;"></canvas>
        </div>

        <div class="modules-table">
            <h2>📦 Detalle Completo por Módulo</h2>
            <table>
                <thead>
                    <tr>
                        <th>Módulo</th>
                        <th>Líneas</th>
                        <th>Declaraciones</th>
                        <th>Ramas</th>
                        <th>Funciones</th>
                        <th>Cobertura Promedio</th>
                        <th>Líneas Cubiertas</th>
                        <th>Reporte</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # Agregar filas de módulos
    for module in module_data:
        badge_class = get_coverage_class(module['average'])
        avg_coverage_rounded = round(module['average'], 1)
        
        html += f"""
                    <tr>
                        <td><strong>{module['name']}</strong></td>
                        <td>{module['lines']}%</td>
                        <td>{module['statements']}%</td>
                        <td>{module['branches']}%</td>
                        <td>{module['functions']}%</td>
                        <td><span class="coverage-badge {badge_class}">{avg_coverage_rounded}%</span></td>
                        <td>{module['covered_lines']:,} / {module['total_lines']:,}</td>
                        <td><a href="{module['report_url']}" target="_blank" class="module-link">Ver Detalle →</a></td>
                    </tr>
"""
    
    # Preparar datos para JavaScript
    module_data_js = ",\n            ".join([
        f"{{ name: '{m['name']}', lines: {m['lines']}, statements: {m['statements']}, branches: {m['branches']}, functions: {m['functions']}, average: {m['average']} }}"
        for m in module_data
    ])
    
    # Datos para gráfico de pastel (distribución de módulos por nivel de cobertura)
    pie_data_js = f"""
        high: {modules_high},
        medium: {modules_medium},
        low: {modules_low}
"""
    
    html += f"""
                </tbody>
            </table>
        </div>

        <div class="footer">
            <p><strong>Reporte generado automáticamente por PGF Coverage System</strong></p>
            <p>
                <a href="../html/index.html" target="_blank">Ver Reporte Completo HTML</a> | 
                <a href="../coverage.xml" target="_blank">Descargar XML</a> | 
                <a href="../coverage.json" target="_blank">Descargar JSON</a>
            </p>
        </div>
    </div>

    <script>
        const moduleData = [
            {module_data_js}
        ];

        const pieData = {{
            {pie_data_js}
        }};

        // Gráfico de barras por módulo
        const barCtx = document.getElementById('moduleBarChart').getContext('2d');
        new Chart(barCtx, {{
            type: 'bar',
            data: {{
                labels: moduleData.map(m => m.name),
                datasets: [
                    {{
                        label: 'Líneas',
                        data: moduleData.map(m => m.lines),
                        backgroundColor: 'rgba(76, 175, 80, 0.8)',
                        borderColor: 'rgba(76, 175, 80, 1)',
                        borderWidth: 2
                    }},
                    {{
                        label: 'Declaraciones',
                        data: moduleData.map(m => m.statements),
                        backgroundColor: 'rgba(33, 150, 243, 0.8)',
                        borderColor: 'rgba(33, 150, 243, 1)',
                        borderWidth: 2
                    }},
                    {{
                        label: 'Ramas',
                        data: moduleData.map(m => m.branches),
                        backgroundColor: 'rgba(255, 152, 0, 0.8)',
                        borderColor: 'rgba(255, 152, 0, 1)',
                        borderWidth: 2
                    }},
                    {{
                        label: 'Funciones',
                        data: moduleData.map(m => m.functions),
                        backgroundColor: 'rgba(156, 39, 176, 0.8)',
                        borderColor: 'rgba(156, 39, 176, 1)',
                        borderWidth: 2
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{
                        position: 'top',
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return context.dataset.label + ': ' + context.parsed.y.toFixed(2) + '%';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        ticks: {{
                            callback: function(value) {{
                                return value + '%';
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Gráfico de pastel - Distribución de módulos por nivel
        const pieCtx = document.getElementById('coveragePieChart').getContext('2d');
        new Chart(pieCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Alta Cobertura (≥80%)', 'Cobertura Media (60-79%)', 'Baja Cobertura (<60%)'],
                datasets: [{{
                    data: [pieData.high, pieData.medium, pieData.low],
                    backgroundColor: [
                        'rgba(76, 175, 80, 0.8)',
                        'rgba(255, 152, 0, 0.8)',
                        'rgba(244, 67, 54, 0.8)'
                    ],
                    borderColor: [
                        'rgba(76, 175, 80, 1)',
                        'rgba(255, 152, 0, 1)',
                        'rgba(244, 67, 54, 1)'
                    ],
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{
                        position: 'right',
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return label + ': ' + value + ' módulos (' + percentage + '%)';
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Gráfico de comparación de métricas
        const compCtx = document.getElementById('moduleComparisonChart').getContext('2d');
        new Chart(compCtx, {{
            type: 'radar',
            data: {{
                labels: moduleData.map(m => m.name),
                datasets: [
                    {{
                        label: 'Líneas',
                        data: moduleData.map(m => m.lines),
                        borderColor: 'rgba(76, 175, 80, 1)',
                        backgroundColor: 'rgba(76, 175, 80, 0.2)',
                        borderWidth: 2
                    }},
                    {{
                        label: 'Declaraciones',
                        data: moduleData.map(m => m.statements),
                        borderColor: 'rgba(33, 150, 243, 1)',
                        backgroundColor: 'rgba(33, 150, 243, 0.2)',
                        borderWidth: 2
                    }},
                    {{
                        label: 'Ramas',
                        data: moduleData.map(m => m.branches),
                        borderColor: 'rgba(255, 152, 0, 1)',
                        backgroundColor: 'rgba(255, 152, 0, 0.2)',
                        borderWidth: 2
                    }},
                    {{
                        label: 'Funciones',
                        data: moduleData.map(m => m.functions),
                        borderColor: 'rgba(156, 39, 176, 1)',
                        backgroundColor: 'rgba(156, 39, 176, 0.2)',
                        borderWidth: 2
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                scales: {{
                    r: {{
                        beginAtZero: true,
                        max: 100,
                        ticks: {{
                            stepSize: 20,
                            callback: function(value) {{
                                return value + '%';
                            }}
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        position: 'top',
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return context.dataset.label + ': ' + context.parsed.r.toFixed(2) + '%';
                            }}
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
    
    # Guardar archivo
    html_path = output_dir / "backend-coverage-report.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print()
    print("=" * 50)
    print("  Dashboard generado exitosamente")
    print("=" * 50)
    print()
    print(f"Ubicacion: {html_path}")
    print()
    print("Resumen de cobertura total:")
    print(f"  - Cobertura Promedio: {round(avg_coverage, 1)}%")
    print(f"  - Lineas: {total_coverage['lines']}% ({total_coverage['covered_lines']:,}/{total_coverage['total_lines']:,})")
    print(f"  - Declaraciones: {total_coverage['statements']}%")
    print(f"  - Ramas: {total_coverage['branches']}%")
    print(f"  - Funciones: {total_coverage['functions']}%")
    print()
    print("Estadisticas de modulos:")
    print(f"  - Total de modulos: {modules_count}")
    print(f"  - Alta cobertura (≥80%): {modules_high}")
    print(f"  - Cobertura media (60-79%): {modules_medium}")
    print(f"  - Baja cobertura (<60%): {modules_low}")
    
    if open_report:
        import webbrowser
        print()
        print("Abriendo dashboard...")
        webbrowser.open(str(html_path.absolute()))

if __name__ == "__main__":
    main()
