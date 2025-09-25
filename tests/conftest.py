"""
Configuração global de testes para FRP Bypass Professional
=========================================================

Configurações e fixtures compartilhadas entre todos os testes.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

# Configuração de ambiente para testes
os.environ['FRP_TEST_MODE'] = '1'
os.environ['FRP_LOG_LEVEL'] = 'DEBUG'

# Importações do projeto
from core.device_detection import AndroidDevice, DeviceMode, Manufacturer
from core.communication import CommunicationManager
from database import DeviceDatabase, ExploitManager


@pytest.fixture(scope="session")
def test_data_dir():
    """Diretório com dados de teste"""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def temp_dir():
    """Diretório temporário para testes"""
    temp_path = Path(tempfile.mkdtemp(prefix="frp_test_"))
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_android_device():
    """Dispositivo Android de exemplo para testes"""
    return AndroidDevice(
        vendor_id=0x04e8,
        product_id=0x6860,
        manufacturer=Manufacturer.SAMSUNG,
        model="Galaxy S20",
        serial="test123456",
        mode=DeviceMode.ADB,
        android_version="11",
        api_level=30,
        build_id="RP1A.200720.012",
        frp_locked=True,
        usb_debugging=True,
        bootloader_locked=True
    )


@pytest.fixture
def sample_lg_device():
    """Dispositivo LG de exemplo"""
    return AndroidDevice(
        vendor_id=0x1004,
        product_id=0x6000,
        manufacturer=Manufacturer.LG,
        model="G8 ThinQ",
        serial="lg123456",
        mode=DeviceMode.ADB,
        android_version="10",
        api_level=29,
        frp_locked=True,
        usb_debugging=True
    )


@pytest.fixture
def sample_xiaomi_device():
    """Dispositivo Xiaomi de exemplo"""
    return AndroidDevice(
        vendor_id=0x2717,
        product_id=0xff40,
        manufacturer=Manufacturer.XIAOMI,
        model="Mi 10",
        serial="xiaomi123456",
        mode=DeviceMode.FASTBOOT,
        android_version="11",
        api_level=30,
        frp_locked=True,
        bootloader_locked=False
    )


@pytest.fixture
def multiple_devices(sample_android_device, sample_lg_device, sample_xiaomi_device):
    """Lista com múltiplos dispositivos para testes"""
    return [sample_android_device, sample_lg_device, sample_xiaomi_device]


@pytest.fixture
def mock_communication_manager():
    """Mock do gerenciador de comunicação"""
    mock_manager = Mock(spec=CommunicationManager)
    
    # Mock interface ADB
    mock_adb_interface = Mock()
    mock_adb_interface.execute_command.return_value = Mock(success=True, output="", error="")
    mock_adb_interface.shell_command.return_value = Mock(success=True, output="", error="")
    mock_adb_interface.get_property.return_value = "test_value"
    mock_adb_interface.is_root.return_value = False
    
    # Mock interface Fastboot
    mock_fastboot_interface = Mock()
    mock_fastboot_interface.execute_command.return_value = Mock(success=True, output="", error="")
    mock_fastboot_interface.get_variable.return_value = "test_value"
    mock_fastboot_interface.is_unlocked.return_value = True
    
    # Configura retorno baseado no modo do dispositivo
    def get_interface_side_effect(device):
        if device.mode == DeviceMode.ADB:
            return mock_adb_interface
        elif device.mode == DeviceMode.FASTBOOT:
            return mock_fastboot_interface
        else:
            return Mock()
    
    mock_manager.get_interface.side_effect = get_interface_side_effect
    mock_manager.test_connection.return_value = True
    
    return mock_manager


@pytest.fixture
def mock_device_database(temp_dir):
    """Mock da base de dados de dispositivos"""
    # Cria arquivo de database temporário
    db_file = temp_dir / "test_device_profiles.json"
    
    test_database = {
        "version": "1.0.0",
        "last_updated": "2025-09-25",
        "manufacturers": {
            "samsung": {
                "name": "Samsung Electronics",
                "vendor_id": "0x04e8",
                "series": {
                    "galaxy_s": {
                        "models": [
                            {
                                "name": "Galaxy S20",
                                "codename": "x1s",
                                "android_versions": ["10", "11", "12"],
                                "api_levels": [29, 30, 31],
                                "chipset": "Exynos 990",
                                "supported_methods": ["adb_exploit", "download_mode"],
                                "frp_bypass_difficulty": "medium",
                                "success_rate": 85
                            }
                        ]
                    }
                },
                "common_exploits": [
                    {
                        "name": "ADB FRP Bypass",
                        "type": "adb_exploit",
                        "description": "Bypass via ADB commands",
                        "requirements": ["ADB access"],
                        "steps": ["Connect ADB", "Execute commands"],
                        "compatibility": ["galaxy_s"],
                        "risk_level": "low"
                    }
                ]
            }
        }
    }
    
    import json
    with open(db_file, 'w') as f:
        json.dump(test_database, f)
    
    return DeviceDatabase(str(db_file))


@pytest.fixture
def mock_exploit_manager(mock_device_database):
    """Mock do gerenciador de exploits"""
    return ExploitManager(mock_device_database)


@pytest.fixture(autouse=True)
def setup_test_environment(temp_dir):
    """Setup automático do ambiente de teste"""
    # Cria diretórios necessários
    (temp_dir / "logs").mkdir(exist_ok=True)
    (temp_dir / "temp").mkdir(exist_ok=True)
    (temp_dir / "exports").mkdir(exist_ok=True)
    
    # Configura variáveis de ambiente
    os.environ['FRP_TEST_TEMP_DIR'] = str(temp_dir)
    
    yield
    
    # Cleanup após teste
    if 'FRP_TEST_TEMP_DIR' in os.environ:
        del os.environ['FRP_TEST_TEMP_DIR']


@pytest.fixture
def mock_usb_device():
    """Mock de dispositivo USB"""
    mock_device = Mock()
    mock_device.idVendor = 0x04e8
    mock_device.idProduct = 0x6860
    mock_device.iSerialNumber = 1
    
    # Mock configuração USB
    mock_config = Mock()
    mock_interface = Mock()
    mock_endpoint_in = Mock()
    mock_endpoint_out = Mock()
    
    mock_endpoint_in.bEndpointAddress = 0x81
    mock_endpoint_out.bEndpointAddress = 0x01
    
    mock_interface.__iter__ = Mock(return_value=iter([mock_endpoint_in, mock_endpoint_out]))
    mock_config.__getitem__ = Mock(return_value=mock_interface)
    
    mock_device.get_active_configuration.return_value = mock_config
    
    return mock_device


@pytest.fixture
def mock_subprocess_run():
    """Mock para subprocess.run"""
    with patch('subprocess.run') as mock_run:
        # Configuração padrão para comandos bem-sucedidos
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        yield mock_run


@pytest.fixture
def mock_adb_commands(mock_subprocess_run):
    """Mock específico para comandos ADB"""
    def adb_side_effect(*args, **kwargs):
        result = Mock()
        result.returncode = 0
        result.stderr = ""
        
        command = ' '.join(args[0]) if isinstance(args[0], list) else args[0]
        
        if 'adb devices' in command:
            result.stdout = "List of devices attached\ntest123456\tdevice\n"
        elif 'adb version' in command:
            result.stdout = "Android Debug Bridge version 1.0.41"
        elif 'get-state' in command:
            result.stdout = "device"
        elif 'getprop ro.product.model' in command:
            result.stdout = "Galaxy S20"
        elif 'getprop ro.build.version.release' in command:
            result.stdout = "11"
        elif 'getprop ro.build.version.sdk' in command:
            result.stdout = "30"
        elif 'dumpsys account' in command:
            result.stdout = "Account: com.google name=test@gmail.com"
        else:
            result.stdout = ""
        
        return result
    
    mock_subprocess_run.side_effect = adb_side_effect
    return mock_subprocess_run


@pytest.fixture
def mock_fastboot_commands(mock_subprocess_run):
    """Mock específico para comandos Fastboot"""
    def fastboot_side_effect(*args, **kwargs):
        result = Mock()
        result.returncode = 0
        result.stdout = ""
        
        command = ' '.join(args[0]) if isinstance(args[0], list) else args[0]
        
        if 'fastboot devices' in command:
            result.stderr = "test123456\tfastboot"
        elif 'fastboot --version' in command:
            result.stderr = "fastboot version 1.0.41"
        elif 'getvar product' in command:
            result.stderr = "product: galaxy_s20"
        elif 'getvar unlocked' in command:
            result.stderr = "unlocked: yes"
        elif 'getvar unlock_ability' in command:
            result.stderr = "unlock_ability: 1"
        else:
            result.stderr = ""
        
        return result
    
    mock_subprocess_run.side_effect = fastboot_side_effect
    return mock_subprocess_run


# Markers customizados para testes
def pytest_configure(config):
    """Configuração customizada do pytest"""
    config.addinivalue_line("markers", "integration: marca testes de integração")
    config.addinivalue_line("markers", "slow: marca testes lentos")
    config.addinivalue_line("markers", "requires_device: marca testes que precisam de dispositivo real")
    config.addinivalue_line("markers", "requires_adb: marca testes que precisam de ADB")
    config.addinivalue_line("markers", "requires_fastboot: marca testes que precisam de Fastboot")


# Skip automático para testes que requerem hardware
def pytest_runtest_setup(item):
    """Setup automático antes de cada teste"""
    # Skip testes que requerem dispositivo real em CI
    if item.get_closest_marker("requires_device"):
        if os.environ.get("CI") == "true":
            pytest.skip("Teste requer dispositivo real - pulando em CI")
    
    # Skip testes que requerem ADB se não disponível
    if item.get_closest_marker("requires_adb"):
        try:
            import subprocess
            subprocess.run(['adb', 'version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("ADB não disponível")
    
    # Skip testes que requerem Fastboot se não disponível
    if item.get_closest_marker("requires_fastboot"):
        try:
            import subprocess
            subprocess.run(['fastboot', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Fastboot não disponível")


# Fixtures para simulação de tempo
@pytest.fixture
def mock_time():
    """Mock para funções de tempo"""
    with patch('time.time') as mock_time_func:
        mock_time_func.return_value = 1640995200.0  # 2022-01-01 00:00:00
        yield mock_time_func


@pytest.fixture
def mock_sleep():
    """Mock para time.sleep"""
    with patch('time.sleep') as mock_sleep_func:
        yield mock_sleep_func


# Configuração de logging para testes
@pytest.fixture(autouse=True)
def setup_test_logging():
    """Configura logging para testes"""
    import logging
    logging.getLogger().setLevel(logging.DEBUG)
    
    # Suprime logs de bibliotecas externas durante testes
    logging.getLogger('usb').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


# Cleanup automático
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup automático após cada teste"""
    yield
    
    # Limpa variáveis de ambiente de teste
    test_env_vars = [key for key in os.environ.keys() if key.startswith('FRP_TEST_')]
    for var in test_env_vars:
        if var != 'FRP_TEST_MODE':  # Mantém modo de teste
            del os.environ[var]
