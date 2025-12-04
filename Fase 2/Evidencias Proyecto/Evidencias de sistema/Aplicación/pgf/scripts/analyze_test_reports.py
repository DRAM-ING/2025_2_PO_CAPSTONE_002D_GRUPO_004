#!/usr/bin/env python3
"""
Script para analizar reportes de pruebas y generar un resumen detallado.

Uso:
    python scripts/analyze_test_reports.py [--latest] [--html]
"""

import json
import xml.etree.ElementTree as ET
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

REPORT_DIR = Path("test-results")
COVERAGE_DIR = REPORT_DIR / "coverage"
JUNIT_DIR = REPORT_DIR / "junit"


def find_latest_junit() -> Path:
    """Encuentra el archivo JUnit más reciente."""
    junit_files = list(JUNIT_DIR.glob("backend-junit-*.xml"))
    if not junit_files:
        return None
    return max(junit_files, key=lambda p: p.stat().st_mtime)


def analyze_junit(xml_path: Path) -> Dict:
    """Analiza un archivo JUnit XML y retorna estadísticas."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        testsuite = root.find('testsuite')
        
        total = int(testsuite.get('tests', 0))
        failures = int(testsuite.get('failures', 0))
        errors = int(testsuite.get('errors', 0))
        skipped = int(testsuite.get('skipped', 0))
        time = float(testsuite.get('time', 0))
        
        passed = total - failures - errors - skipped
        
        # Encontrar pruebas fallidas
        failed_tests = []
        for testcase in testsuite.findall('testcase'):
            failure = testcase.find('failure')
            error = testcase.find('error')
            if failure is not None:
                failed_tests.append({
                    'class': testcase.get('classname', ''),
                    'name': testcase.get('name', ''),
                    'type': 'failure',
                    'message': failure.get('message', '')[:200] if failure.get('message') else '',
                    'time': float(testcase.get('time', 0))
                })
            elif error is not None:
                failed_tests.append({
                    'class': testcase.get('classname', ''),
                    'name': testcase.get('name', ''),
                    'type': 'error',
                    'message': error.get('message', '')[:200] if error.get('message') else '',
                    'time': float(testcase.get('time', 0))
                })
        
        # Agrupar por módulo
        modules = {}
        for test in failed_tests:
            module = test['class'].split('.')[1] if '.' in test['class'] else 'unknown'
            if module not in modules:
                modules[module] = []
            modules[module].append(test)
        
        return {
            'total': total,
            'passed': passed,
            'failures': failures,
            'errors': errors,
            'skipped': skipped,
            'time': time,
            'success_rate': (passed / total * 100) if total > 0 else 0,
            'failed_tests': failed_tests,
            'failed_by_module': modules
        }
    except Exception as e:
        return {'error': str(e)}


def analyze_coverage() -> Dict:
    """Analiza el reporte de cobertura."""
    coverage_file = COVERAGE_DIR / "coverage.json"
    if not coverage_file.exists():
        return {'error': 'Archivo de cobertura no encontrado'}
    
    try:
        with open(coverage_file, 'r') as f:
            cov = json.load(f)
        
        totals = cov.get('totals', {})
        files = cov.get('files', {})
        
        # Calcular estadísticas por módulo
        modules = {}
        for filepath, data in files.items():
            if 'summary' in data:
                module = filepath.split('/')[0] if '/' in filepath else 'root'
                if module not in modules:
                    modules[module] = {
                        'files': 0,
                        'total_lines': 0,
                        'covered_lines': 0,
                        'files_detail': []
                    }
                
                summary = data['summary']
                modules[module]['files'] += 1
                modules[module]['total_lines'] += summary.get('num_statements', 0)
                modules[module]['covered_lines'] += summary.get('covered_lines', 0)
                modules[module]['files_detail'].append({
                    'file': filepath,
                    'coverage': summary.get('percent_covered', 0),
                    'lines': f"{summary.get('covered_lines', 0)}/{summary.get('num_statements', 0)}"
                })
        
        # Calcular porcentaje por módulo
        for module in modules:
            total = modules[module]['total_lines']
            covered = modules[module]['covered_lines']
            modules[module]['coverage'] = (covered / total * 100) if total > 0 else 0
            modules[module]['files_detail'].sort(key=lambda x: x['coverage'])
        
        # Archivos con menor cobertura
        files_cov = []
        for filepath, data in files.items():
            if 'summary' in data:
                summary = data['summary']
                pct = summary.get('percent_covered', 0)
                files_cov.append({
                    'file': filepath,
                    'coverage': pct,
                    'covered': summary.get('covered_lines', 0),
                    'total': summary.get('num_statements', 0)
                })
        
        files_cov.sort(key=lambda x: x['coverage'])
        
        return {
            'total_coverage': totals.get('percent_covered', 0),
            'total_lines': totals.get('num_statements', 0),
            'covered_lines': totals.get('covered_lines', 0),
            'total_files': len(files),
            'by_module': modules,
            'lowest_coverage': files_cov[:15]  # Top 15 archivos con menor cobertura
        }
    except Exception as e:
        return {'error': str(e)}


def generate_summary(junit_data: Dict, coverage_data: Dict, output_html: bool = False) -> str:
    """Genera un resumen detallado en texto o HTML."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if output_html:
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Análisis de Pruebas - PGF</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #003DA5; border-bottom: 3px solid #003DA5; padding-bottom: 10px; }}
        h2 {{ color: #0052CC; margin-top: 30px; }}
        .stat-box {{ display: inline-block; margin: 10px; padding: 15px; background: #f9f9f9; border-radius: 5px; min-width: 150px; }}
        .stat-box .label {{ font-size: 12px; color: #666; }}
        .stat-box .value {{ font-size: 24px; font-weight: bold; color: #003DA5; }}
        .success {{ color: #00A859; }}
        .failure {{ color: #E60012; }}
        .warning {{ color: #FF6B35; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #003DA5; color: white; }}
        tr:hover {{ background: #f5f5f5; }}
        .code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: monospace; font-size: 12px; }}
        .module {{ margin: 20px 0; padding: 15px; background: #f9f9f9; border-left: 4px solid #003DA5; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Análisis de Pruebas - PGF</h1>
        <p><strong>Generado:</strong> {timestamp}</p>
        
        <h2>📈 Resumen de Pruebas</h2>
        <div class="stat-box">
            <div class="label">Total</div>
            <div class="value">{junit_data.get('total', 0)}</div>
        </div>
        <div class="stat-box">
            <div class="label">Pasadas</div>
            <div class="value success">{junit_data.get('passed', 0)}</div>
        </div>
        <div class="stat-box">
            <div class="label">Fallidas</div>
            <div class="value failure">{junit_data.get('failures', 0)}</div>
        </div>
        <div class="stat-box">
            <div class="label">Errores</div>
            <div class="value failure">{junit_data.get('errors', 0)}</div>
        </div>
        <div class="stat-box">
            <div class="label">Tasa de Éxito</div>
            <div class="value">{junit_data.get('success_rate', 0):.2f}%</div>
        </div>
        <div class="stat-box">
            <div class="label">Tiempo</div>
            <div class="value">{junit_data.get('time', 0):.2f}s</div>
        </div>
"""
        
        # Pruebas fallidas
        if junit_data.get('failed_tests'):
            html += f"""
        <h2>❌ Pruebas Fallidas ({len(junit_data['failed_tests'])})</h2>
        <table>
            <tr>
                <th>Módulo</th>
                <th>Prueba</th>
                <th>Tipo</th>
                <th>Mensaje</th>
                <th>Tiempo</th>
            </tr>
"""
            for test in junit_data['failed_tests']:
                module = test['class'].split('.')[1] if '.' in test['class'] else 'unknown'
                html += f"""
            <tr>
                <td><span class="code">{module}</span></td>
                <td><span class="code">{test['name']}</span></td>
                <td><span class="failure">{test['type']}</span></td>
                <td>{test['message'][:100]}...</td>
                <td>{test['time']:.3f}s</td>
            </tr>
"""
            html += "</table>"
        
        # Cobertura
        if 'error' not in coverage_data:
            html += f"""
        <h2>📊 Cobertura de Código</h2>
        <div class="stat-box">
            <div class="label">Cobertura Total</div>
            <div class="value">{coverage_data.get('total_coverage', 0):.2f}%</div>
        </div>
        <div class="stat-box">
            <div class="label">Líneas Cubiertas</div>
            <div class="value">{coverage_data.get('covered_lines', 0)}/{coverage_data.get('total_lines', 0)}</div>
        </div>
        <div class="stat-box">
            <div class="label">Archivos</div>
            <div class="value">{coverage_data.get('total_files', 0)}</div>
        </div>
        
        <h3>Cobertura por Módulo</h3>
        <table>
            <tr>
                <th>Módulo</th>
                <th>Cobertura</th>
                <th>Archivos</th>
                <th>Líneas</th>
            </tr>
"""
            for module, data in sorted(coverage_data.get('by_module', {}).items(), key=lambda x: x[1]['coverage']):
                html += f"""
            <tr>
                <td><strong>{module}</strong></td>
                <td>{data['coverage']:.2f}%</td>
                <td>{data['files']}</td>
                <td>{data['covered_lines']}/{data['total_lines']}</td>
            </tr>
"""
            html += "</table>"
            
            # Archivos con menor cobertura
            if coverage_data.get('lowest_coverage'):
                html += """
        <h3>Archivos con Menor Cobertura (Top 15)</h3>
        <table>
            <tr>
                <th>Archivo</th>
                <th>Cobertura</th>
                <th>Líneas</th>
            </tr>
"""
                for file_info in coverage_data['lowest_coverage']:
                    color = "failure" if file_info['coverage'] < 50 else "warning" if file_info['coverage'] < 80 else "success"
                    html += f"""
            <tr>
                <td><span class="code">{file_info['file']}</span></td>
                <td><span class="{color}">{file_info['coverage']:.2f}%</span></td>
                <td>{file_info['covered']}/{file_info['total']}</td>
            </tr>
"""
                html += "</table>"
        
        html += """
    </div>
</body>
</html>
"""
        return html
    else:
        # Texto plano
        text = f"""
{'='*80}
📊 ANÁLISIS DE PRUEBAS - PGF
{'='*80}
Generado: {timestamp}

📈 RESUMEN DE PRUEBAS
{'-'*80}
Total:        {junit_data.get('total', 0)}
Pasadas:      {junit_data.get('passed', 0)} ✅
Fallidas:     {junit_data.get('failures', 0)} ❌
Errores:      {junit_data.get('errors', 0)} ❌
Omitidas:     {junit_data.get('skipped', 0)} ⏭️
Tasa de Éxito: {junit_data.get('success_rate', 0):.2f}%
Tiempo:       {junit_data.get('time', 0):.2f}s
"""
        
        # Pruebas fallidas
        if junit_data.get('failed_tests'):
            text += f"""
❌ PRUEBAS FALLIDAS ({len(junit_data['failed_tests'])})
{'-'*80}
"""
            for i, test in enumerate(junit_data['failed_tests'], 1):
                module = test['class'].split('.')[1] if '.' in test['class'] else 'unknown'
                text += f"""
{i}. [{module}] {test['name']}
   Tipo: {test['type']}
   Mensaje: {test['message'][:150]}
   Tiempo: {test['time']:.3f}s
"""
        
        # Cobertura
        if 'error' not in coverage_data:
            text += f"""
📊 COBERTURA DE CÓDIGO
{'-'*80}
Cobertura Total: {coverage_data.get('total_coverage', 0):.2f}%
Líneas:         {coverage_data.get('covered_lines', 0)}/{coverage_data.get('total_lines', 0)}
Archivos:       {coverage_data.get('total_files', 0)}

Cobertura por Módulo:
"""
            for module, data in sorted(coverage_data.get('by_module', {}).items(), key=lambda x: x[1]['coverage']):
                text += f"  {module:20s} {data['coverage']:6.2f}% ({data['covered_lines']}/{data['total_lines']} líneas, {data['files']} archivos)\n"
            
            if coverage_data.get('lowest_coverage'):
                text += f"""
Archivos con Menor Cobertura (Top 15):
"""
                for file_info in coverage_data['lowest_coverage']:
                    text += f"  {file_info['coverage']:6.2f}% - {file_info['file']} ({file_info['covered']}/{file_info['total']})\n"
        
        text += f"""
{'='*80}
📄 Reportes completos disponibles en: test-results/
  - HTML: test-results/backend-report-*.html
  - JUnit: test-results/junit/backend-junit-*.xml
  - Cobertura: test-results/coverage/index.html
{'='*80}
"""
        return text


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Analiza reportes de pruebas')
    parser.add_argument('--latest', action='store_true', help='Usar el reporte más reciente')
    parser.add_argument('--html', action='store_true', help='Generar reporte HTML')
    parser.add_argument('--junit', type=str, help='Ruta al archivo JUnit XML específico')
    args = parser.parse_args()
    
    # Encontrar archivo JUnit
    if args.junit:
        junit_file = Path(args.junit)
    elif args.latest:
        junit_file = find_latest_junit()
    else:
        junit_file = find_latest_junit()
    
    if not junit_file or not junit_file.exists():
        print("❌ No se encontró archivo JUnit XML")
        print(f"   Buscando en: {JUNIT_DIR}")
        sys.exit(1)
    
    print(f"📄 Analizando: {junit_file}")
    
    # Analizar reportes
    junit_data = analyze_junit(junit_file)
    if 'error' in junit_data:
        print(f"❌ Error analizando JUnit: {junit_data['error']}")
        sys.exit(1)
    
    coverage_data = analyze_coverage()
    if 'error' in coverage_data:
        print(f"⚠️  Advertencia: {coverage_data['error']}")
        coverage_data = {}
    
    # Generar resumen
    summary = generate_summary(junit_data, coverage_data, output_html=args.html)
    
    # Guardar o mostrar
    if args.html:
        output_file = REPORT_DIR / f"analysis-{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"✅ Reporte HTML generado: {output_file}")
    else:
        print(summary)
        
        # Guardar también en archivo de texto
        output_file = REPORT_DIR / f"analysis-{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"✅ Reporte de texto guardado: {output_file}")


if __name__ == '__main__':
    main()

