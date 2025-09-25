#!/usr/bin/env python3
"""
FRP Bypass Professional - Main CLI Interface
============================================

Interface de linha de comando principal para o software de bypass FRP.
Fornece acesso a todas as funcionalidades do sistema via terminal.

Comandos disponíveis:
- detect: Detecta dispositivos conectados
- bypass: Executa bypass FRP
- info: Mostra informações do dispositivo
- database: Gerencia base de dados
- test: Testa conectividade
"""

import sys
import os
import time
import json
from typing import List, Optional
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text
from loguru import logger

# Adiciona o diretório atual ao path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.device_detection import DeviceDetector, AndroidDevice
from core.communication import CommunicationManager, check_adb_available, check_fastboot_available
from core.bypass_engine import FRPBypassEngine, BypassStatus
from database import DeviceDatabase, ExploitManager

# Configuração do console
console = Console()

# Configuração de logging
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")


def print_banner():
    """Imprime banner do software"""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              FRP BYPASS PROFESSIONAL v1.0.0                  ║
║                                                               ║
║     ⚠️  AVISO: Use apenas em dispositivos próprios ou        ║
║         com autorização expressa do proprietário             ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
    console.print(banner, style="bold cyan")


def check_dependencies() -> bool:
    """Verifica dependências necessárias"""
    console.print("🔍 Verificando dependências...", style="yellow")
    
    issues = []
    
    # Verifica ADB
    if not check_adb_available():
        issues.append("ADB não encontrado ou não funcional")
    else:
        console.print("  ✓ ADB disponível", style="green")
    
    # Verifica Fastboot
    if not check_fastboot_available():
        issues.append("Fastboot não encontrado ou não funcional")
    else:
        console.print("  ✓ Fastboot disponível", style="green")
    
    if issues:
        console.print("\n❌ Problemas encontrados:", style="red bold")
        for issue in issues:
            console.print(f"  • {issue}", style="red")
        console.print("\nInstale Android SDK Platform Tools para continuar.", style="yellow")
        return False
    
    console.print("✅ Todas as dependências estão disponíveis\n", style="green bold")
    return True


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Modo verboso')
@click.option('--no-banner', is_flag=True, help='Não mostrar banner')
@click.option('--api-mode', is_flag=True, help='Modo API para GUI')
def cli(verbose, no_banner, api_mode):
    """FRP Bypass Professional - Ferramenta profissional de bypass FRP"""
    if not no_banner and not api_mode:
        print_banner()
    
    if verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")
    
    if api_mode:
        start_api_server()


@cli.command()
@click.option('--continuous', '-c', is_flag=True, help='Escaneamento contínuo')
@click.option('--interval', '-i', default=5, help='Intervalo para escaneamento contínuo (segundos)')
def detect(continuous, interval):
    """Detecta dispositivos Android conectados"""
    
    if not check_dependencies():
        return
    
    detector = DeviceDetector()
    
    if continuous:
        console.print(f"🔄 Iniciando escaneamento contínuo (intervalo: {interval}s)", style="blue")
        console.print("Pressione Ctrl+C para parar\n", style="yellow")
        
        try:
            while True:
                devices = detector.scan_usb_devices()
                _display_devices(devices)
                
                if devices:
                    console.print(f"\n⏳ Próximo scan em {interval}s...", style="dim")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            console.print("\n🛑 Escaneamento interrompido", style="yellow")
    else:
        console.print("🔍 Escaneando dispositivos USB...", style="blue")
        devices = detector.scan_usb_devices()
        _display_devices(devices)


def _display_devices(devices: List[AndroidDevice]):
    """Exibe lista de dispositivos detectados"""
    if not devices:
        console.print("❌ Nenhum dispositivo Android detectado", style="red")
        console.print("\nDicas:", style="yellow")
        console.print("• Certifique-se de que o dispositivo está conectado via USB", style="dim")
        console.print("• Verifique se USB debugging está habilitado", style="dim")
        console.print("• Tente diferentes modos (fastboot, recovery, download)", style="dim")
        return
    
    console.print(f"✅ {len(devices)} dispositivo(s) detectado(s):", style="green bold")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Fabricante", style="cyan")
    table.add_column("Modelo", style="white")
    table.add_column("Serial", style="dim")
    table.add_column("Modo", style="yellow")
    table.add_column("Android", style="blue")
    table.add_column("FRP", style="red bold")
    table.add_column("Status", style="green")
    
    for device in devices:
        frp_status = "🔒 Bloqueado" if device.frp_locked else "🔓 Livre" if device.frp_locked is False else "❓ Desconhecido"
        bypass_status = "✅ Possível" if device.is_frp_bypassable else "❌ Não possível"
        
        table.add_row(
            device.manufacturer.value.upper(),
            device.model or "Desconhecido",
            device.serial[:10] + "..." if len(device.serial) > 10 else device.serial,
            device.mode.value,
            device.android_version or "?",
            frp_status,
            bypass_status
        )
    
    console.print(table)


@cli.command()
@click.option('--serial', '-s', help='Serial do dispositivo específico')
@click.option('--method', '-m', help='Método específico para usar')
@click.option('--max-attempts', default=3, help='Número máximo de tentativas')
@click.option('--dry-run', is_flag=True, help='Simular execução sem fazer alterações')
def bypass(serial, method, max_attempts, dry_run):
    """Executa bypass FRP em um dispositivo"""
    
    if not check_dependencies():
        return
    
    if dry_run:
        console.print("🧪 MODO SIMULAÇÃO - Nenhuma alteração será feita", style="yellow bold")
    
    # Detecta dispositivos
    detector = DeviceDetector()
    devices = detector.scan_usb_devices()
    
    if not devices:
        console.print("❌ Nenhum dispositivo detectado", style="red")
        return
    
    # Seleciona dispositivo
    target_device = None
    if serial:
        target_device = detector.get_device_by_serial(serial)
        if not target_device:
            console.print(f"❌ Dispositivo com serial '{serial}' não encontrado", style="red")
            return
    else:
        # Se há apenas um dispositivo, usa ele
        if len(devices) == 1:
            target_device = devices[0]
        else:
            console.print("Múltiplos dispositivos detectados. Use --serial para especificar:", style="yellow")
            _display_devices(devices)
            return
    
    # Verifica se o dispositivo pode ter bypass
    if not target_device.is_frp_bypassable:
        console.print(f"❌ Dispositivo {target_device.device_id} não pode ter FRP bypassed", style="red")
        console.print(f"Motivo: FRP não está ativo ou modo incompatível ({target_device.mode.value})", style="dim")
        return
    
    # Mostra informações do dispositivo
    _show_device_info(target_device)
    
    # Confirmação
    if not dry_run:
        console.print("\n⚠️  ATENÇÃO: Esta operação irá modificar o dispositivo!", style="red bold")
        console.print("Certifique-se de que você tem autorização para fazer isso.", style="yellow")
        
        if not click.confirm("Deseja continuar com o bypass FRP?"):
            console.print("Operação cancelada pelo usuário", style="yellow")
            return
    
    # Executa bypass
    _execute_bypass(target_device, max_attempts, dry_run)


def _show_device_info(device: AndroidDevice):
    """Mostra informações detalhadas do dispositivo"""
    info_panel = Panel.fit(
        f"""[bold cyan]Dispositivo Selecionado[/bold cyan]

[bold]Fabricante:[/bold] {device.manufacturer.value.upper()}
[bold]Modelo:[/bold] {device.model or 'Desconhecido'}
[bold]Serial:[/bold] {device.serial}
[bold]Modo:[/bold] {device.mode.value}
[bold]Android:[/bold] {device.android_version or 'Desconhecido'}
[bold]API Level:[/bold] {device.api_level or 'Desconhecido'}
[bold]FRP Status:[/bold] {'🔒 Bloqueado' if device.frp_locked else '🔓 Livre'}
[bold]USB Debug:[/bold] {'✅ Ativo' if device.usb_debugging else '❌ Inativo' if device.usb_debugging is False else '❓ Desconhecido'}""",
        title="📱 Informações do Dispositivo",
        border_style="blue"
    )
    console.print(info_panel)


def _execute_bypass(device: AndroidDevice, max_attempts: int, dry_run: bool):
    """Executa o processo de bypass"""
    
    if dry_run:
        console.print("🧪 Simulando bypass...", style="yellow")
        time.sleep(3)
        console.print("✅ Simulação concluída com sucesso!", style="green")
        return
    
    # Inicializa componentes
    try:
        device_db = DeviceDatabase()
        comm_manager = CommunicationManager()
        engine = FRPBypassEngine(device_db, comm_manager)
    except Exception as e:
        console.print(f"❌ Erro ao inicializar engine: {e}", style="red")
        return
    
    # Inicia sessão de bypass
    session_id = engine.start_bypass_session(device)
    session = engine.get_session(session_id)
    
    console.print(f"🚀 Iniciando bypass (Sessão: {session_id})", style="green bold")
    
    # Progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Executando bypass...", total=None)
        
        # Executa bypass
        result = engine.execute_bypass(device, max_attempts)
        
        progress.update(task, completed=True)
    
    # Mostra resultado
    _display_bypass_result(result)


def _display_bypass_result(result):
    """Exibe resultado do bypass"""
    if result.success:
        console.print("\n🎉 BYPASS EXECUTADO COM SUCESSO!", style="green bold")
        status_color = "green"
        status_icon = "✅"
    else:
        console.print("\n❌ BYPASS FALHOU", style="red bold")
        status_color = "red"
        status_icon = "❌"
    
    # Painel com detalhes
    details = f"""[bold]{status_icon} Status:[/bold] [{status_color}]{result.status.value.upper()}[/{status_color}]
[bold]⚙️ Método:[/bold] {result.method_used}
[bold]⏱️ Tempo:[/bold] {result.execution_time:.2f}s
[bold]📝 Etapas:[/bold] {len(result.steps_completed)}"""
    
    if result.error_message:
        details += f"\n[bold]❌ Erro:[/bold] [red]{result.error_message}[/red]"
    
    result_panel = Panel.fit(
        details,
        title="📊 Resultado do Bypass",
        border_style=status_color
    )
    console.print(result_panel)
    
    # Mostra logs se houver
    if result.logs:
        console.print("\n📋 Log de Execução:", style="bold")
        for log_entry in result.logs[-10:]:  # Últimas 10 entradas
            console.print(f"  {log_entry}", style="dim")


@cli.command()
@click.option('--serial', '-s', help='Serial do dispositivo específico')
def info(serial):
    """Mostra informações detalhadas de um dispositivo"""
    
    detector = DeviceDetector()
    devices = detector.scan_usb_devices()
    
    if not devices:
        console.print("❌ Nenhum dispositivo detectado", style="red")
        return
    
    target_device = None
    if serial:
        target_device = detector.get_device_by_serial(serial)
        if not target_device:
            console.print(f"❌ Dispositivo com serial '{serial}' não encontrado", style="red")
            return
    else:
        if len(devices) == 1:
            target_device = devices[0]
        else:
            console.print("Múltiplos dispositivos detectados. Use --serial para especificar:", style="yellow")
            _display_devices(devices)
            return
    
    # Mostra informações detalhadas
    _show_device_info(target_device)
    
    # Informações da base de dados
    try:
        device_db = DeviceDatabase()
        profile = None
        
        if target_device.model:
            profile = device_db.find_device_by_name(target_device.model)
        
        if not profile:
            manufacturer_devices = device_db.find_devices_by_manufacturer(target_device.manufacturer.value)
            if manufacturer_devices:
                profile = manufacturer_devices[0]  # Pega o primeiro como exemplo
        
        if profile:
            console.print("\n📚 Informações da Base de Dados:", style="bold blue")
            console.print(f"  • Dificuldade de Bypass: {profile.frp_bypass_difficulty}")
            console.print(f"  • Taxa de Sucesso: {profile.success_rate}%")
            console.print(f"  • Métodos Suportados: {', '.join(profile.supported_methods)}")
            console.print(f"  • Chipset: {profile.chipset}")
        else:
            console.print("\n❓ Dispositivo não encontrado na base de dados", style="yellow")
            
    except Exception as e:
        console.print(f"\n❌ Erro ao acessar base de dados: {e}", style="red")


@cli.command()
def database():
    """Gerencia a base de dados de dispositivos"""
    
    try:
        device_db = DeviceDatabase()
        stats = device_db.get_statistics()
        
        console.print("📊 Estatísticas da Base de Dados:", style="bold blue")
        
        # Tabela principal
        main_table = Table(show_header=False, box=None)
        main_table.add_column("Metric", style="cyan")
        main_table.add_column("Value", style="white")
        
        main_table.add_row("📱 Total de Dispositivos", str(stats['total_devices']))
        main_table.add_row("🏭 Fabricantes", str(stats['manufacturers']))
        main_table.add_row("⚙️ Métodos de Bypass", str(stats['total_methods']))
        main_table.add_row("📈 Taxa de Sucesso Média", f"{stats['average_success_rate']}%")
        main_table.add_row("📅 Versão da Base", stats['database_version'])
        main_table.add_row("🔄 Última Atualização", stats['last_updated'])
        
        console.print(main_table)
        
        # Distribuição por dificuldade
        console.print("\n📊 Distribuição por Dificuldade:", style="bold")
        difficulty_table = Table()
        difficulty_table.add_column("Dificuldade", style="cyan")
        difficulty_table.add_column("Quantidade", style="white")
        difficulty_table.add_column("Porcentagem", style="green")
        
        for difficulty, count in stats['difficulty_distribution'].items():
            percentage = (count / stats['total_devices'] * 100) if stats['total_devices'] > 0 else 0
            difficulty_table.add_row(
                difficulty.replace('_', ' ').title(),
                str(count),
                f"{percentage:.1f}%"
            )
        
        console.print(difficulty_table)
        
        # Fabricantes
        console.print("\n🏭 Fabricantes Suportados:", style="bold")
        manufacturers_text = ", ".join(stats['manufacturer_list'])
        console.print(manufacturers_text, style="dim")
        
    except Exception as e:
        console.print(f"❌ Erro ao acessar base de dados: {e}", style="red")


@cli.command()
def test():
    """Testa conectividade e funcionalidades básicas"""
    
    console.print("🧪 Executando testes de conectividade...", style="blue bold")
    
    # Teste 1: Dependências
    console.print("\n1. Verificando dependências:", style="bold")
    deps_ok = check_dependencies()
    
    # Teste 2: Base de dados
    console.print("2. Testando base de dados:", style="bold")
    try:
        device_db = DeviceDatabase()
        stats = device_db.get_statistics()
        console.print(f"  ✓ Base carregada: {stats['total_devices']} dispositivos", style="green")
    except Exception as e:
        console.print(f"  ❌ Erro na base de dados: {e}", style="red")
        deps_ok = False
    
    # Teste 3: Detecção de dispositivos
    console.print("3. Testando detecção de dispositivos:", style="bold")
    try:
        detector = DeviceDetector()
        devices = detector.scan_usb_devices()
        console.print(f"  ✓ Scan concluído: {len(devices)} dispositivos encontrados", style="green")
        
        if devices:
            console.print(f"  📱 Primeiro dispositivo: {devices[0].manufacturer.value} {devices[0].model}", style="dim")
    except Exception as e:
        console.print(f"  ❌ Erro na detecção: {e}", style="red")
        deps_ok = False
    
    # Teste 4: Engine de bypass
    console.print("4. Testando engine de bypass:", style="bold")
    try:
        comm_manager = CommunicationManager()
        engine = FRPBypassEngine(device_db, comm_manager)
        engine_stats = engine.get_engine_statistics()
        console.print(f"  ✓ Engine inicializado: {engine_stats['available_exploits']} exploits", style="green")
    except Exception as e:
        console.print(f"  ❌ Erro no engine: {e}", style="red")
        deps_ok = False
    
    # Resultado final
    if deps_ok:
        console.print("\n✅ TODOS OS TESTES PASSARAM!", style="green bold")
        console.print("Sistema pronto para uso.", style="green")
    else:
        console.print("\n❌ ALGUNS TESTES FALHARAM!", style="red bold")
        console.print("Verifique os erros acima antes de usar o sistema.", style="yellow")


def start_api_server():
    """Inicia servidor API para comunicação com GUI"""
    try:
        from flask import Flask, jsonify, request
        from flask_cors import CORS
        import threading
        
        app = Flask(__name__)
        CORS(app)
        
        # Inicializa componentes
        device_db = DeviceDatabase()
        comm_manager = CommunicationManager()
        engine = FRPBypassEngine(device_db, comm_manager)
        detector = DeviceDetector()
        
        @app.route('/api/status', methods=['GET'])
        def api_status():
            return jsonify({
                'status': 'online',
                'version': '1.0.0',
                'timestamp': time.time()
            })
        
        @app.route('/api/detect', methods=['GET'])
        def api_detect():
            try:
                devices = detector.scan_usb_devices()
                device_list = [device.to_dict() for device in devices]
                return jsonify({
                    'success': True,
                    'devices': device_list,
                    'count': len(device_list)
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'devices': []
                }), 500
        
        @app.route('/api/device/<serial>/info', methods=['GET'])
        def api_device_info(serial):
            try:
                device = detector.get_device_by_serial(serial)
                if not device:
                    return jsonify({
                        'success': False,
                        'error': 'Device not found'
                    }), 404
                
                return jsonify({
                    'success': True,
                    'device': device.to_dict()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @app.route('/api/bypass', methods=['POST'])
        def api_bypass():
            try:
                data = request.get_json()
                serial = data.get('serial')
                method = data.get('method')
                dry_run = data.get('dry_run', False)
                
                if not serial:
                    return jsonify({
                        'success': False,
                        'error': 'Serial number required'
                    }), 400
                
                device = detector.get_device_by_serial(serial)
                if not device:
                    return jsonify({
                        'success': False,
                        'error': 'Device not found'
                    }), 404
                
                if dry_run:
                    # Simulação
                    return jsonify({
                        'success': True,
                        'result': {
                            'status': 'success',
                            'method_used': method or 'simulation',
                            'execution_time': 5.0,
                            'message': 'Simulação executada com sucesso'
                        }
                    })
                
                # Executa bypass real
                result = engine.execute_bypass(device)
                
                return jsonify({
                    'success': result.success,
                    'result': result.to_dict()
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @app.route('/api/stats', methods=['GET'])
        def api_stats():
            try:
                stats = device_db.get_statistics()
                engine_stats = engine.get_engine_statistics()
                
                return jsonify({
                    'success': True,
                    'database': stats,
                    'engine': engine_stats
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @app.route('/api/test', methods=['GET'])
        def api_test():
            try:
                # Executa testes básicos
                deps_ok = check_dependencies()
                devices = detector.scan_usb_devices()
                
                return jsonify({
                    'success': True,
                    'dependencies': deps_ok,
                    'devices_detected': len(devices),
                    'timestamp': time.time()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # Inicia servidor em thread separada
        def run_server():
            app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        console.print("🌐 Servidor API iniciado em http://127.0.0.1:5000", style="green")
        console.print("Pressione Ctrl+C para parar", style="yellow")
        
        # Mantém o processo vivo
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n🛑 Servidor API interrompido", style="yellow")
            
    except ImportError:
        console.print("❌ Flask não instalado. Execute: pip install flask flask-cors", style="red")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Erro ao iniciar servidor API: {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n🛑 Operação interrompida pelo usuário", style="yellow")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n💥 Erro inesperado: {e}", style="red bold")
        logger.exception("Erro inesperado na aplicação")
        sys.exit(1)
