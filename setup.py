#!/usr/bin/env python3
"""
FRP Bypass Professional - Setup Script
======================================

Script de configuração e instalação do FRP Bypass Professional.
Instala dependências, configura ambiente e realiza testes iniciais.

Uso:
    python setup.py install    # Instalação completa
    python setup.py check      # Verificação de dependências
    python setup.py demo       # Configuração de demonstração
"""

import sys
import os
import subprocess
import platform
from pathlib import Path
import json
import time
from typing import List, Dict, Any, Optional

# Adiciona diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.panel import Panel
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Console setup
if RICH_AVAILABLE:
    console = Console()
else:
    class SimpleConsole:
        def print(self, text, style=None):
            print(text)
    console = SimpleConsole()


class SetupManager:
    """Gerenciador de setup do FRP Bypass Professional"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.python_executable = sys.executable
        self.os_type = platform.system().lower()
        self.requirements_installed = False
        
    def print_banner(self):
        """Imprime banner do setup"""
        banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║         FRP BYPASS PROFESSIONAL - SETUP WIZARD               ║
║                        Version 1.0.0                         ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
        console.print(banner, style="bold cyan" if RICH_AVAILABLE else None)
    
    def check_python_version(self) -> bool:
        """Verifica versão do Python"""
        console.print("🐍 Verificando versão do Python...", style="blue" if RICH_AVAILABLE else None)
        
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 9):
            console.print(f"❌ Python {version.major}.{version.minor} não é suportado", style="red" if RICH_AVAILABLE else None)
            console.print("   Requer Python 3.9 ou superior", style="yellow" if RICH_AVAILABLE else None)
            return False
        
        console.print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK", style="green" if RICH_AVAILABLE else None)
        return True
    
    def check_system_requirements(self) -> Dict[str, bool]:
        """Verifica requisitos do sistema"""
        console.print("💻 Verificando requisitos do sistema...", style="blue" if RICH_AVAILABLE else None)
        
        requirements = {
            "python_version": self.check_python_version(),
            "pip_available": self._check_pip(),
            "git_available": self._check_git(),
            "adb_available": self._check_adb(),
            "fastboot_available": self._check_fastboot()
        }
        
        return requirements
    
    def _check_pip(self) -> bool:
        """Verifica se pip está disponível"""
        try:
            subprocess.run([self.python_executable, "-m", "pip", "--version"], 
                         capture_output=True, check=True)
            console.print("✅ pip - OK", style="green" if RICH_AVAILABLE else None)
            return True
        except subprocess.CalledProcessError:
            console.print("❌ pip não encontrado", style="red" if RICH_AVAILABLE else None)
            return False
    
    def _check_git(self) -> bool:
        """Verifica se Git está disponível"""
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True)
            console.print("✅ Git - OK", style="green" if RICH_AVAILABLE else None)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            console.print("⚠️  Git não encontrado (opcional)", style="yellow" if RICH_AVAILABLE else None)
            return False
    
    def _check_adb(self) -> bool:
        """Verifica se ADB está disponível"""
        try:
            subprocess.run(["adb", "version"], capture_output=True, check=True)
            console.print("✅ ADB - OK", style="green" if RICH_AVAILABLE else None)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            console.print("❌ ADB não encontrado", style="red" if RICH_AVAILABLE else None)
            return False
    
    def _check_fastboot(self) -> bool:
        """Verifica se Fastboot está disponível"""
        try:
            subprocess.run(["fastboot", "--version"], capture_output=True, check=True)
            console.print("✅ Fastboot - OK", style="green" if RICH_AVAILABLE else None)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            console.print("❌ Fastboot não encontrado", style="red" if RICH_AVAILABLE else None)
            return False
    
    def install_python_dependencies(self) -> bool:
        """Instala dependências Python"""
        console.print("📦 Instalando dependências Python...", style="blue" if RICH_AVAILABLE else None)
        
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            console.print("❌ Arquivo requirements.txt não encontrado", style="red" if RICH_AVAILABLE else None)
            return False
        
        try:
            if RICH_AVAILABLE:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task("Instalando dependências...", total=None)
                    
                    result = subprocess.run([
                        self.python_executable, "-m", "pip", "install", "-r", str(requirements_file)
                    ], capture_output=True, text=True)
                    
                    progress.update(task, completed=True)
            else:
                print("Instalando dependências...")
                result = subprocess.run([
                    self.python_executable, "-m", "pip", "install", "-r", str(requirements_file)
                ], capture_output=True, text=True)
            
            if result.returncode == 0:
                console.print("✅ Dependências instaladas com sucesso", style="green" if RICH_AVAILABLE else None)
                self.requirements_installed = True
                return True
            else:
                console.print("❌ Erro ao instalar dependências:", style="red" if RICH_AVAILABLE else None)
                console.print(result.stderr, style="dim" if RICH_AVAILABLE else None)
                return False
                
        except Exception as e:
            console.print(f"❌ Erro durante instalação: {e}", style="red" if RICH_AVAILABLE else None)
            return False
    
    def setup_directories(self) -> bool:
        """Cria diretórios necessários"""
        console.print("📁 Configurando diretórios...", style="blue" if RICH_AVAILABLE else None)
        
        directories = ["logs", "temp", "exports", "backups"]
        
        try:
            for directory in directories:
                dir_path = self.project_root / directory
                dir_path.mkdir(exist_ok=True)
                console.print(f"  ✓ {directory}/", style="dim" if RICH_AVAILABLE else None)
            
            console.print("✅ Diretórios configurados", style="green" if RICH_AVAILABLE else None)
            return True
            
        except Exception as e:
            console.print(f"❌ Erro ao criar diretórios: {e}", style="red" if RICH_AVAILABLE else None)
            return False
    
    def create_demo_license(self) -> bool:
        """Cria licença de demonstração"""
        console.print("🔑 Criando licença de demonstração...", style="blue" if RICH_AVAILABLE else None)
        
        try:
            if not self.requirements_installed:
                console.print("⚠️  Dependências não instaladas, pulando criação de licença", style="yellow" if RICH_AVAILABLE else None)
                return False
            
            from core.security import create_demo_license
            
            if create_demo_license():
                console.print("✅ Licença de demonstração criada", style="green" if RICH_AVAILABLE else None)
                console.print("  Usuário: Demo User", style="dim" if RICH_AVAILABLE else None)
                console.print("  Organização: Demo Organization", style="dim" if RICH_AVAILABLE else None)
                console.print("  Válida por: 365 dias", style="dim" if RICH_AVAILABLE else None)
                return True
            else:
                console.print("❌ Erro ao criar licença de demonstração", style="red" if RICH_AVAILABLE else None)
                return False
                
        except Exception as e:
            console.print(f"❌ Erro durante criação da licença: {e}", style="red" if RICH_AVAILABLE else None)
            return False
    
    def run_initial_tests(self) -> bool:
        """Executa testes iniciais"""
        console.print("🧪 Executando testes iniciais...", style="blue" if RICH_AVAILABLE else None)
        
        if not self.requirements_installed:
            console.print("⚠️  Dependências não instaladas, pulando testes", style="yellow" if RICH_AVAILABLE else None)
            return False
        
        try:
            # Teste de importação dos módulos principais
            console.print("  Testando importações...", style="dim" if RICH_AVAILABLE else None)
            
            from core.device_detection import DeviceDetector
            from core.communication import CommunicationManager
            from database import DeviceDatabase
            from core.bypass_engine import FRPBypassEngine
            
            console.print("  ✓ Módulos importados", style="dim" if RICH_AVAILABLE else None)
            
            # Teste de inicialização
            console.print("  Testando inicializações...", style="dim" if RICH_AVAILABLE else None)
            
            detector = DeviceDetector()
            comm_manager = CommunicationManager()
            device_db = DeviceDatabase()
            engine = FRPBypassEngine(device_db, comm_manager)
            
            console.print("  ✓ Componentes inicializados", style="dim" if RICH_AVAILABLE else None)
            
            # Teste da base de dados
            stats = device_db.get_statistics()
            console.print(f"  ✓ Base de dados: {stats['total_devices']} dispositivos", style="dim" if RICH_AVAILABLE else None)
            
            console.print("✅ Testes iniciais aprovados", style="green" if RICH_AVAILABLE else None)
            return True
            
        except Exception as e:
            console.print(f"❌ Erro nos testes iniciais: {e}", style="red" if RICH_AVAILABLE else None)
            return False
    
    def create_config_file(self) -> bool:
        """Cria arquivo de configuração"""
        console.print("⚙️  Criando arquivo de configuração...", style="blue" if RICH_AVAILABLE else None)
        
        config = {
            "version": "1.0.0",
            "setup_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": platform.platform(),
            "directories": {
                "logs": "logs/",
                "temp": "temp/",
                "exports": "exports/",
                "backups": "backups/"
            },
            "features": {
                "adb_available": self._check_adb(),
                "fastboot_available": self._check_fastboot(),
                "demo_license": True
            },
            "security": {
                "audit_enabled": True,
                "compliance_checks": True,
                "license_validation": True
            }
        }
        
        try:
            config_file = self.project_root / "config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            console.print("✅ Configuração salva em config.json", style="green" if RICH_AVAILABLE else None)
            return True
            
        except Exception as e:
            console.print(f"❌ Erro ao criar configuração: {e}", style="red" if RICH_AVAILABLE else None)
            return False
    
    def show_installation_summary(self, results: Dict[str, bool]):
        """Mostra resumo da instalação"""
        console.print("\n📋 Resumo da Instalação:", style="bold blue" if RICH_AVAILABLE else None)
        
        if RICH_AVAILABLE:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Componente", style="cyan")
            table.add_column("Status", style="white")
            table.add_column("Observações", style="dim")
            
            for component, status in results.items():
                status_text = "✅ OK" if status else "❌ Falhou"
                observations = self._get_component_observations(component, status)
                table.add_row(component.replace('_', ' ').title(), status_text, observations)
            
            console.print(table)
        else:
            for component, status in results.items():
                status_text = "OK" if status else "FALHOU"
                print(f"  {component.replace('_', ' ').title()}: {status_text}")
    
    def _get_component_observations(self, component: str, status: bool) -> str:
        """Obtém observações sobre componente"""
        observations = {
            "python_version": "Python 3.9+ necessário" if not status else "Versão compatível",
            "pip_available": "Necessário para instalar dependências" if not status else "Gerenciador de pacotes OK",
            "dependencies": "Algumas funcionalidades limitadas" if not status else "Todas as dependências instaladas",
            "directories": "Logs e exports podem não funcionar" if not status else "Estrutura de diretórios OK",
            "demo_license": "Use licença própria" if not status else "Licença demo válida por 365 dias",
            "initial_tests": "Verifique erros acima" if not status else "Sistema funcionando corretamente",
            "config_file": "Configuração manual necessária" if not status else "Configuração automática criada",
            "adb_available": "Instale Android SDK Platform Tools" if not status else "ADB funcionando",
            "fastboot_available": "Instale Android SDK Platform Tools" if not status else "Fastboot funcionando"
        }
        
        return observations.get(component, "")
    
    def show_next_steps(self):
        """Mostra próximos passos após instalação"""
        next_steps = """
🚀 PRÓXIMOS PASSOS:

1. Instale Android SDK Platform Tools (se não instalado):
   • Windows: https://developer.android.com/studio/releases/platform-tools
   • Linux: sudo apt install android-tools-adb android-tools-fastboot
   • macOS: brew install android-platform-tools

2. Conecte um dispositivo Android e teste:
   python main.py detect

3. Execute testes completos:
   python main.py test

4. Para usar o software:
   python main.py bypass --help

⚠️  IMPORTANTE:
• Use apenas em dispositivos próprios ou com autorização
• Leia toda a documentação antes de usar
• Mantenha logs de auditoria para conformidade legal

📚 Documentação completa: docs/README.md
"""
        
        console.print(next_steps, style="yellow" if RICH_AVAILABLE else None)
    
    def full_installation(self) -> bool:
        """Executa instalação completa"""
        self.print_banner()
        
        console.print("🔧 Iniciando instalação completa...\n", style="bold green" if RICH_AVAILABLE else None)
        
        results = {}
        
        # Verifica requisitos do sistema
        system_reqs = self.check_system_requirements()
        results.update(system_reqs)
        
        # Se Python não está OK, para aqui
        if not system_reqs["python_version"]:
            console.print("\n❌ Instalação interrompida: Python incompatível", style="red bold" if RICH_AVAILABLE else None)
            return False
        
        print()  # Linha em branco
        
        # Instala dependências Python
        results["dependencies"] = self.install_python_dependencies()
        
        # Configura diretórios
        results["directories"] = self.setup_directories()
        
        # Cria licença demo
        results["demo_license"] = self.create_demo_license()
        
        # Executa testes iniciais
        results["initial_tests"] = self.run_initial_tests()
        
        # Cria arquivo de configuração
        results["config_file"] = self.create_config_file()
        
        # Mostra resumo
        print()  # Linha em branco
        self.show_installation_summary(results)
        
        # Verifica se instalação foi bem-sucedida
        critical_components = ["python_version", "dependencies", "directories", "initial_tests"]
        success = all(results.get(comp, False) for comp in critical_components)
        
        if success:
            console.print("\n🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!", style="bold green" if RICH_AVAILABLE else None)
            self.show_next_steps()
        else:
            console.print("\n⚠️  INSTALAÇÃO PARCIALMENTE CONCLUÍDA", style="bold yellow" if RICH_AVAILABLE else None)
            console.print("Alguns componentes falharam. Verifique os erros acima.", style="yellow" if RICH_AVAILABLE else None)
        
        return success


def main():
    """Função principal do setup"""
    if len(sys.argv) < 2:
        print("Uso: python setup.py [install|check|demo]")
        print("  install - Instalação completa")
        print("  check   - Verificação de dependências apenas")
        print("  demo    - Configuração de demonstração")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    setup_manager = SetupManager()
    
    if command == "install":
        setup_manager.full_installation()
    
    elif command == "check":
        setup_manager.print_banner()
        requirements = setup_manager.check_system_requirements()
        
        print("\n📊 Resultado da Verificação:")
        for component, status in requirements.items():
            status_text = "✅ OK" if status else "❌ Falhou"
            print(f"  {component.replace('_', ' ').title()}: {status_text}")
    
    elif command == "demo":
        setup_manager.print_banner()
        console.print("🧪 Configurando demonstração...\n", style="bold blue" if RICH_AVAILABLE else None)
        
        # Verificações mínimas
        if not setup_manager.check_python_version():
            sys.exit(1)
        
        # Instala dependências
        if setup_manager.install_python_dependencies():
            setup_manager.setup_directories()
            setup_manager.create_demo_license()
            setup_manager.create_config_file()
            
            console.print("\n✅ Configuração de demonstração concluída!", style="green bold" if RICH_AVAILABLE else None)
            console.print("Execute: python main.py test", style="yellow" if RICH_AVAILABLE else None)
        else:
            console.print("\n❌ Falha na configuração", style="red bold" if RICH_AVAILABLE else None)
    
    else:
        print(f"Comando desconhecido: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
