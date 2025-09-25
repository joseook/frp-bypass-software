"""
Testes para módulo de detecção de dispositivos
==============================================

Testa todas as funcionalidades do sistema de detecção de dispositivos Android.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import usb.core

from core.device_detection import (
    DeviceDetector, AndroidDevice, DeviceMode, Manufacturer,
    quick_scan, find_frp_devices
)


class TestAndroidDevice:
    """Testes para a classe AndroidDevice"""
    
    def test_device_creation(self):
        """Testa criação de dispositivo Android"""
        device = AndroidDevice(
            vendor_id=0x04e8,
            product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG,
            model="Galaxy S20",
            serial="test123456",
            mode=DeviceMode.ADB,
            frp_locked=True
        )
        
        assert device.vendor_id == 0x04e8
        assert device.manufacturer == Manufacturer.SAMSUNG
        assert device.model == "Galaxy S20"
        assert device.device_id == "samsung_Galaxy S20_test123456"
        assert device.is_frp_bypassable is True
    
    def test_device_id_generation(self):
        """Testa geração de ID único do dispositivo"""
        device = AndroidDevice(
            vendor_id=0x04e8,
            product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG,
            model="Galaxy S20",
            serial="ABC123",
            mode=DeviceMode.ADB
        )
        
        expected_id = "samsung_Galaxy S20_ABC123"
        assert device.device_id == expected_id
    
    def test_frp_bypassable_conditions(self):
        """Testa condições para bypass FRP"""
        # Dispositivo com FRP e modo compatível
        device1 = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Test",
            serial="123", mode=DeviceMode.ADB, frp_locked=True
        )
        assert device1.is_frp_bypassable is True
        
        # Dispositivo sem FRP
        device2 = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Test",
            serial="123", mode=DeviceMode.ADB, frp_locked=False
        )
        assert device2.is_frp_bypassable is False
        
        # Dispositivo com FRP mas modo incompatível
        device3 = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Test",
            serial="123", mode=DeviceMode.UNKNOWN, frp_locked=True
        )
        assert device3.is_frp_bypassable is False
    
    def test_to_dict_conversion(self):
        """Testa conversão para dicionário"""
        device = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Galaxy S20",
            serial="test123", mode=DeviceMode.ADB,
            android_version="11", frp_locked=True
        )
        
        device_dict = device.to_dict()
        
        assert device_dict['vendor_id'] == '0x4e8'
        assert device_dict['manufacturer'] == 'samsung'
        assert device_dict['model'] == 'Galaxy S20'
        assert device_dict['android_version'] == '11'
        assert device_dict['frp_locked'] is True


class TestDeviceDetector:
    """Testes para a classe DeviceDetector"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.detector = DeviceDetector()
    
    def test_detector_initialization(self):
        """Testa inicialização do detector"""
        assert isinstance(self.detector, DeviceDetector)
        assert self.detector.detected_devices == []
        assert len(self.detector.VENDOR_IDS) >= 4  # Samsung, LG, Xiaomi, Google
    
    def test_vendor_id_mapping(self):
        """Testa mapeamento de vendor IDs"""
        assert self.detector.VENDOR_IDS[0x04e8] == Manufacturer.SAMSUNG
        assert self.detector.VENDOR_IDS[0x1004] == Manufacturer.LG
        assert self.detector.VENDOR_IDS[0x2717] == Manufacturer.XIAOMI
        assert self.detector.VENDOR_IDS[0x18d1] == Manufacturer.GOOGLE
    
    @patch('usb.core.find')
    def test_scan_usb_devices_no_devices(self, mock_find):
        """Testa scan quando não há dispositivos"""
        mock_find.return_value = []
        
        devices = self.detector.scan_usb_devices()
        
        assert devices == []
        assert self.detector.detected_devices == []
    
    @patch('usb.core.find')
    @patch('core.device_detection.DeviceDetector._analyze_usb_device')
    def test_scan_usb_devices_with_devices(self, mock_analyze, mock_find):
        """Testa scan com dispositivos conectados"""
        # Mock USB device
        mock_usb_device = Mock()
        mock_usb_device.idVendor = 0x04e8  # Samsung
        mock_usb_device.idProduct = 0x6860
        
        mock_find.return_value = [mock_usb_device]
        
        # Mock device analysis
        mock_device = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Galaxy S20",
            serial="test123", mode=DeviceMode.ADB
        )
        mock_analyze.return_value = mock_device
        
        devices = self.detector.scan_usb_devices()
        
        assert len(devices) == 1
        assert devices[0].manufacturer == Manufacturer.SAMSUNG
        mock_analyze.assert_called_once_with(mock_usb_device)
    
    @patch('usb.util.get_string')
    def test_get_device_serial(self, mock_get_string):
        """Testa obtenção do serial do dispositivo"""
        mock_usb_device = Mock()
        mock_usb_device.iSerialNumber = 1
        mock_get_string.return_value = "ABC123456"
        
        serial = self.detector._get_device_serial(mock_usb_device)
        
        assert serial == "ABC123456"
        mock_get_string.assert_called_once()
    
    def test_detect_device_mode_samsung(self):
        """Testa detecção de modo para dispositivos Samsung"""
        # ADB mode
        mode = self.detector._detect_device_mode(0x04e8, 0x6860)
        assert mode == DeviceMode.ADB
        
        # Download mode
        mode = self.detector._detect_device_mode(0x04e8, 0x6877)
        assert mode == DeviceMode.DOWNLOAD
        
        # Unknown product ID
        mode = self.detector._detect_device_mode(0x04e8, 0x9999)
        assert mode == DeviceMode.UNKNOWN
    
    @patch('subprocess.run')
    def test_detect_mode_via_adb(self, mock_run):
        """Testa detecção de modo via ADB"""
        # Mock successful ADB command
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "ABC123\tdevice\n"
        mock_run.return_value = mock_result
        
        mode = self.detector._detect_mode_via_tools()
        
        assert mode == DeviceMode.ADB
    
    @patch('subprocess.run')
    def test_detect_mode_via_fastboot(self, mock_run):
        """Testa detecção de modo via Fastboot"""
        # Mock ADB failure, Fastboot success
        def side_effect(*args, **kwargs):
            if 'adb' in args[0]:
                result = Mock()
                result.returncode = 1
                return result
            elif 'fastboot' in args[0]:
                result = Mock()
                result.returncode = 0
                result.stdout = "ABC123\tfastboot"
                return result
        
        mock_run.side_effect = side_effect
        
        mode = self.detector._detect_mode_via_tools()
        
        assert mode == DeviceMode.FASTBOOT
    
    def test_get_device_by_serial(self):
        """Testa busca de dispositivo por serial"""
        # Adiciona dispositivo mock
        device = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Test",
            serial="ABC123", mode=DeviceMode.ADB
        )
        self.detector.detected_devices = [device]
        
        # Busca existente
        found_device = self.detector.get_device_by_serial("ABC123")
        assert found_device == device
        
        # Busca inexistente
        not_found = self.detector.get_device_by_serial("XYZ789")
        assert not_found is None
    
    def test_get_frp_locked_devices(self):
        """Testa filtro de dispositivos com FRP"""
        device1 = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Test1",
            serial="ABC123", mode=DeviceMode.ADB, frp_locked=True
        )
        device2 = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Test2",
            serial="DEF456", mode=DeviceMode.ADB, frp_locked=False
        )
        device3 = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Test3",
            serial="GHI789", mode=DeviceMode.ADB, frp_locked=None
        )
        
        self.detector.detected_devices = [device1, device2, device3]
        
        frp_devices = self.detector.get_frp_locked_devices()
        
        assert len(frp_devices) == 1
        assert frp_devices[0] == device1
    
    @patch('core.device_detection.DeviceDetector.scan_usb_devices')
    @patch('time.sleep')
    def test_continuous_scan(self, mock_sleep, mock_scan):
        """Testa escaneamento contínuo"""
        # Mock para parar após 2 iterações
        mock_scan.side_effect = [[], []]
        mock_sleep.side_effect = [None, KeyboardInterrupt()]
        
        # Deve capturar KeyboardInterrupt e parar
        self.detector.continuous_scan(interval=1)
        
        assert mock_scan.call_count == 2
        assert mock_sleep.call_count == 2


class TestUtilityFunctions:
    """Testes para funções utilitárias"""
    
    @patch('core.device_detection.DeviceDetector.scan_usb_devices')
    def test_quick_scan(self, mock_scan):
        """Testa função de scan rápido"""
        mock_device = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Test",
            serial="123", mode=DeviceMode.ADB
        )
        mock_scan.return_value = [mock_device]
        
        devices = quick_scan()
        
        assert len(devices) == 1
        assert devices[0] == mock_device
    
    @patch('core.device_detection.DeviceDetector.scan_usb_devices')
    @patch('core.device_detection.DeviceDetector.get_frp_locked_devices')
    def test_find_frp_devices(self, mock_get_frp, mock_scan):
        """Testa função para encontrar dispositivos com FRP"""
        mock_frp_device = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Test",
            serial="123", mode=DeviceMode.ADB, frp_locked=True
        )
        mock_get_frp.return_value = [mock_frp_device]
        
        frp_devices = find_frp_devices()
        
        assert len(frp_devices) == 1
        assert frp_devices[0].frp_locked is True


class TestDeviceEnrichment:
    """Testes para enriquecimento de informações do dispositivo"""
    
    def setup_method(self):
        self.detector = DeviceDetector()
    
    @patch('subprocess.run')
    def test_get_adb_info_success(self, mock_run):
        """Testa obtenção de informações via ADB"""
        device = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Unknown",
            serial="test123", mode=DeviceMode.ADB
        )
        
        # Mock successful ADB commands
        def adb_side_effect(*args, **kwargs):
            result = Mock()
            result.returncode = 0
            
            if 'ro.product.model' in args[0]:
                result.stdout = "Galaxy S20"
            elif 'ro.build.version.release' in args[0]:
                result.stdout = "11"
            elif 'ro.build.version.sdk' in args[0]:
                result.stdout = "30"
            elif 'ro.build.id' in args[0]:
                result.stdout = "RP1A.200720.012"
            else:
                result.stdout = ""
            
            return result
        
        mock_run.side_effect = adb_side_effect
        
        self.detector._get_adb_info(device)
        
        assert device.model == "Galaxy S20"
        assert device.android_version == "11"
        assert device.api_level == 30
        assert device.build_id == "RP1A.200720.012"
        assert device.usb_debugging is True
    
    @patch('subprocess.run')
    def test_get_fastboot_info_success(self, mock_run):
        """Testa obtenção de informações via Fastboot"""
        device = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Unknown",
            serial="test123", mode=DeviceMode.FASTBOOT
        )
        
        # Mock Fastboot commands (output goes to stderr)
        def fastboot_side_effect(*args, **kwargs):
            result = Mock()
            result.returncode = 0
            result.stdout = ""
            
            if 'product' in args[0]:
                result.stderr = "product: galaxy_s20"
            elif 'unlocked' in args[0]:
                result.stderr = "unlocked: no"
            else:
                result.stderr = ""
            
            return result
        
        mock_run.side_effect = fastboot_side_effect
        
        self.detector._get_fastboot_info(device)
        
        assert device.model == "galaxy_s20"
        assert device.bootloader_locked is True
    
    @patch('subprocess.run')
    def test_check_frp_status_with_google_account(self, mock_run):
        """Testa verificação de FRP com conta Google"""
        device = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Test",
            serial="test123", mode=DeviceMode.ADB
        )
        
        # Mock dumpsys account with Google account
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Account: com.google name=user@gmail.com"
        mock_run.return_value = mock_result
        
        self.detector._check_frp_status(device)
        
        assert device.frp_locked is True
        assert device.google_account == "user@gmail.com"
    
    @patch('subprocess.run')
    def test_check_frp_status_no_google_account(self, mock_run):
        """Testa verificação de FRP sem conta Google"""
        device = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Test",
            serial="test123", mode=DeviceMode.ADB
        )
        
        # Mock dumpsys account without Google account
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "No Google accounts found"
        mock_run.return_value = mock_result
        
        self.detector._check_frp_status(device)
        
        assert device.frp_locked is False
        assert device.google_account is None


# Fixtures para testes
@pytest.fixture
def sample_android_device():
    """Fixture com dispositivo Android de exemplo"""
    return AndroidDevice(
        vendor_id=0x04e8,
        product_id=0x6860,
        manufacturer=Manufacturer.SAMSUNG,
        model="Galaxy S20",
        serial="test123456",
        mode=DeviceMode.ADB,
        android_version="11",
        api_level=30,
        frp_locked=True,
        usb_debugging=True
    )


@pytest.fixture
def device_detector():
    """Fixture com detector de dispositivos"""
    return DeviceDetector()


# Testes de integração
class TestIntegration:
    """Testes de integração do sistema de detecção"""
    
    def test_full_detection_workflow(self, device_detector):
        """Testa fluxo completo de detecção"""
        # Este teste requer dispositivos reais conectados
        # Em ambiente de CI/CD, seria mockado
        
        devices = device_detector.scan_usb_devices()
        
        # Verifica que o scan não falha
        assert isinstance(devices, list)
        
        # Se houver dispositivos, verifica estrutura
        for device in devices:
            assert isinstance(device, AndroidDevice)
            assert device.vendor_id > 0
            assert device.manufacturer != Manufacturer.UNKNOWN
            assert device.serial != ""
            assert device.mode != DeviceMode.UNKNOWN


if __name__ == "__main__":
    # Executa testes se chamado diretamente
    pytest.main([__file__, "-v"])
