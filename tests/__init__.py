"""
Test Suite for FRP Bypass Professional
======================================

Conjunto completo de testes para validação do sistema FRP Bypass Professional.

Módulos de teste:
- test_device_detection: Testes de detecção de dispositivos
- test_communication: Testes de protocolos de comunicação
- test_bypass_engine: Testes do engine de bypass
- test_database: Testes da base de dados
- test_security: Testes de segurança e auditoria
"""

import sys
import os
from pathlib import Path

# Adiciona diretório raiz ao path para imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

__version__ = "1.0.0"
__author__ = "FRP Bypass Professional Team"
