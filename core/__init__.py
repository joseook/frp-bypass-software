"""
FRP Bypass Professional - Core Module
=====================================

Este módulo contém os componentes principais do sistema de bypass FRP.

Módulos disponíveis:
- device_detection: Detecção e identificação de dispositivos Android
- communication: Protocolo de comunicação USB/ADB/Fastboot
- bypass_engine: Engine principal de bypass FRP
- security: Sistema de segurança e conformidade

Autor: FRP Bypass Professional Team
Versão: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "FRP Bypass Professional Team"

# Imports principais
from .device_detection import DeviceDetector, AndroidDevice
from .communication import USBCommunicator, ADBInterface, FastbootInterface
from .bypass_engine import FRPBypassEngine

__all__ = [
    'DeviceDetector',
    'AndroidDevice', 
    'USBCommunicator',
    'ADBInterface',
    'FastbootInterface',
    'FRPBypassEngine'
]
