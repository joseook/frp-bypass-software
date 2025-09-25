"""
Database Module
===============

Sistema de gerenciamento de base de dados para dispositivos e exploits FRP.

Classes:
- DeviceDatabase: Gerenciador da base de dados de dispositivos
- ExploitManager: Gerenciador de exploits e métodos de bypass
"""

from .device_database import DeviceDatabase, ExploitManager

__all__ = ['DeviceDatabase', 'ExploitManager']
