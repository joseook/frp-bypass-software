# FRP Bypass Professional - Developer Guide

## 🛠️ Guia Completo para Desenvolvedores

Este documento fornece informações detalhadas para desenvolvedores que desejam contribuir, modificar ou estender o FRP Bypass Professional.

---

## 📋 Índice

- [Arquitetura do Sistema](#-arquitetura-do-sistema)
- [Ambiente de Desenvolvimento](#-ambiente-de-desenvolvimento)
- [Estrutura do Código](#-estrutura-do-código)
- [APIs e Interfaces](#-apis-e-interfaces)
- [Adicionando Novos Dispositivos](#-adicionando-novos-dispositivos)
- [Criando Novos Métodos de Bypass](#-criando-novos-métodos-de-bypass)
- [Sistema de Cache](#-sistema-de-cache)
- [Testes](#-testes)
- [Build e Deploy](#-build-e-deploy)
- [Contribuição](#-contribuição)

---

## 🏗️ Arquitetura do Sistema

### **Visão Geral**

```
FRP Bypass Professional
├── Core Engine (Python)          # Lógica principal
├── Database System               # Base de dados de dispositivos
├── Communication Layer           # Protocolos ADB/Fastboot/USB
├── Security & Compliance         # Auditoria e conformidade
├── Cache System                  # Otimização de performance
├── CLI Interface                 # Interface de linha de comando
├── GUI Application (Electron)    # Interface gráfica
└── Testing Framework            # Testes automatizados
```

### **Padrões Arquiteturais**

1. **Model-View-Controller (MVC)**
   - **Model**: `core/` e `database/`
   - **View**: `gui/` e CLI output
   - **Controller**: `main.py` e `core/bypass_engine.py`

2. **Plugin Architecture**
   - Métodos de bypass são plugáveis
   - Novos fabricantes podem ser adicionados facilmente
   - Sistema de hooks para extensibilidade

3. **Event-Driven**
   - Comunicação assíncrona entre componentes
   - Sistema de callbacks para UI
   - Logs em tempo real

---

## 💻 Ambiente de Desenvolvimento

### **Requisitos**

```bash
# Python
Python 3.9+
pip 21.0+

# Node.js (para GUI)
Node.js 16+
npm 8+

# Ferramentas de Build
Visual Studio Build Tools (Windows)
Xcode Command Line Tools (macOS)
build-essential (Linux)

# Ferramentas de Desenvolvimento
Git
VS Code ou PyCharm
Android SDK Platform Tools
```

### **Setup Inicial**

```bash
# 1. Clone o repositório
git clone https://github.com/frp-bypass/professional.git
cd frp-software

# 2. Crie ambiente virtual Python
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate     # Windows

# 3. Instale dependências Python
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Configure pre-commit hooks
pre-commit install

# 5. Execute testes
python -m pytest tests/

# 6. Setup GUI (opcional)
cd gui
npm install
cd ..

# 7. Verifique instalação
python main.py test
```

### **Configuração do IDE**

#### **Visual Studio Code**
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/node_modules": true
    }
}
```

#### **PyCharm**
- Interpreter: `./venv/bin/python`
- Test runner: pytest
- Code style: Black
- Linter: Flake8 + Pylint

---

## 📁 Estrutura do Código

### **Diretório Raiz**
```
frp-software/
├── core/                    # Módulos principais
│   ├── __init__.py         # Exports principais
│   ├── device_detection.py # Detecção de dispositivos
│   ├── communication.py    # Protocolos de comunicação
│   ├── bypass_engine.py    # Engine de bypass
│   ├── security.py         # Segurança e auditoria
│   └── cache.py            # Sistema de cache
├── database/               # Base de dados
│   ├── __init__.py
│   ├── device_database.py  # Gerenciador da base
│   └── device_profiles.json # Perfis de dispositivos
├── gui/                    # Interface gráfica
│   ├── src/               # Código fonte React/Electron
│   ├── public/            # Assets públicos
│   └── package.json       # Dependências Node.js
├── tests/                 # Testes automatizados
│   ├── __init__.py
│   ├── conftest.py        # Configuração pytest
│   ├── test_*.py          # Arquivos de teste
│   └── test_runner.py     # Runner customizado
├── docs/                  # Documentação
├── logs/                  # Logs da aplicação
├── cache/                 # Cache persistente
├── main.py               # Interface CLI principal
├── setup.py              # Script de instalação
├── requirements.txt      # Dependências Python
└── README.md            # Documentação principal
```

### **Módulos Core**

#### **device_detection.py**
```python
# Classes principais:
class AndroidDevice:         # Representa um dispositivo
class DeviceDetector:        # Detecta dispositivos USB
class DeviceMode(Enum):      # Modos de operação
class Manufacturer(Enum):    # Fabricantes suportados

# Funções utilitárias:
def quick_scan() -> List[AndroidDevice]
def find_frp_devices() -> List[AndroidDevice]
```

#### **communication.py**
```python
# Classes principais:
class CommunicationManager:   # Gerenciador central
class ADBInterface:          # Interface ADB
class FastbootInterface:     # Interface Fastboot
class USBCommunicator:       # Comunicação USB baixo nível

# Funções utilitárias:
def check_adb_available() -> bool
def check_fastboot_available() -> bool
```

#### **bypass_engine.py**
```python
# Classes principais:
class FRPBypassEngine:       # Engine principal
class BypassMethod:          # Classe base para métodos
class ADBBypassMethod:       # Método via ADB
class FastbootBypassMethod:  # Método via Fastboot
class BypassResult:          # Resultado de bypass
class BypassSession:         # Sessão de bypass
```

---

## 🔌 APIs e Interfaces

### **API Principal - FRPBypassEngine**

```python
from core.bypass_engine import FRPBypassEngine
from core.device_detection import DeviceDetector
from core.communication import CommunicationManager
from database import DeviceDatabase

# Inicialização
detector = DeviceDetector()
comm_manager = CommunicationManager()
device_db = DeviceDatabase()
engine = FRPBypassEngine(device_db, comm_manager)

# Uso básico
devices = detector.scan_usb_devices()
for device in devices:
    if device.is_frp_bypassable:
        result = engine.execute_bypass(device)
        print(f"Bypass result: {result.success}")
```

### **API de Cache**

```python
from core.cache import get_cache_manager, cached

# Cache manager global
cache = get_cache_manager()

# Cache manual
cache.set("key", "value", ttl=3600)
value = cache.get("key")

# Decorador de cache
@cached(ttl=1800)
def expensive_function(param):
    # Função custosa
    return result
```

### **API de Database**

```python
from database import DeviceDatabase, ExploitManager

# Base de dados
db = DeviceDatabase()

# Busca dispositivos
device = db.find_device_by_name("Galaxy S20")
samsung_devices = db.find_devices_by_manufacturer("samsung")

# Gerenciador de exploits
exploit_mgr = ExploitManager(db)
exploits = exploit_mgr.get_exploits_for_device(device_profile)
```

---

## 📱 Adicionando Novos Dispositivos

### **1. Atualizar device_profiles.json**

```json
{
  "manufacturers": {
    "novo_fabricante": {
      "name": "Novo Fabricante",
      "vendor_id": "0x1234",
      "series": {
        "nova_serie": {
          "models": [
            {
              "name": "Novo Modelo X1",
              "codename": "novo_x1",
              "android_versions": ["11", "12", "13"],
              "api_levels": [30, 31, 33],
              "chipset": "Snapdragon 888",
              "supported_methods": ["adb_exploit", "fastboot_method"],
              "frp_bypass_difficulty": "medium",
              "success_rate": 80
            }
          ]
        }
      },
      "common_exploits": [
        {
          "name": "Novo Método Específico",
          "type": "novo_method",
          "description": "Método específico para este fabricante",
          "requirements": ["Requisito 1", "Requisito 2"],
          "steps": ["Passo 1", "Passo 2", "Passo 3"],
          "compatibility": ["nova_serie"],
          "risk_level": "low"
        }
      ]
    }
  }
}
```

### **2. Atualizar DeviceDetector**

```python
# Em device_detection.py, adicione:
VENDOR_IDS = {
    # ... existentes ...
    0x1234: Manufacturer.NOVO_FABRICANTE,
}

# Em Manufacturer enum:
class Manufacturer(Enum):
    # ... existentes ...
    NOVO_FABRICANTE = "novo_fabricante"
```

### **3. Criar Método de Bypass Específico**

```python
# Crie novo arquivo: core/bypass_methods/novo_fabricante.py
from ..bypass_engine import BypassMethod, BypassResult, BypassStatus

class NovoFabricanteBypassMethod(BypassMethod):
    def can_execute(self) -> Tuple[bool, str]:
        # Verificações específicas
        if self.device.manufacturer != Manufacturer.NOVO_FABRICANTE:
            return False, "Dispositivo não é do fabricante esperado"
        
        # Outras verificações...
        return True, "Método disponível"
    
    def execute(self) -> BypassResult:
        # Implementação do bypass
        start_time = time.time()
        self.result.status = BypassStatus.IN_PROGRESS
        
        try:
            # Lógica específica do bypass
            success = self._execute_specific_bypass()
            
            if success:
                self.result.status = BypassStatus.SUCCESS
                self.result.success = True
            else:
                self.result.status = BypassStatus.FAILED
                
        except Exception as e:
            self.result.status = BypassStatus.ERROR
            self.result.error_message = str(e)
        
        finally:
            self.result.execution_time = time.time() - start_time
        
        return self.result
    
    def _execute_specific_bypass(self) -> bool:
        # Implementação específica
        return True
```

### **4. Registrar Novo Método**

```python
# Em bypass_engine.py, adicione ao BypassStrategy:
def _generate_strategy(self) -> None:
    # ... código existente ...
    
    if self.device.manufacturer == Manufacturer.NOVO_FABRICANTE:
        from .bypass_methods.novo_fabricante import NovoFabricanteBypassMethod
        self.methods.append((NovoFabricanteBypassMethod, 0.8))
```

---

## 🔧 Criando Novos Métodos de Bypass

### **Template Base**

```python
from typing import Tuple
import time
from core.bypass_engine import BypassMethod, BypassResult, BypassStatus

class NovoMetodoBypass(BypassMethod):
    """Template para novos métodos de bypass"""
    
    def __init__(self, name: str, device, communication_manager):
        super().__init__(name, device, communication_manager)
        # Inicialização específica
        self.required_mode = DeviceMode.ADB  # ou outro modo
    
    def can_execute(self) -> Tuple[bool, str]:
        """
        Verifica se o método pode ser executado
        
        Returns:
            Tupla (pode_executar, motivo)
        """
        # Verificação de modo
        if self.device.mode != self.required_mode:
            return False, f"Dispositivo deve estar em modo {self.required_mode.value}"
        
        # Verificação de fabricante (se necessário)
        if self.device.manufacturer not in [Manufacturer.SAMSUNG, Manufacturer.LG]:
            return False, "Fabricante não suportado"
        
        # Verificações específicas do método
        try:
            interface = self.comm_manager.get_interface(self.device)
            # Teste de conectividade específico
            test_result = interface.execute_command("test-command")
            if not test_result.success:
                return False, "Falha no teste de conectividade"
        except Exception as e:
            return False, f"Erro ao verificar conectividade: {e}"
        
        return True, "Método disponível"
    
    def execute(self) -> BypassResult:
        """
        Executa o método de bypass
        
        Returns:
            Resultado da execução
        """
        start_time = time.time()
        self.result.status = BypassStatus.IN_PROGRESS
        self.result.add_log(f"Iniciando {self.name}")
        
        try:
            # Etapa 1: Preparação
            if not self.prepare_device():
                raise Exception("Falha na preparação do dispositivo")
            
            # Etapa 2: Execução principal
            success = self._execute_main_logic()
            
            if success:
                # Etapa 3: Verificação
                if self.verify_bypass():
                    self.result.status = BypassStatus.SUCCESS
                    self.result.success = True
                    self.result.add_log("✓ Bypass executado com sucesso")
                else:
                    self.result.status = BypassStatus.FAILED
                    self.result.error_message = "Bypass executado mas FRP ainda ativo"
            else:
                self.result.status = BypassStatus.FAILED
                self.result.error_message = "Falha na execução principal"
                
        except Exception as e:
            self.result.status = BypassStatus.ERROR
            self.result.error_message = str(e)
            self.result.add_log(f"✗ Erro: {e}")
        
        finally:
            self.result.execution_time = time.time() - start_time
            self.result.add_log(f"Método finalizado em {self.result.execution_time:.2f}s")
        
        return self.result
    
    def _execute_main_logic(self) -> bool:
        """
        Lógica principal do método (implementar em subclasses)
        
        Returns:
            True se executado com sucesso
        """
        interface = self.comm_manager.get_interface(self.device)
        
        # Exemplo de implementação
        self.result.add_log("Executando comandos específicos")
        
        # Comando 1
        result1 = interface.execute_command("comando-especifico-1")
        if result1.success:
            self.result.steps_completed.append("comando_1")
            self.result.add_log("✓ Comando 1 executado")
        else:
            self.result.add_log("✗ Falha no comando 1")
            return False
        
        # Comando 2
        result2 = interface.execute_command("comando-especifico-2")
        if result2.success:
            self.result.steps_completed.append("comando_2")
            self.result.add_log("✓ Comando 2 executado")
        else:
            self.result.add_log("✗ Falha no comando 2")
            return False
        
        return True
```

### **Registrando o Método**

```python
# Em bypass_engine.py
from .bypass_methods.novo_metodo import NovoMetodoBypass

class BypassStrategy:
    def _generate_strategy(self) -> None:
        # ... código existente ...
        
        # Adicione condição para novo método
        if self._supports_novo_metodo():
            self.methods.append((NovoMetodoBypass, 0.7))  # prioridade
    
    def _supports_novo_metodo(self) -> bool:
        """Verifica se dispositivo suporta novo método"""
        return (
            self.device.manufacturer in [Manufacturer.SAMSUNG, Manufacturer.LG] and
            self.device.mode == DeviceMode.ADB and
            "novo_metodo" in self.device_profile.supported_methods
        )
```

---

## 🚀 Sistema de Cache

### **Uso do Cache**

```python
from core.cache import get_cache_manager, cached, CacheLevel

# Cache manager
cache = get_cache_manager()

# Cache básico
cache.set("device_info_ABC123", device_data, ttl=1800)
cached_data = cache.get("device_info_ABC123")

# Cache de função
@cached(ttl=3600, level=CacheLevel.BOTH)
def expensive_device_analysis(device_id: str):
    # Análise custosa
    return analysis_result

# Cache específico de dispositivos
cache.device_cache.cache_device_info("ABC123", device_info)
cached_info = cache.device_cache.get_device_info("ABC123")
```

### **Configuração de Cache**

```python
# Configuração customizada
from core.cache import CacheManager

cache_manager = CacheManager(
    cache_dir="custom_cache",
    memory_size=2000  # 2000 entradas em memória
)

# Limpeza manual
cleaned = cache_manager.cleanup_expired()
print(f"Limpas: {cleaned['memory']} memória, {cleaned['persistent']} disco")

# Estatísticas
stats = cache_manager.get_stats()
print(f"Hit rate: {stats['memory']['hit_rate']}%")
```

---

## 🧪 Testes

### **Estrutura de Testes**

```
tests/
├── conftest.py              # Fixtures globais
├── test_device_detection.py # Testes de detecção
├── test_communication.py    # Testes de comunicação
├── test_bypass_engine.py    # Testes do engine
├── test_database.py         # Testes da database
├── test_security.py         # Testes de segurança
├── test_cache.py           # Testes de cache
└── test_runner.py          # Runner customizado
```

### **Executando Testes**

```bash
# Todos os testes
python -m pytest tests/

# Testes específicos
python -m pytest tests/test_device_detection.py -v

# Testes com cobertura
python -m pytest tests/ --cov=core --cov=database

# Testes de integração
python -m pytest tests/ -m integration

# Runner customizado
python tests/test_runner.py --all --html-report
```

### **Criando Novos Testes**

```python
# tests/test_novo_modulo.py
import pytest
from unittest.mock import Mock, patch
from core.novo_modulo import NovaClasse

class TestNovaClasse:
    def setup_method(self):
        """Setup para cada teste"""
        self.nova_classe = NovaClasse()
    
    def test_funcionalidade_basica(self):
        """Testa funcionalidade básica"""
        result = self.nova_classe.metodo_basico()
        assert result is not None
        assert isinstance(result, str)
    
    @patch('core.novo_modulo.funcao_externa')
    def test_com_mock(self, mock_funcao):
        """Teste com mock"""
        mock_funcao.return_value = "valor_mockado"
        
        result = self.nova_classe.metodo_que_usa_funcao_externa()
        
        assert result == "valor_esperado"
        mock_funcao.assert_called_once()
    
    @pytest.mark.integration
    def test_integracao(self):
        """Teste de integração (requer hardware)"""
        # Só executa se hardware disponível
        pass

# Fixtures específicas
@pytest.fixture
def mock_device():
    """Device mockado para testes"""
    device = Mock()
    device.serial = "TEST123"
    device.manufacturer = "samsung"
    return device
```

---

## 📦 Build e Deploy

### **Build Local**

```bash
# Build Python
python setup.py build
python setup.py bdist_wheel

# Build GUI
cd gui
npm run build
npm run build-win  # Windows
npm run build-linux  # Linux
npm run build-mac  # macOS

# Build completo
python build_script.py --all-platforms
```

### **Estrutura de Release**

```
releases/
├── windows/
│   ├── FRP-Bypass-Professional-Setup.exe
│   └── FRP-Bypass-Professional-Portable.zip
├── linux/
│   ├── frp-bypass-professional.AppImage
│   └── frp-bypass-professional.deb
├── macos/
│   └── FRP-Bypass-Professional.dmg
└── source/
    └── frp-bypass-professional-v1.0.0.tar.gz
```

### **CI/CD Pipeline**

```yaml
# .github/workflows/build.yml
name: Build and Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: [3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        python -m pytest tests/ --cov=core --cov=database
    
    - name: Build package
      run: |
        python setup.py build
        python setup.py bdist_wheel

  build-gui:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '16'
    
    - name: Build GUI
      run: |
        cd gui
        npm install
        npm run build
```

---

## 🤝 Contribuição

### **Processo de Contribuição**

1. **Fork** do repositório
2. **Clone** seu fork
3. **Crie branch** para feature: `git checkout -b feature/nova-funcionalidade`
4. **Faça mudanças** e adicione testes
5. **Execute testes**: `python -m pytest tests/`
6. **Commit** mudanças: `git commit -m "feat: adiciona nova funcionalidade"`
7. **Push** para branch: `git push origin feature/nova-funcionalidade`
8. **Abra Pull Request**

### **Padrões de Código**

#### **Python**
```python
# Use Black para formatação
black core/ database/ tests/

# Use Flake8 para linting
flake8 core/ database/ tests/

# Use mypy para type checking
mypy core/ database/

# Docstrings no formato Google
def exemplo_funcao(param: str) -> bool:
    """
    Função de exemplo.
    
    Args:
        param: Parâmetro de exemplo
        
    Returns:
        True se sucesso
        
    Raises:
        ValueError: Se param inválido
    """
    return True
```

#### **Commits**
```bash
# Use Conventional Commits
feat: adiciona suporte para novo fabricante
fix: corrige bug na detecção USB
docs: atualiza documentação da API
test: adiciona testes para cache system
refactor: melhora estrutura do bypass engine
perf: otimiza consultas na database
```

### **Code Review**

#### **Checklist do Reviewer**
- [ ] Código segue padrões estabelecidos
- [ ] Testes cobrem funcionalidade nova/alterada
- [ ] Documentação foi atualizada
- [ ] Não quebra compatibilidade backward
- [ ] Performance não foi degradada
- [ ] Segurança foi considerada
- [ ] Logs apropriados foram adicionados

#### **Checklist do Contributor**
- [ ] Branch atualizada com main
- [ ] Testes passam localmente
- [ ] Linting/formatação OK
- [ ] Documentação atualizada
- [ ] CHANGELOG.md atualizado
- [ ] PR description é clara

---

## 🔍 Debugging

### **Logs de Debug**

```python
# Configuração de logging
import logging
from loguru import logger

# Nível debug
logger.add("debug.log", level="DEBUG")

# Logs estruturados
logger.bind(device_id="ABC123", method="adb_bypass").info("Starting bypass")
```

### **Profiling**

```python
# Profile de performance
import cProfile
import pstats

# Profile função específica
cProfile.run('bypass_function()', 'profile_stats')
stats = pstats.Stats('profile_stats')
stats.sort_stats('cumulative').print_stats(10)

# Memory profiling
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Função que consome memória
    pass
```

### **Debugging GUI**

```bash
# Electron DevTools
cd gui
npm run dev  # Abre com DevTools

# React DevTools
# Instalar extensão React DevTools no Chrome
```

---

## 📚 Recursos Adicionais

### **Documentação Interna**
- `docs/API_REFERENCE.md` - Referência completa da API
- `docs/ARCHITECTURE.md` - Arquitetura detalhada
- `docs/SECURITY.md` - Considerações de segurança
- `docs/PERFORMANCE.md` - Otimização de performance

### **Ferramentas Recomendadas**
- **IDE**: VS Code, PyCharm
- **Git GUI**: GitKraken, SourceTree
- **API Testing**: Postman, Insomnia
- **Database**: DB Browser for SQLite
- **Monitoring**: htop, Task Manager

### **Comunidade**
- **Discord**: https://discord.gg/frp-bypass-pro
- **Forum**: https://forum.frp-bypass-professional.com
- **Stack Overflow**: Tag `frp-bypass-professional`

---

## 🎯 Roadmap de Desenvolvimento

### **v1.1.0 (Próxima Release)**
- [ ] API REST completa
- [ ] Sistema de plugins
- [ ] Suporte a mais fabricantes
- [ ] Interface web

### **v1.2.0**
- [ ] Machine Learning para detecção
- [ ] Bypass automático inteligente
- [ ] Relatórios avançados
- [ ] Integração com CI/CD

### **v2.0.0**
- [ ] Arquitetura distribuída
- [ ] Suporte a dispositivos IoT
- [ ] Blockchain para auditoria
- [ ] IA para novos métodos

---

**Happy Coding! 🚀**

Para dúvidas específicas de desenvolvimento:
- 📧 **Email**: dev@frp-bypass-professional.com
- 💬 **Chat**: Canal #development no Discord
- 📝 **Issues**: GitHub Issues para bugs e features
