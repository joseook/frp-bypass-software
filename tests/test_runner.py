#!/usr/bin/env python3
"""
Test Runner para FRP Bypass Professional
========================================

Runner customizado para execução de testes com relatórios detalhados.
"""

import sys
import os
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any
import json

# Adiciona projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

if RICH_AVAILABLE:
    console = Console()
else:
    class SimpleConsole:
        def print(self, text, style=None):
            print(text)
    console = SimpleConsole()


class TestRunner:
    """Runner customizado para testes"""
    
    def __init__(self):
        self.project_root = project_root
        self.test_dir = self.project_root / "tests"
        self.results = {}
        
    def run_all_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """
        Executa todos os testes
        
        Args:
            verbose: Modo verboso
            
        Returns:
            Resultados dos testes
        """
        console.print("🧪 Executando Suite Completa de Testes", style="bold blue" if RICH_AVAILABLE else None)
        
        test_categories = [
            ("Detecção de Dispositivos", "test_device_detection.py"),
            ("Engine de Bypass", "test_bypass_engine.py"),
            ("Base de Dados", "test_database.py"),
            ("Comunicação", "test_communication.py"),
            ("Segurança", "test_security.py")
        ]
        
        all_results = {}
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_time = 0
        
        for category, test_file in test_categories:
            console.print(f"\n📋 Executando: {category}", style="yellow" if RICH_AVAILABLE else None)
            
            result = self._run_pytest(test_file, verbose)
            all_results[category] = result
            
            total_tests += result.get('total', 0)
            total_passed += result.get('passed', 0)
            total_failed += result.get('failed', 0)
            total_time += result.get('duration', 0)
            
            # Mostra resultado da categoria
            status = "✅ PASSOU" if result.get('success', False) else "❌ FALHOU"
            console.print(f"   {status} - {result.get('passed', 0)}/{result.get('total', 0)} testes", 
                         style="green" if result.get('success', False) else "red" if RICH_AVAILABLE else None)
        
        # Resumo final
        self._show_test_summary(all_results, total_tests, total_passed, total_failed, total_time)
        
        return all_results
    
    def run_specific_test(self, test_name: str, verbose: bool = False) -> Dict[str, Any]:
        """
        Executa teste específico
        
        Args:
            test_name: Nome do arquivo de teste
            verbose: Modo verboso
            
        Returns:
            Resultados do teste
        """
        console.print(f"🎯 Executando teste específico: {test_name}", style="blue" if RICH_AVAILABLE else None)
        
        result = self._run_pytest(test_name, verbose)
        
        if result.get('success', False):
            console.print(f"✅ {test_name} - PASSOU", style="green" if RICH_AVAILABLE else None)
        else:
            console.print(f"❌ {test_name} - FALHOU", style="red" if RICH_AVAILABLE else None)
        
        return result
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Executa apenas testes de integração"""
        console.print("🔗 Executando Testes de Integração", style="bold cyan" if RICH_AVAILABLE else None)
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir),
            "-m", "integration",
            "--tb=short",
            "-v"
        ]
        
        return self._execute_pytest_command(cmd)
    
    def run_unit_tests(self) -> Dict[str, Any]:
        """Executa apenas testes unitários"""
        console.print("⚡ Executando Testes Unitários", style="bold green" if RICH_AVAILABLE else None)
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir),
            "-m", "not integration and not slow",
            "--tb=short",
            "-v"
        ]
        
        return self._execute_pytest_command(cmd)
    
    def run_coverage_tests(self) -> Dict[str, Any]:
        """Executa testes com cobertura"""
        console.print("📊 Executando Testes com Cobertura", style="bold magenta" if RICH_AVAILABLE else None)
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir),
            "--cov=core",
            "--cov=database",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--tb=short"
        ]
        
        return self._execute_pytest_command(cmd)
    
    def _run_pytest(self, test_file: str, verbose: bool = False) -> Dict[str, Any]:
        """
        Executa pytest para arquivo específico
        
        Args:
            test_file: Arquivo de teste
            verbose: Modo verboso
            
        Returns:
            Resultados do teste
        """
        test_path = self.test_dir / test_file
        
        if not test_path.exists():
            return {
                'success': False,
                'error': f'Arquivo de teste não encontrado: {test_file}',
                'total': 0,
                'passed': 0,
                'failed': 0,
                'duration': 0
            }
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(test_path),
            "--tb=short",
            "--json-report",
            "--json-report-file=test_results.json"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._execute_pytest_command(cmd)
    
    def _execute_pytest_command(self, cmd: List[str]) -> Dict[str, Any]:
        """
        Executa comando pytest
        
        Args:
            cmd: Comando a executar
            
        Returns:
            Resultados do teste
        """
        start_time = time.time()
        
        try:
            if RICH_AVAILABLE:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task("Executando testes...", total=None)
                    
                    result = subprocess.run(
                        cmd,
                        cwd=self.project_root,
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minutos timeout
                    )
                    
                    progress.update(task, completed=True)
            else:
                print("Executando testes...")
                result = subprocess.run(
                    cmd,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            
            duration = time.time() - start_time
            
            # Tenta ler relatório JSON se disponível
            json_report_path = self.project_root / "test_results.json"
            if json_report_path.exists():
                try:
                    with open(json_report_path, 'r') as f:
                        json_data = json.load(f)
                    
                    return {
                        'success': result.returncode == 0,
                        'total': json_data.get('summary', {}).get('total', 0),
                        'passed': json_data.get('summary', {}).get('passed', 0),
                        'failed': json_data.get('summary', {}).get('failed', 0),
                        'duration': duration,
                        'output': result.stdout,
                        'error': result.stderr if result.returncode != 0 else None
                    }
                except Exception:
                    pass
                finally:
                    # Limpa arquivo temporário
                    json_report_path.unlink(missing_ok=True)
            
            # Fallback para parsing manual da saída
            return self._parse_pytest_output(result, duration)
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Timeout na execução dos testes',
                'total': 0,
                'passed': 0,
                'failed': 0,
                'duration': time.time() - start_time
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro na execução: {str(e)}',
                'total': 0,
                'passed': 0,
                'failed': 0,
                'duration': time.time() - start_time
            }
    
    def _parse_pytest_output(self, result: subprocess.CompletedProcess, duration: float) -> Dict[str, Any]:
        """
        Faz parsing manual da saída do pytest
        
        Args:
            result: Resultado do subprocess
            duration: Duração da execução
            
        Returns:
            Resultados parseados
        """
        output = result.stdout
        
        # Extrai estatísticas da linha final do pytest
        passed = failed = total = 0
        
        lines = output.split('\n')
        for line in reversed(lines):
            if 'passed' in line or 'failed' in line:
                # Procura por padrões como "5 passed, 2 failed"
                import re
                
                passed_match = re.search(r'(\d+) passed', line)
                if passed_match:
                    passed = int(passed_match.group(1))
                
                failed_match = re.search(r'(\d+) failed', line)
                if failed_match:
                    failed = int(failed_match.group(1))
                
                total = passed + failed
                break
        
        return {
            'success': result.returncode == 0,
            'total': total,
            'passed': passed,
            'failed': failed,
            'duration': duration,
            'output': output,
            'error': result.stderr if result.returncode != 0 else None
        }
    
    def _show_test_summary(self, results: Dict[str, Any], total_tests: int, 
                          total_passed: int, total_failed: int, total_time: float):
        """
        Mostra resumo dos testes
        
        Args:
            results: Resultados por categoria
            total_tests: Total de testes
            total_passed: Testes aprovados
            total_failed: Testes falhados
            total_time: Tempo total
        """
        console.print("\n" + "="*60, style="bold" if RICH_AVAILABLE else None)
        console.print("📊 RESUMO DOS TESTES", style="bold blue" if RICH_AVAILABLE else None)
        console.print("="*60, style="bold" if RICH_AVAILABLE else None)
        
        if RICH_AVAILABLE:
            # Tabela detalhada
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Categoria", style="cyan")
            table.add_column("Total", justify="center")
            table.add_column("Passou", justify="center", style="green")
            table.add_column("Falhou", justify="center", style="red")
            table.add_column("Taxa", justify="center")
            table.add_column("Tempo", justify="center")
            
            for category, result in results.items():
                total = result.get('total', 0)
                passed = result.get('passed', 0)
                failed = result.get('failed', 0)
                duration = result.get('duration', 0)
                
                if total > 0:
                    success_rate = f"{(passed/total)*100:.1f}%"
                else:
                    success_rate = "N/A"
                
                table.add_row(
                    category,
                    str(total),
                    str(passed),
                    str(failed),
                    success_rate,
                    f"{duration:.1f}s"
                )
            
            console.print(table)
        else:
            # Versão texto simples
            for category, result in results.items():
                total = result.get('total', 0)
                passed = result.get('passed', 0)
                failed = result.get('failed', 0)
                duration = result.get('duration', 0)
                
                print(f"{category}: {passed}/{total} passou, {failed} falhou ({duration:.1f}s)")
        
        # Estatísticas gerais
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        console.print(f"\n📈 ESTATÍSTICAS GERAIS:", style="bold yellow" if RICH_AVAILABLE else None)
        console.print(f"   Total de Testes: {total_tests}")
        console.print(f"   Aprovados: {total_passed}", style="green" if RICH_AVAILABLE else None)
        console.print(f"   Falhados: {total_failed}", style="red" if total_failed > 0 and RICH_AVAILABLE else None)
        console.print(f"   Taxa de Sucesso: {success_rate:.1f}%")
        console.print(f"   Tempo Total: {total_time:.1f}s")
        
        # Status final
        if total_failed == 0:
            console.print(f"\n🎉 TODOS OS TESTES PASSARAM!", style="bold green" if RICH_AVAILABLE else None)
        else:
            console.print(f"\n⚠️  {total_failed} TESTE(S) FALHARAM", style="bold red" if RICH_AVAILABLE else None)
    
    def generate_html_report(self, results: Dict[str, Any]) -> str:
        """
        Gera relatório HTML dos testes
        
        Args:
            results: Resultados dos testes
            
        Returns:
            Caminho do arquivo HTML gerado
        """
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>FRP Bypass Professional - Test Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
                .summary { background: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }
                .test-category { margin: 20px 0; }
                .passed { color: #27ae60; }
                .failed { color: #e74c3c; }
                .warning { color: #f39c12; }
                table { width: 100%; border-collapse: collapse; margin: 10px 0; }
                th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f8f9fa; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>FRP Bypass Professional - Test Report</h1>
                <p>Generated on: {timestamp}</p>
            </div>
        """.format(timestamp=time.strftime("%Y-%m-%d %H:%M:%S"))
        
        # Adiciona sumário
        total_tests = sum(r.get('total', 0) for r in results.values())
        total_passed = sum(r.get('passed', 0) for r in results.values())
        total_failed = sum(r.get('failed', 0) for r in results.values())
        
        html_content += f"""
            <div class="summary">
                <h2>Summary</h2>
                <p><strong>Total Tests:</strong> {total_tests}</p>
                <p><strong class="passed">Passed:</strong> {total_passed}</p>
                <p><strong class="failed">Failed:</strong> {total_failed}</p>
                <p><strong>Success Rate:</strong> {(total_passed/total_tests*100):.1f}%</p>
            </div>
        """
        
        # Adiciona detalhes por categoria
        html_content += "<h2>Test Categories</h2>"
        
        for category, result in results.items():
            status_class = "passed" if result.get('success', False) else "failed"
            
            html_content += f"""
            <div class="test-category">
                <h3 class="{status_class}">{category}</h3>
                <p>Tests: {result.get('passed', 0)}/{result.get('total', 0)} passed</p>
                <p>Duration: {result.get('duration', 0):.1f}s</p>
            """
            
            if result.get('error'):
                html_content += f'<p class="failed">Error: {result["error"]}</p>'
            
            html_content += "</div>"
        
        html_content += "</body></html>"
        
        # Salva arquivo
        report_path = self.project_root / "test_report.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(report_path)


def main():
    """Função principal do test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Runner para FRP Bypass Professional")
    parser.add_argument("--all", action="store_true", help="Executa todos os testes")
    parser.add_argument("--unit", action="store_true", help="Executa apenas testes unitários")
    parser.add_argument("--integration", action="store_true", help="Executa apenas testes de integração")
    parser.add_argument("--coverage", action="store_true", help="Executa testes com cobertura")
    parser.add_argument("--test", type=str, help="Executa teste específico")
    parser.add_argument("--verbose", "-v", action="store_true", help="Modo verboso")
    parser.add_argument("--html-report", action="store_true", help="Gera relatório HTML")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    results = {}
    
    if args.all or (not args.unit and not args.integration and not args.coverage and not args.test):
        results = runner.run_all_tests(args.verbose)
    elif args.unit:
        results = {"Unit Tests": runner.run_unit_tests()}
    elif args.integration:
        results = {"Integration Tests": runner.run_integration_tests()}
    elif args.coverage:
        results = {"Coverage Tests": runner.run_coverage_tests()}
    elif args.test:
        results = {args.test: runner.run_specific_test(args.test, args.verbose)}
    
    # Gera relatório HTML se solicitado
    if args.html_report and results:
        report_path = runner.generate_html_report(results)
        console.print(f"\n📄 Relatório HTML gerado: {report_path}", style="blue" if RICH_AVAILABLE else None)
    
    # Exit code baseado no sucesso dos testes
    all_success = all(r.get('success', False) for r in results.values())
    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
