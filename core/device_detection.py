"""
Device Detection Module
======================

Sistema de detecção e identificação de dispositivos Android conectados via USB.
Suporte para múltiplos fabricantes e modos de operação.

Classes:
- AndroidDevice: Representa um dispositivo Android detectado
- DeviceDetector: Sistema de detecção de dispositivos USB
"""

import usb.core
import usb.util
import subprocess
import re
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from loguru import logger


class DeviceMode(Enum):
    """Modos de operação do dispositivo Android"""
    UNKNOWN = "unknown"
    NORMAL = "normal"
    ADB = "adb"
    FASTBOOT = "fastboot"
    RECOVERY = "recovery"
    DOWNLOAD = "download"  # Samsung Download Mode
    EDL = "edl"           # Qualcomm Emergency Download Mode
    SIDELOAD = "sideload"


class Manufacturer(Enum):
    """Fabricantes suportados"""
    SAMSUNG = "samsung"
    LG = "lg"
    XIAOMI = "xiaomi"
    GOOGLE = "google"
    HUAWEI = "huawei"
    ONEPLUS = "oneplus"
    MOTOROLA = "motorola"
    SONY = "sony"
    UNKNOWN = "unknown"


@dataclass
class AndroidDevice:
    """Representa um dispositivo Android detectado"""
    
    # Informações básicas
    vendor_id: int
    product_id: int
    manufacturer: Manufacturer
    model: str
    serial: str
    
    # Estado do dispositivo
    mode: DeviceMode
    android_version: Optional[str] = None
    api_level: Optional[int] = None
    build_id: Optional[str] = None
    
    # Informações FRP
    frp_locked: Optional[bool] = None
    google_account: Optional[str] = None
    
    # Informações técnicas
    bootloader_locked: Optional[bool] = None
    root_access: Optional[bool] = None
    usb_debugging: Optional[bool] = None
    
    # Metadados
    detection_time: float = 0.0
    
    def __post_init__(self):
        """Inicialização pós-criação"""
        if self.detection_time == 0.0:
            self.detection_time = time.time()
    
    @property
    def device_id(self) -> str:
        """ID único do dispositivo"""
        return f"{self.manufacturer.value}_{self.model}_{self.serial}"
    
    @property
    def is_frp_bypassable(self) -> bool:
        """Verifica se o dispositivo pode ter FRP bypassed"""
        if self.frp_locked is None:
            return False
        return self.frp_locked and self.mode in [
            DeviceMode.ADB, 
            DeviceMode.FASTBOOT, 
            DeviceMode.DOWNLOAD,
            DeviceMode.EDL
        ]
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'vendor_id': hex(self.vendor_id),
            'product_id': hex(self.product_id),
            'manufacturer': self.manufacturer.value,
            'model': self.model,
            'serial': self.serial,
            'mode': self.mode.value,
            'android_version': self.android_version,
            'api_level': self.api_level,
            'build_id': self.build_id,
            'frp_locked': self.frp_locked,
            'google_account': self.google_account,
            'bootloader_locked': self.bootloader_locked,
            'root_access': self.root_access,
            'usb_debugging': self.usb_debugging,
            'detection_time': self.detection_time,
            'device_id': self.device_id,
            'is_frp_bypassable': self.is_frp_bypassable
        }


class DeviceDetector:
    """Sistema de detecção de dispositivos Android via USB"""
    
    # Vendor IDs dos principais fabricantes
    VENDOR_IDS = {
        0x04e8: Manufacturer.SAMSUNG,    # Samsung
        0x1004: Manufacturer.LG,         # LG Electronics
        0x2717: Manufacturer.XIAOMI,     # Xiaomi
        0x18d1: Manufacturer.GOOGLE,     # Google
        0x12d1: Manufacturer.HUAWEI,     # Huawei
        0x2a70: Manufacturer.ONEPLUS,    # OnePlus
        0x22b8: Manufacturer.MOTOROLA,   # Motorola
        0x0fce: Manufacturer.SONY,       # Sony
    }
    
    # Product IDs para diferentes modos (Samsung como exemplo)
    SAMSUNG_PRODUCT_IDS = {
        0x6860: DeviceMode.ADB,          # ADB mode
        0x685d: DeviceMode.FASTBOOT,     # Fastboot mode
        0x6877: DeviceMode.DOWNLOAD,     # Download mode
        0x685c: DeviceMode.RECOVERY,     # Recovery mode
        0x6859: DeviceMode.NORMAL,       # Normal mode
    }
    
    # Product IDs para LG
    LG_PRODUCT_IDS = {
        0x618e: DeviceMode.ADB,          # LG ADB mode
        0x6000: DeviceMode.NORMAL,       # LG Normal mode
        0x633e: DeviceMode.FASTBOOT,     # LG Fastboot mode
        0x6344: DeviceMode.RECOVERY,     # LG Recovery mode
    }
    
    def __init__(self):
        """Inicializa o detector de dispositivos"""
        self.detected_devices: List[AndroidDevice] = []
        logger.info("DeviceDetector inicializado")
    
    def scan_usb_devices(self) -> List[AndroidDevice]:
        """
        Escaneia dispositivos USB conectados
        
        Returns:
            Lista de dispositivos Android detectados
        """
        devices = []
        
        try:
            # Encontra todos os dispositivos USB
            usb_devices = usb.core.find(find_all=True)
            
            for usb_device in usb_devices:
                if usb_device.idVendor in self.VENDOR_IDS:
                    android_device = self._analyze_usb_device(usb_device)
                    if android_device:
                        devices.append(android_device)
                        logger.info(f"Dispositivo detectado: {android_device.device_id}")
            
        except Exception as e:
            logger.error(f"Erro ao escanear dispositivos USB: {e}")
        
        self.detected_devices = devices
        return devices
    
    def _analyze_usb_device(self, usb_device) -> Optional[AndroidDevice]:
        """
        Analisa um dispositivo USB específico
        
        Args:
            usb_device: Objeto USB device
            
        Returns:
            AndroidDevice se for um dispositivo Android válido
        """
        try:
            vendor_id = usb_device.idVendor
            product_id = usb_device.idProduct
            
            # Identifica o fabricante
            manufacturer = self.VENDOR_IDS.get(vendor_id, Manufacturer.UNKNOWN)
            
            # Tenta obter o serial number
            serial = self._get_device_serial(usb_device)
            
            # Determina o modo do dispositivo
            mode = self._detect_device_mode(vendor_id, product_id)
            
            # Cria o objeto AndroidDevice básico
            device = AndroidDevice(
                vendor_id=vendor_id,
                product_id=product_id,
                manufacturer=manufacturer,
                model="Unknown",  # Será determinado posteriormente
                serial=serial or "Unknown",
                mode=mode
            )
            
            # Enriquece com informações adicionais se possível
            self._enrich_device_info(device)
            
            return device
            
        except Exception as e:
            logger.error(f"Erro ao analisar dispositivo USB: {e}")
            return None
    
    def _get_device_serial(self, usb_device) -> Optional[str]:
        """
        Obtém o número serial do dispositivo USB
        
        Args:
            usb_device: Objeto USB device
            
        Returns:
            Serial number ou None se não conseguir obter
        """
        try:
            if usb_device.iSerialNumber:
                return usb.util.get_string(usb_device, usb_device.iSerialNumber)
        except Exception as e:
            logger.debug(f"Não foi possível obter serial USB: {e}")
        
        return None
    
    def _detect_device_mode(self, vendor_id: int, product_id: int) -> DeviceMode:
        """
        Detecta o modo de operação do dispositivo
        
        Args:
            vendor_id: ID do fabricante
            product_id: ID do produto
            
        Returns:
            Modo detectado do dispositivo
        """
        # Samsung specific detection
        if vendor_id == 0x04e8:  # Samsung
            return self.SAMSUNG_PRODUCT_IDS.get(product_id, DeviceMode.UNKNOWN)
        
        # LG specific detection
        if vendor_id == 0x1004:  # LG Electronics
            return self.LG_PRODUCT_IDS.get(product_id, DeviceMode.UNKNOWN)
        
        # Para outros fabricantes, tentamos detectar via ADB/Fastboot
        return self._detect_mode_via_tools()
    
    def _detect_mode_via_tools(self) -> DeviceMode:
        """
        Detecta modo usando ferramentas ADB/Fastboot
        
        Returns:
            Modo detectado
        """
        # Verifica se há dispositivos ADB
        try:
            result = subprocess.run(
                ['adb', 'devices'], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode == 0 and "device" in result.stdout:
                return DeviceMode.ADB
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Verifica se há dispositivos Fastboot
        try:
            result = subprocess.run(
                ['fastboot', 'devices'], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return DeviceMode.FASTBOOT
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return DeviceMode.UNKNOWN
    
    def _enrich_device_info(self, device: AndroidDevice) -> None:
        """
        Enriquece as informações do dispositivo usando ADB/Fastboot
        
        Args:
            device: Dispositivo para enriquecer informações
        """
        if device.mode == DeviceMode.ADB:
            self._get_adb_info(device)
        elif device.mode == DeviceMode.FASTBOOT:
            self._get_fastboot_info(device)
    
    def _get_adb_info(self, device: AndroidDevice) -> None:
        """
        Obtém informações via ADB
        
        Args:
            device: Dispositivo para obter informações
        """
        try:
            # Modelo do dispositivo
            result = subprocess.run(
                ['adb', '-s', device.serial, 'shell', 'getprop', 'ro.product.model'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                device.model = result.stdout.strip()
            
            # Versão do Android
            result = subprocess.run(
                ['adb', '-s', device.serial, 'shell', 'getprop', 'ro.build.version.release'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                device.android_version = result.stdout.strip()
            
            # API Level
            result = subprocess.run(
                ['adb', '-s', device.serial, 'shell', 'getprop', 'ro.build.version.sdk'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                try:
                    device.api_level = int(result.stdout.strip())
                except ValueError:
                    pass
            
            # Build ID
            result = subprocess.run(
                ['adb', '-s', device.serial, 'shell', 'getprop', 'ro.build.id'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                device.build_id = result.stdout.strip()
            
            # Status do USB Debugging
            device.usb_debugging = True  # Se conseguimos conectar via ADB
            
            # Verifica status FRP
            self._check_frp_status(device)
            
        except Exception as e:
            logger.error(f"Erro ao obter informações ADB: {e}")
    
    def _get_fastboot_info(self, device: AndroidDevice) -> None:
        """
        Obtém informações via Fastboot
        
        Args:
            device: Dispositivo para obter informações
        """
        try:
            # Modelo do dispositivo
            result = subprocess.run(
                ['fastboot', '-s', device.serial, 'getvar', 'product'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                # Fastboot output vai para stderr
                output = result.stderr
                match = re.search(r'product:\s*(.+)', output)
                if match:
                    device.model = match.group(1).strip()
            
            # Status do bootloader
            result = subprocess.run(
                ['fastboot', '-s', device.serial, 'getvar', 'unlocked'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                output = result.stderr
                device.bootloader_locked = 'yes' not in output.lower()
                
        except Exception as e:
            logger.error(f"Erro ao obter informações Fastboot: {e}")
    
    def _check_frp_status(self, device: AndroidDevice) -> None:
        """
        Verifica o status do FRP no dispositivo
        
        Args:
            device: Dispositivo para verificar FRP
        """
        try:
            # Verifica se há conta Google configurada
            result = subprocess.run(
                ['adb', '-s', device.serial, 'shell', 'dumpsys', 'account'],
                capture_output=True, text=True, timeout=15
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                
                # Procura por contas Google
                google_accounts = re.findall(r'com\.google.*?name=([^\s,}]+)', output)
                if google_accounts:
                    device.google_account = google_accounts[0]
                    device.frp_locked = True
                else:
                    device.frp_locked = False
                    
                # Verifica especificamente FRP
                if 'frp' in output or 'factory reset protection' in output:
                    device.frp_locked = True
            
            # Para dispositivos LG, verifica também Secure Startup
            if device.manufacturer == Manufacturer.LG:
                self._check_lg_secure_startup(device)
                    
        except Exception as e:
            logger.error(f"Erro ao verificar status FRP: {e}")
    
    def _check_lg_secure_startup(self, device: AndroidDevice) -> None:
        """
        Verifica se dispositivo LG tem Secure Startup ativo
        
        Args:
            device: Dispositivo LG para verificar
        """
        try:
            # Verifica configurações de criptografia
            result = subprocess.run(
                ['adb', '-s', device.serial, 'shell', 'getprop', 'ro.crypto.state'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                crypto_state = result.stdout.strip().lower()
                if crypto_state == 'encrypted':
                    # Verifica se requer senha no boot
                    pwd_result = subprocess.run(
                        ['adb', '-s', device.serial, 'shell', 'settings', 'get', 'global', 'require_password_to_decrypt'],
                        capture_output=True, text=True, timeout=10
                    )
                    
                    if pwd_result.returncode == 0 and pwd_result.stdout.strip() == '1':
                        device.frp_locked = True
                        logger.info(f"Dispositivo {device.device_id} tem Secure Startup ativo")
                        
        except Exception as e:
            logger.debug(f"Erro ao verificar Secure Startup: {e}")
    
    def get_device_by_serial(self, serial: str) -> Optional[AndroidDevice]:
        """
        Busca dispositivo pelo serial
        
        Args:
            serial: Serial number do dispositivo
            
        Returns:
            AndroidDevice se encontrado
        """
        for device in self.detected_devices:
            if device.serial == serial:
                return device
        return None
    
    def get_frp_locked_devices(self) -> List[AndroidDevice]:
        """
        Retorna apenas dispositivos com FRP ativo
        
        Returns:
            Lista de dispositivos com FRP bloqueado
        """
        return [
            device for device in self.detected_devices 
            if device.frp_locked is True
        ]
    
    def continuous_scan(self, interval: int = 5) -> None:
        """
        Inicia escaneamento contínuo de dispositivos
        
        Args:
            interval: Intervalo em segundos entre scans
        """
        logger.info(f"Iniciando escaneamento contínuo (intervalo: {interval}s)")
        
        while True:
            try:
                devices = self.scan_usb_devices()
                logger.info(f"Scan completo: {len(devices)} dispositivos encontrados")
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("Escaneamento interrompido pelo usuário")
                break
            except Exception as e:
                logger.error(f"Erro durante escaneamento contínuo: {e}")
                time.sleep(interval)


# Funções utilitárias
def quick_scan() -> List[AndroidDevice]:
    """
    Função de conveniência para scan rápido
    
    Returns:
        Lista de dispositivos detectados
    """
    detector = DeviceDetector()
    return detector.scan_usb_devices()


def find_frp_devices() -> List[AndroidDevice]:
    """
    Função de conveniência para encontrar dispositivos com FRP
    
    Returns:
        Lista de dispositivos com FRP bloqueado
    """
    detector = DeviceDetector()
    detector.scan_usb_devices()
    return detector.get_frp_locked_devices()


if __name__ == "__main__":
    # Teste básico do módulo
    print("=== FRP Bypass Professional - Device Detection ===")
    
    detector = DeviceDetector()
    devices = detector.scan_usb_devices()
    
    if devices:
        print(f"\n{len(devices)} dispositivo(s) detectado(s):")
        for device in devices:
            print(f"\n- {device.manufacturer.value.upper()} {device.model}")
            print(f"  Serial: {device.serial}")
            print(f"  Modo: {device.mode.value}")
            print(f"  FRP Bloqueado: {device.frp_locked}")
            print(f"  Android: {device.android_version}")
    else:
        print("\nNenhum dispositivo Android detectado.")
