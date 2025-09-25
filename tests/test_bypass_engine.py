"""
Testes para o engine de bypass FRP
==================================

Testa todas as funcionalidades do engine principal de bypass.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

from core.bypass_engine import (
    FRPBypassEngine, BypassResult, BypassStatus, BypassMethod,
    ADBBypassMethod, FastbootBypassMethod, BypassStrategy, BypassSession
)
from core.device_detection import AndroidDevice, DeviceMode, Manufacturer
from core.communication import CommunicationManager, ADBInterface, FastbootInterface
from database import DeviceDatabase, ExploitManager


class TestBypassResult:
    """Testes para a classe BypassResult"""
    
    def test_bypass_result_creation(self):
        """Testa criação de resultado de bypass"""
        result = BypassResult(
            status=BypassStatus.SUCCESS,
            method_used="adb_exploit",
            execution_time=15.5,
            success=True
        )
        
        assert result.status == BypassStatus.SUCCESS
        assert result.method_used == "adb_exploit"
        assert result.execution_time == 15.5
        assert result.success is True
        assert len(result.logs) == 0
    
    def test_add_log_functionality(self):
        """Testa adição de logs"""
        result = BypassResult(
            status=BypassStatus.IN_PROGRESS,
            method_used="test_method",
            execution_time=0.0
        )
        
        result.add_log("Iniciando teste")
        result.add_log("Teste concluído")
        
        assert len(result.logs) == 2
        assert "Iniciando teste" in result.logs[0]
        assert "Teste concluído" in result.logs[1]
        # Verifica formato de timestamp
        assert "[" in result.logs[0] and "]" in result.logs[0]
    
    def test_to_dict_conversion(self):
        """Testa conversão para dicionário"""
        result = BypassResult(
            status=BypassStatus.SUCCESS,
            method_used="adb_exploit",
            execution_time=10.0,
            success=True,
            steps_completed=["step1", "step2"]
        )
        result.add_log("Test log")
        
        result_dict = result.to_dict()
        
        assert result_dict['status'] == 'success'
        assert result_dict['method_used'] == 'adb_exploit'
        assert result_dict['execution_time'] == 10.0
        assert result_dict['success'] is True
        assert result_dict['steps_completed'] == ["step1", "step2"]
        assert len(result_dict['logs']) == 1


class TestBypassMethod:
    """Testes para métodos de bypass"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.device = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Galaxy S20",
            serial="test123", mode=DeviceMode.ADB,
            frp_locked=True, usb_debugging=True
        )
        self.comm_manager = Mock(spec=CommunicationManager)
    
    def test_adb_bypass_method_can_execute_success(self):
        """Testa verificação de execução ADB bem-sucedida"""
        # Mock interface ADB
        mock_interface = Mock(spec=ADBInterface)
        mock_result = Mock()
        mock_result.success = True
        mock_interface.execute_command.return_value = mock_result
        
        self.comm_manager.get_interface.return_value = mock_interface
        
        method = ADBBypassMethod("test_adb", self.device, self.comm_manager)
        can_execute, reason = method.can_execute()
        
        assert can_execute is True
        assert "ADB disponível" in reason
    
    def test_adb_bypass_method_can_execute_wrong_mode(self):
        """Testa verificação de execução ADB com modo incorreto"""
        device_wrong_mode = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Galaxy S20",
            serial="test123", mode=DeviceMode.FASTBOOT,  # Modo incorreto
            frp_locked=True
        )
        
        method = ADBBypassMethod("test_adb", device_wrong_mode, self.comm_manager)
        can_execute, reason = method.can_execute()
        
        assert can_execute is False
        assert "não está em modo ADB" in reason
    
    def test_adb_bypass_method_can_execute_no_usb_debug(self):
        """Testa verificação ADB sem USB debugging"""
        device_no_debug = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Galaxy S20",
            serial="test123", mode=DeviceMode.ADB,
            frp_locked=True, usb_debugging=False  # USB debug desabilitado
        )
        
        method = ADBBypassMethod("test_adb", device_no_debug, self.comm_manager)
        can_execute, reason = method.can_execute()
        
        assert can_execute is False
        assert "USB debugging não está habilitado" in reason
    
    @patch('time.time')
    def test_adb_bypass_method_execute_success(self, mock_time):
        """Testa execução bem-sucedida do bypass ADB"""
        # Mock tempo
        mock_time.side_effect = [100.0, 110.0]  # 10 segundos de execução
        
        # Mock interface ADB
        mock_interface = Mock(spec=ADBInterface)
        
        # Mock comandos ADB
        mock_get_state = Mock()
        mock_get_state.success = True
        
        mock_shell_result = Mock()
        mock_shell_result.success = True
        mock_shell_result.output = ""
        
        mock_clear_result = Mock()
        mock_clear_result.success = True
        
        mock_interface.execute_command.return_value = mock_get_state
        mock_interface.shell_command.return_value = mock_shell_result
        mock_interface.get_property.side_effect = [
            "Galaxy S20", "11", "30", "RP1A.200720.012"
        ]
        
        self.comm_manager.get_interface.return_value = mock_interface
        
        method = ADBBypassMethod("test_adb", self.device, self.comm_manager)
        
        # Mock métodos internos
        with patch.object(method, 'verify_bypass', return_value=True):
            result = method.execute()
        
        assert result.status == BypassStatus.SUCCESS
        assert result.success is True
        assert result.execution_time == 10.0
        assert len(result.logs) > 0
    
    def test_fastboot_bypass_method_can_execute_success(self):
        """Testa verificação de execução Fastboot"""
        device_fastboot = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Galaxy S20",
            serial="test123", mode=DeviceMode.FASTBOOT,
            frp_locked=True
        )
        
        # Mock interface Fastboot
        mock_interface = Mock(spec=FastbootInterface)
        mock_interface.get_variable.return_value = "yes"  # Bootloader unlocked
        
        self.comm_manager.get_interface.return_value = mock_interface
        
        method = FastbootBypassMethod("test_fastboot", device_fastboot, self.comm_manager)
        can_execute, reason = method.can_execute()
        
        assert can_execute is True
        assert "desbloqueado" in reason
    
    def test_fastboot_bypass_method_can_execute_locked_bootloader(self):
        """Testa Fastboot com bootloader bloqueado mas desbloqueável"""
        device_fastboot = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Galaxy S20",
            serial="test123", mode=DeviceMode.FASTBOOT,
            frp_locked=True
        )
        
        # Mock interface Fastboot
        mock_interface = Mock(spec=FastbootInterface)
        mock_interface.get_variable.side_effect = ["no", "1"]  # Locked but unlockable
        
        self.comm_manager.get_interface.return_value = mock_interface
        
        method = FastbootBypassMethod("test_fastboot", device_fastboot, self.comm_manager)
        can_execute, reason = method.can_execute()
        
        assert can_execute is True
        assert "pode ser desbloqueado" in reason
    
    @patch('time.time')
    def test_fastboot_bypass_method_execute_success(self, mock_time):
        """Testa execução bem-sucedida do bypass Fastboot"""
        mock_time.side_effect = [100.0, 115.0]  # 15 segundos
        
        device_fastboot = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Galaxy S20",
            serial="test123", mode=DeviceMode.FASTBOOT,
            frp_locked=True
        )
        
        # Mock interface Fastboot
        mock_interface = Mock(spec=FastbootInterface)
        mock_interface.is_unlocked.return_value = True
        
        mock_erase_result = Mock()
        mock_erase_result.success = True
        mock_interface.erase_partition.return_value = mock_erase_result
        
        mock_reboot_result = Mock()
        mock_reboot_result.success = True
        mock_interface.reboot.return_value = mock_reboot_result
        
        self.comm_manager.get_interface.return_value = mock_interface
        
        method = FastbootBypassMethod("test_fastboot", device_fastboot, self.comm_manager)
        result = method.execute()
        
        assert result.status == BypassStatus.SUCCESS
        assert result.success is True
        assert result.execution_time == 15.0
        assert "userdata_erase" in result.steps_completed


class TestBypassStrategy:
    """Testes para estratégia de bypass"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.device = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Galaxy S20",
            serial="test123", mode=DeviceMode.ADB,
            frp_locked=True
        )
        
        # Mock device profile
        self.device_profile = Mock()
        self.device_profile.supported_methods = ["adb_exploit", "fastboot_method"]
        self.device_profile.frp_bypass_difficulty = "medium"
        self.device_profile.success_rate = 85
        
        # Mock exploit manager
        self.exploit_manager = Mock(spec=ExploitManager)
        mock_exploits = [Mock(), Mock()]
        for i, exploit in enumerate(mock_exploits):
            exploit.risk_enum.value = i
            exploit.name = f"exploit_{i}"
        self.exploit_manager.get_exploits_for_device.return_value = mock_exploits
    
    def test_strategy_generation(self):
        """Testa geração de estratégia"""
        strategy = BypassStrategy(self.device, self.device_profile, self.exploit_manager)
        
        assert len(strategy.methods) > 0
        assert strategy.has_more_methods() is True
    
    def test_get_next_method(self):
        """Testa obtenção do próximo método"""
        strategy = BypassStrategy(self.device, self.device_profile, self.exploit_manager)
        
        # Deve ter pelo menos um método
        assert strategy.has_more_methods() is True
        
        # Obtém primeiro método
        method_info = strategy.get_next_method()
        assert method_info is not None
        
        method_class, priority = method_info
        assert issubclass(method_class, BypassMethod)
        assert isinstance(priority, float)
    
    def test_method_exhaustion(self):
        """Testa esgotamento de métodos"""
        strategy = BypassStrategy(self.device, self.device_profile, self.exploit_manager)
        
        # Esgota todos os métodos
        while strategy.has_more_methods():
            strategy.get_next_method()
        
        # Não deve ter mais métodos
        assert strategy.has_more_methods() is False
        assert strategy.get_next_method() is None


class TestFRPBypassEngine:
    """Testes para o engine principal"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.device_db = Mock(spec=DeviceDatabase)
        self.comm_manager = Mock(spec=CommunicationManager)
        self.engine = FRPBypassEngine(self.device_db, self.comm_manager)
        
        self.device = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Galaxy S20",
            serial="test123", mode=DeviceMode.ADB,
            frp_locked=True
        )
    
    def test_engine_initialization(self):
        """Testa inicialização do engine"""
        assert self.engine.device_database == self.device_db
        assert self.engine.comm_manager == self.comm_manager
        assert len(self.engine.active_sessions) == 0
    
    def test_start_bypass_session(self):
        """Testa início de sessão de bypass"""
        session_id = self.engine.start_bypass_session(self.device)
        
        assert session_id is not None
        assert session_id in self.engine.active_sessions
        
        session = self.engine.get_session(session_id)
        assert session is not None
        assert session.device == self.device
    
    def test_get_session_existing(self):
        """Testa obtenção de sessão existente"""
        session_id = self.engine.start_bypass_session(self.device)
        
        retrieved_session = self.engine.get_session(session_id)
        
        assert retrieved_session is not None
        assert retrieved_session.session_id == session_id
    
    def test_get_session_nonexistent(self):
        """Testa obtenção de sessão inexistente"""
        session = self.engine.get_session("nonexistent_id")
        
        assert session is None
    
    @patch('core.bypass_engine.BypassStrategy')
    def test_execute_bypass_device_not_found(self, mock_strategy_class):
        """Testa bypass com dispositivo não encontrado na base"""
        # Mock device database returning None
        self.engine._find_device_profile = Mock(return_value=None)
        
        result = self.engine.execute_bypass(self.device)
        
        assert result.status == BypassStatus.ERROR
        assert "não encontrado na base de dados" in result.error_message
    
    @patch('core.bypass_engine.BypassStrategy')
    def test_execute_bypass_success(self, mock_strategy_class):
        """Testa execução bem-sucedida de bypass"""
        # Mock device profile
        mock_profile = Mock()
        self.engine._find_device_profile = Mock(return_value=mock_profile)
        
        # Mock strategy
        mock_strategy = Mock()
        mock_strategy.has_more_methods.side_effect = [True, False]
        mock_strategy.get_next_method.return_value = (ADBBypassMethod, 0.9)
        mock_strategy_class.return_value = mock_strategy
        
        # Mock successful bypass method
        with patch('core.bypass_engine.ADBBypassMethod') as mock_method_class:
            mock_method = Mock()
            mock_method.can_execute.return_value = (True, "OK")
            
            mock_result = BypassResult(
                status=BypassStatus.SUCCESS,
                method_used="adb_test",
                execution_time=10.0,
                success=True
            )
            mock_method.execute.return_value = mock_result
            mock_method_class.return_value = mock_method
            
            result = self.engine.execute_bypass(self.device)
        
        assert result.status == BypassStatus.SUCCESS
        assert result.success is True
    
    @patch('core.bypass_engine.BypassStrategy')
    def test_execute_bypass_all_methods_fail(self, mock_strategy_class):
        """Testa bypass quando todos os métodos falham"""
        # Mock device profile
        mock_profile = Mock()
        self.engine._find_device_profile = Mock(return_value=mock_profile)
        
        # Mock strategy with failing methods
        mock_strategy = Mock()
        mock_strategy.has_more_methods.side_effect = [True, True, False]
        mock_strategy.get_next_method.side_effect = [
            (ADBBypassMethod, 0.9),
            (FastbootBypassMethod, 0.8)
        ]
        mock_strategy_class.return_value = mock_strategy
        
        # Mock failing methods
        with patch('core.bypass_engine.ADBBypassMethod') as mock_adb, \
             patch('core.bypass_engine.FastbootBypassMethod') as mock_fastboot:
            
            # First method fails to execute
            mock_adb_instance = Mock()
            mock_adb_instance.can_execute.return_value = (False, "Cannot execute")
            mock_adb.return_value = mock_adb_instance
            
            # Second method executes but fails
            mock_fastboot_instance = Mock()
            mock_fastboot_instance.can_execute.return_value = (True, "OK")
            mock_fail_result = BypassResult(
                status=BypassStatus.FAILED,
                method_used="fastboot_test",
                execution_time=5.0,
                success=False,
                error_message="Bypass failed"
            )
            mock_fastboot_instance.execute.return_value = mock_fail_result
            mock_fastboot.return_value = mock_fastboot_instance
            
            result = self.engine.execute_bypass(self.device, max_attempts=2)
        
        assert result.status == BypassStatus.FAILED
        assert result.success is False
        assert "tentativas falharam" in result.error_message
    
    def test_find_device_profile_by_model(self):
        """Testa busca de perfil por modelo"""
        mock_profile = Mock()
        self.device_db.find_device_by_name.return_value = mock_profile
        
        profile = self.engine._find_device_profile(self.device)
        
        assert profile == mock_profile
        self.device_db.find_device_by_name.assert_called_once_with("Galaxy S20")
    
    def test_find_device_profile_by_manufacturer(self):
        """Testa busca de perfil por fabricante"""
        # Mock model not found
        self.device_db.find_device_by_name.return_value = None
        
        # Mock manufacturer devices
        mock_profile = Mock()
        self.device_db.find_devices_by_manufacturer.return_value = [mock_profile]
        
        profile = self.engine._find_device_profile(self.device)
        
        assert profile == mock_profile
        self.device_db.find_devices_by_manufacturer.assert_called_once_with("samsung")
    
    def test_get_engine_statistics(self):
        """Testa obtenção de estatísticas do engine"""
        # Adiciona algumas sessões mock
        session1 = Mock()
        session1.current_result = Mock()
        session1.current_result.success = True
        session1.current_result.status = BypassStatus.SUCCESS
        
        session2 = Mock()
        session2.current_result = Mock()
        session2.current_result.success = False
        session2.current_result.status = BypassStatus.FAILED
        
        self.engine.active_sessions = {
            "session1": session1,
            "session2": session2
        }
        
        # Mock database stats
        self.device_db.devices = {"device1": Mock(), "device2": Mock()}
        self.engine.exploit_manager.exploits = {"exploit1": Mock()}
        
        stats = self.engine.get_engine_statistics()
        
        assert stats['active_sessions'] == 2
        assert stats['session_statistics']['total'] == 2
        assert stats['session_statistics']['successful'] == 1
        assert stats['session_statistics']['failed'] == 1
        assert stats['supported_devices'] == 2
        assert stats['available_exploits'] == 1


class TestBypassSession:
    """Testes para sessão de bypass"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.device = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Galaxy S20",
            serial="test123", mode=DeviceMode.ADB,
            frp_locked=True
        )
        self.engine = Mock(spec=FRPBypassEngine)
        self.session = BypassSession("test_session", self.device, self.engine)
    
    def test_session_initialization(self):
        """Testa inicialização da sessão"""
        assert self.session.session_id == "test_session"
        assert self.session.device == self.device
        assert self.session.engine == self.engine
        assert self.session.current_result is None
        assert len(self.session.attempt_history) == 0
        assert self.session.is_cancelled is False
    
    def test_session_cancellation(self):
        """Testa cancelamento da sessão"""
        # Simula resultado em progresso
        self.session.current_result = BypassResult(
            status=BypassStatus.IN_PROGRESS,
            method_used="test_method",
            execution_time=0.0
        )
        
        self.session.cancel()
        
        assert self.session.is_cancelled is True
        assert self.session.current_result.status == BypassStatus.CANCELLED
    
    def test_get_session_info(self):
        """Testa obtenção de informações da sessão"""
        # Adiciona resultado mock
        mock_result = Mock()
        mock_result.status = BypassStatus.SUCCESS
        self.session.current_result = mock_result
        self.session.attempt_history = [mock_result]
        
        info = self.session.get_session_info()
        
        assert info['session_id'] == "test_session"
        assert info['device_id'] == self.device.device_id
        assert info['current_status'] == 'success'
        assert info['attempts'] == 1
        assert info['is_cancelled'] is False
        assert 'duration' in info
        assert 'start_time' in info
    
    @patch('threading.Thread')
    def test_execute_async(self, mock_thread_class):
        """Testa execução assíncrona"""
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread
        
        # Mock engine execute_bypass
        mock_result = BypassResult(
            status=BypassStatus.SUCCESS,
            method_used="test_method",
            execution_time=10.0,
            success=True
        )
        self.engine.execute_bypass.return_value = mock_result
        
        # Mock callback
        callback = Mock()
        
        thread = self.session.execute_async(callback)
        
        assert thread == mock_thread
        mock_thread_class.assert_called_once()
        mock_thread.start.assert_called_once()


# Fixtures para testes
@pytest.fixture
def sample_device():
    """Fixture com dispositivo de exemplo"""
    return AndroidDevice(
        vendor_id=0x04e8, product_id=0x6860,
        manufacturer=Manufacturer.SAMSUNG, model="Galaxy S20",
        serial="test123456", mode=DeviceMode.ADB,
        frp_locked=True, usb_debugging=True
    )


@pytest.fixture
def mock_communication_manager():
    """Fixture com gerenciador de comunicação mock"""
    return Mock(spec=CommunicationManager)


@pytest.fixture
def mock_device_database():
    """Fixture com base de dados mock"""
    return Mock(spec=DeviceDatabase)


@pytest.fixture
def bypass_engine(mock_device_database, mock_communication_manager):
    """Fixture com engine de bypass"""
    return FRPBypassEngine(mock_device_database, mock_communication_manager)


# Testes de integração
class TestBypassEngineIntegration:
    """Testes de integração do engine de bypass"""
    
    @patch('core.bypass_engine.DeviceDatabase')
    @patch('core.bypass_engine.CommunicationManager')
    def test_full_bypass_workflow_mock(self, mock_comm_class, mock_db_class):
        """Testa fluxo completo de bypass (mockado)"""
        # Setup mocks
        mock_db = Mock()
        mock_comm = Mock()
        mock_db_class.return_value = mock_db
        mock_comm_class.return_value = mock_comm
        
        # Create engine
        engine = FRPBypassEngine(mock_db, mock_comm)
        
        # Mock device profile found
        mock_profile = Mock()
        mock_profile.supported_methods = ["adb_exploit"]
        engine._find_device_profile = Mock(return_value=mock_profile)
        
        # Create test device
        device = AndroidDevice(
            vendor_id=0x04e8, product_id=0x6860,
            manufacturer=Manufacturer.SAMSUNG, model="Galaxy S20",
            serial="test123", mode=DeviceMode.ADB,
            frp_locked=True
        )
        
        # This would normally execute real bypass
        # In production, we'd mock the entire bypass chain
        with patch.object(engine, 'execute_bypass') as mock_execute:
            mock_result = BypassResult(
                status=BypassStatus.SUCCESS,
                method_used="adb_exploit",
                execution_time=10.0,
                success=True
            )
            mock_execute.return_value = mock_result
            
            result = engine.execute_bypass(device)
            
            assert result.success is True
            assert result.status == BypassStatus.SUCCESS


if __name__ == "__main__":
    # Executa testes se chamado diretamente
    pytest.main([__file__, "-v"])
