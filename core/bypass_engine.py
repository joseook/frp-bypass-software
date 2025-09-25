"""
FRP Bypass Engine
================

Engine principal para bypass de FRP (Factory Reset Protection) em dispositivos Android.
Implementa algoritmos inteligentes de seleção e execução de métodos de bypass.

Classes:
- BypassResult: Resultado de uma tentativa de bypass
- BypassStrategy: Estratégia de bypass para um dispositivo
- FRPBypassEngine: Engine principal de bypass
- BypassSession: Sessão de bypass com histórico
"""

import time
import threading
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from loguru import logger
import json

from .device_detection import AndroidDevice, DeviceMode
from .communication import CommunicationManager, ADBInterface, FastbootInterface, USBCommunicator
from ..database import DeviceDatabase, ExploitManager, DeviceProfile, ExploitMethod


class BypassStatus(Enum):
    """Status de uma operação de bypass"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ERROR = "error"


class BypassStep(Enum):
    """Etapas do processo de bypass"""
    INITIALIZATION = "initialization"
    DEVICE_ANALYSIS = "device_analysis"
    METHOD_SELECTION = "method_selection"
    PREPARATION = "preparation"
    EXECUTION = "execution"
    VERIFICATION = "verification"
    CLEANUP = "cleanup"
    COMPLETED = "completed"


@dataclass
class BypassResult:
    """Resultado de uma tentativa de bypass"""
    
    status: BypassStatus
    method_used: str
    execution_time: float
    success: bool = False
    error_message: str = ""
    steps_completed: List[str] = field(default_factory=list)
    device_state_before: Dict[str, Any] = field(default_factory=dict)
    device_state_after: Dict[str, Any] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    
    def add_log(self, message: str) -> None:
        """Adiciona entrada ao log"""
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        self.logs.append(f"[{timestamp}] {message}")
        logger.info(f"Bypass Log: {message}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte resultado para dicionário"""
        return {
            'status': self.status.value,
            'method_used': self.method_used,
            'execution_time': self.execution_time,
            'success': self.success,
            'error_message': self.error_message,
            'steps_completed': self.steps_completed,
            'device_state_before': self.device_state_before,
            'device_state_after': self.device_state_after,
            'logs': self.logs,
            'timestamp': self.timestamp
        }


class BypassMethod(ABC):
    """Classe base para métodos de bypass"""
    
    def __init__(self, name: str, device: AndroidDevice, communication_manager: CommunicationManager):
        self.name = name
        self.device = device
        self.comm_manager = communication_manager
        self.result = BypassResult(BypassStatus.PENDING, name, 0.0)
    
    @abstractmethod
    def can_execute(self) -> Tuple[bool, str]:
        """
        Verifica se o método pode ser executado
        
        Returns:
            Tupla (pode_executar, motivo)
        """
        pass
    
    @abstractmethod
    def execute(self) -> BypassResult:
        """
        Executa o método de bypass
        
        Returns:
            Resultado da execução
        """
        pass
    
    def prepare_device(self) -> bool:
        """
        Prepara o dispositivo para o bypass
        
        Returns:
            True se preparado com sucesso
        """
        self.result.add_log(f"Preparando dispositivo para método {self.name}")
        return True
    
    def verify_bypass(self) -> bool:
        """
        Verifica se o bypass foi bem-sucedido
        
        Returns:
            True se FRP foi removido
        """
        self.result.add_log("Verificando status do FRP após bypass")
        
        try:
            interface = self.comm_manager.get_interface(self.device)
            
            if isinstance(interface, ADBInterface):
                # Verifica se ainda há contas Google
                result = interface.shell_command("dumpsys account")
                if result.success:
                    output = result.output.lower()
                    has_google_account = 'com.google' in output and '@gmail.com' in output
                    
                    if not has_google_account:
                        self.result.add_log("✓ Nenhuma conta Google encontrada")
                        return True
                    else:
                        self.result.add_log("✗ Conta Google ainda presente")
                        return False
            
            # Para outros modos, assume sucesso se chegou até aqui
            return True
            
        except Exception as e:
            self.result.add_log(f"Erro ao verificar bypass: {e}")
            return False


class ADBBypassMethod(BypassMethod):
    """Método de bypass via ADB"""
    
    def can_execute(self) -> Tuple[bool, str]:
        """Verifica se pode executar bypass via ADB"""
        if self.device.mode != DeviceMode.ADB:
            return False, "Dispositivo não está em modo ADB"
        
        if not self.device.usb_debugging:
            return False, "USB debugging não está habilitado"
        
        try:
            interface = self.comm_manager.get_interface(self.device)
            if not isinstance(interface, ADBInterface):
                return False, "Não foi possível criar interface ADB"
            
            # Testa conexão
            result = interface.execute_command("get-state")
            if not result.success:
                return False, "Falha na comunicação ADB"
            
            return True, "Método ADB disponível"
            
        except Exception as e:
            return False, f"Erro ao verificar ADB: {e}"
    
    def execute(self) -> BypassResult:
        """Executa bypass via ADB"""
        start_time = time.time()
        self.result.status = BypassStatus.IN_PROGRESS
        self.result.add_log("Iniciando bypass via ADB")
        
        try:
            interface = self.comm_manager.get_interface(self.device)
            
            # Etapa 1: Análise do dispositivo
            self.result.add_log("Analisando estado do dispositivo")
            device_info = self._analyze_device_state(interface)
            self.result.device_state_before = device_info
            
            # Etapa 2: Preparação
            if not self.prepare_device():
                raise Exception("Falha na preparação do dispositivo")
            
            # Etapa 3: Execução do bypass
            success = self._execute_adb_bypass(interface)
            
            if success:
                # Etapa 4: Verificação
                if self.verify_bypass():
                    self.result.status = BypassStatus.SUCCESS
                    self.result.success = True
                    self.result.add_log("✓ Bypass ADB executado com sucesso")
                else:
                    self.result.status = BypassStatus.FAILED
                    self.result.error_message = "Bypass executado mas FRP ainda ativo"
                    self.result.add_log("✗ FRP ainda está ativo após bypass")
            else:
                self.result.status = BypassStatus.FAILED
                self.result.error_message = "Falha na execução do bypass ADB"
                self.result.add_log("✗ Falha na execução do bypass ADB")
            
        except Exception as e:
            self.result.status = BypassStatus.ERROR
            self.result.error_message = str(e)
            self.result.add_log(f"✗ Erro durante bypass ADB: {e}")
        
        finally:
            self.result.execution_time = time.time() - start_time
            self.result.add_log(f"Bypass finalizado em {self.result.execution_time:.2f}s")
        
        return self.result
    
    def _analyze_device_state(self, interface: ADBInterface) -> Dict[str, Any]:
        """Analisa estado atual do dispositivo"""
        state = {}
        
        try:
            # Informações básicas
            state['model'] = interface.get_property('ro.product.model')
            state['android_version'] = interface.get_property('ro.build.version.release')
            state['api_level'] = interface.get_property('ro.build.version.sdk')
            state['build_id'] = interface.get_property('ro.build.id')
            
            # Verifica contas
            accounts_result = interface.shell_command("dumpsys account")
            if accounts_result.success:
                state['has_google_account'] = 'com.google' in accounts_result.output.lower()
            
            # Verifica status de setup
            setup_result = interface.shell_command("settings get secure user_setup_complete")
            if setup_result.success:
                state['setup_complete'] = setup_result.output.strip() == "1"
            
        except Exception as e:
            logger.warning(f"Erro ao analisar estado do dispositivo: {e}")
        
        return state
    
    def _execute_adb_bypass(self, interface: ADBInterface) -> bool:
        """Executa comandos específicos de bypass ADB"""
        try:
            self.result.add_log("Executando comandos de bypass ADB")
            
            # Método 1: Tentar acessar configurações via activity
            self.result.add_log("Tentando abrir configurações via activity")
            result = interface.shell_command(
                "am start -n com.android.settings/.Settings"
            )
            
            if result.success:
                self.result.steps_completed.append("settings_activity")
                self.result.add_log("✓ Configurações abertas")
                
                # Aguarda um pouco para a activity carregar
                time.sleep(2)
                
                # Tenta remover conta Google via comando
                self.result.add_log("Tentando remover contas Google")
                remove_result = interface.shell_command(
                    "pm clear com.google.android.gms"
                )
                
                if remove_result.success:
                    self.result.steps_completed.append("clear_gms")
                    self.result.add_log("✓ Dados do Google Services limpos")
                    
                    # Limpa dados de setup
                    interface.shell_command("settings put secure user_setup_complete 0")
                    interface.shell_command("settings put global device_provisioned 0")
                    
                    self.result.steps_completed.append("reset_setup")
                    self.result.add_log("✓ Status de setup resetado")
                    
                    return True
            
            # Método 2: Bypass via database (requer root)
            if interface.is_root():
                return self._execute_root_bypass(interface)
            
            return False
            
        except Exception as e:
            self.result.add_log(f"Erro na execução ADB: {e}")
            return False
    
    def _execute_root_bypass(self, interface: ADBInterface) -> bool:
        """Executa bypass com acesso root"""
        try:
            self.result.add_log("Executando bypass com privilégios root")
            
            # Remove arquivos de FRP
            frp_files = [
                "/data/system/users/0/settings_global.xml",
                "/data/system/users/0/settings_secure.xml",
                "/data/system/sync/accounts.xml"
            ]
            
            for file_path in frp_files:
                result = interface.shell_command(f"rm {file_path}")
                if result.success:
                    self.result.add_log(f"✓ Removido: {file_path}")
                else:
                    self.result.add_log(f"✗ Falha ao remover: {file_path}")
            
            # Reinicia serviços
            interface.shell_command("stop")
            time.sleep(2)
            interface.shell_command("start")
            
            self.result.steps_completed.append("root_bypass")
            return True
            
        except Exception as e:
            self.result.add_log(f"Erro no bypass root: {e}")
            return False


class FastbootBypassMethod(BypassMethod):
    """Método de bypass via Fastboot"""
    
    def can_execute(self) -> Tuple[bool, str]:
        """Verifica se pode executar bypass via Fastboot"""
        if self.device.mode != DeviceMode.FASTBOOT:
            return False, "Dispositivo não está em modo Fastboot"
        
        try:
            interface = self.comm_manager.get_interface(self.device)
            if not isinstance(interface, FastbootInterface):
                return False, "Não foi possível criar interface Fastboot"
            
            # Verifica se bootloader pode ser desbloqueado
            unlocked = interface.get_variable("unlocked")
            if unlocked == "yes":
                return True, "Bootloader já desbloqueado"
            
            # Verifica se pode desbloquear
            unlock_ability = interface.get_variable("unlock_ability")
            if unlock_ability == "1":
                return True, "Bootloader pode ser desbloqueado"
            
            return False, "Bootloader não pode ser desbloqueado"
            
        except Exception as e:
            return False, f"Erro ao verificar Fastboot: {e}"
    
    def execute(self) -> BypassResult:
        """Executa bypass via Fastboot"""
        start_time = time.time()
        self.result.status = BypassStatus.IN_PROGRESS
        self.result.add_log("Iniciando bypass via Fastboot")
        
        try:
            interface = self.comm_manager.get_interface(self.device)
            
            # Verifica se bootloader já está desbloqueado
            if not interface.is_unlocked():
                self.result.add_log("Desbloqueando bootloader")
                unlock_result = interface.unlock_bootloader()
                
                if not unlock_result.success:
                    raise Exception("Falha ao desbloquear bootloader")
                
                self.result.steps_completed.append("bootloader_unlock")
                self.result.add_log("✓ Bootloader desbloqueado")
            
            # Apaga partição userdata para remover FRP
            self.result.add_log("Apagando partição userdata")
            erase_result = interface.erase_partition("userdata")
            
            if erase_result.success:
                self.result.steps_completed.append("userdata_erase")
                self.result.add_log("✓ Partição userdata apagada")
                
                # Reinicia o dispositivo
                self.result.add_log("Reiniciando dispositivo")
                interface.reboot()
                
                self.result.status = BypassStatus.SUCCESS
                self.result.success = True
                self.result.add_log("✓ Bypass Fastboot executado com sucesso")
            else:
                raise Exception("Falha ao apagar partição userdata")
            
        except Exception as e:
            self.result.status = BypassStatus.ERROR
            self.result.error_message = str(e)
            self.result.add_log(f"✗ Erro durante bypass Fastboot: {e}")
        
        finally:
            self.result.execution_time = time.time() - start_time
            self.result.add_log(f"Bypass finalizado em {self.result.execution_time:.2f}s")
        
        return self.result


class BypassStrategy:
    """Estratégia de bypass para um dispositivo específico"""
    
    def __init__(self, device: AndroidDevice, device_profile: DeviceProfile, 
                 exploit_manager: ExploitManager):
        self.device = device
        self.device_profile = device_profile
        self.exploit_manager = exploit_manager
        self.methods: List[Tuple[BypassMethod, float]] = []  # (método, prioridade)
        self._generate_strategy()
    
    def _generate_strategy(self) -> None:
        """Gera estratégia baseada no dispositivo e exploits disponíveis"""
        logger.info(f"Gerando estratégia para {self.device.device_id}")
        
        # Obtém exploits compatíveis
        compatible_exploits = self.exploit_manager.get_exploits_for_device(self.device_profile)
        
        # Ordena exploits por prioridade (risco baixo primeiro)
        compatible_exploits.sort(key=lambda e: (e.risk_enum.value, e.name))
        
        # Cria métodos baseado no modo do dispositivo e exploits
        if self.device.mode == DeviceMode.ADB:
            self.methods.append((ADBBypassMethod, 0.9))  # Alta prioridade para ADB
        
        if self.device.mode == DeviceMode.FASTBOOT:
            self.methods.append((FastbootBypassMethod, 0.8))  # Alta prioridade para Fastboot
        
        logger.info(f"Estratégia gerada com {len(self.methods)} métodos")
    
    def get_next_method(self) -> Optional[Tuple[type, float]]:
        """
        Retorna o próximo método a ser tentado
        
        Returns:
            Tupla (classe_método, prioridade) ou None se não há mais métodos
        """
        if self.methods:
            return self.methods.pop(0)
        return None
    
    def has_more_methods(self) -> bool:
        """Verifica se há mais métodos para tentar"""
        return len(self.methods) > 0


class FRPBypassEngine:
    """Engine principal de bypass FRP"""
    
    def __init__(self, device_database: DeviceDatabase, communication_manager: CommunicationManager):
        """
        Inicializa o engine de bypass
        
        Args:
            device_database: Base de dados de dispositivos
            communication_manager: Gerenciador de comunicação
        """
        self.device_database = device_database
        self.comm_manager = communication_manager
        self.exploit_manager = ExploitManager(device_database)
        self.active_sessions: Dict[str, 'BypassSession'] = {}
        self.session_lock = threading.Lock()
        
        logger.info("FRPBypassEngine inicializado")
    
    def start_bypass_session(self, device: AndroidDevice) -> str:
        """
        Inicia uma nova sessão de bypass
        
        Args:
            device: Dispositivo para bypass
            
        Returns:
            ID da sessão criada
        """
        with self.session_lock:
            session_id = f"session_{int(time.time())}_{device.serial}"
            session = BypassSession(session_id, device, self)
            self.active_sessions[session_id] = session
            
            logger.info(f"Sessão de bypass iniciada: {session_id}")
            return session_id
    
    def get_session(self, session_id: str) -> Optional['BypassSession']:
        """
        Obtém sessão por ID
        
        Args:
            session_id: ID da sessão
            
        Returns:
            BypassSession se encontrada
        """
        return self.active_sessions.get(session_id)
    
    def execute_bypass(self, device: AndroidDevice, max_attempts: int = 3) -> BypassResult:
        """
        Executa bypass em um dispositivo
        
        Args:
            device: Dispositivo para bypass
            max_attempts: Número máximo de tentativas
            
        Returns:
            Resultado final do bypass
        """
        logger.info(f"Iniciando bypass para dispositivo: {device.device_id}")
        
        # Busca perfil do dispositivo
        device_profile = self._find_device_profile(device)
        if not device_profile:
            return BypassResult(
                status=BypassStatus.ERROR,
                method_used="unknown",
                execution_time=0.0,
                error_message="Dispositivo não encontrado na base de dados"
            )
        
        # Cria estratégia
        strategy = BypassStrategy(device, device_profile, self.exploit_manager)
        
        # Executa tentativas
        attempt = 0
        while attempt < max_attempts and strategy.has_more_methods():
            attempt += 1
            logger.info(f"Tentativa {attempt}/{max_attempts}")
            
            method_info = strategy.get_next_method()
            if not method_info:
                break
            
            method_class, priority = method_info
            
            # Cria e executa método
            method = method_class(
                f"{method_class.__name__}_{attempt}",
                device,
                self.comm_manager
            )
            
            # Verifica se pode executar
            can_execute, reason = method.can_execute()
            if not can_execute:
                logger.warning(f"Método {method.name} não pode ser executado: {reason}")
                continue
            
            # Executa método
            result = method.execute()
            
            # Se foi bem-sucedido, retorna resultado
            if result.success:
                logger.info(f"Bypass bem-sucedido com método: {method.name}")
                return result
            
            logger.warning(f"Método {method.name} falhou: {result.error_message}")
        
        # Se chegou aqui, todas as tentativas falharam
        return BypassResult(
            status=BypassStatus.FAILED,
            method_used="multiple_attempts",
            execution_time=0.0,
            error_message=f"Todas as {attempt} tentativas falharam"
        )
    
    def _find_device_profile(self, device: AndroidDevice) -> Optional[DeviceProfile]:
        """
        Encontra perfil do dispositivo na base de dados
        
        Args:
            device: Dispositivo para buscar
            
        Returns:
            DeviceProfile se encontrado
        """
        # Busca por nome/modelo
        if device.model and device.model != "Unknown":
            profile = self.device_database.find_device_by_name(device.model)
            if profile:
                return profile
        
        # Busca por fabricante
        manufacturer_name = device.manufacturer.value.lower()
        devices = self.device_database.find_devices_by_manufacturer(manufacturer_name)
        
        if devices:
            # Retorna o primeiro dispositivo compatível
            # Em versão futura, pode usar heurísticas mais sofisticadas
            return devices[0]
        
        return None
    
    def get_engine_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do engine
        
        Returns:
            Dicionário com estatísticas
        """
        with self.session_lock:
            active_sessions = len(self.active_sessions)
            
            # Estatísticas de sessões
            session_stats = {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'in_progress': 0
            }
            
            for session in self.active_sessions.values():
                session_stats['total'] += 1
                if session.current_result:
                    if session.current_result.success:
                        session_stats['successful'] += 1
                    elif session.current_result.status == BypassStatus.FAILED:
                        session_stats['failed'] += 1
                    elif session.current_result.status == BypassStatus.IN_PROGRESS:
                        session_stats['in_progress'] += 1
        
        return {
            'active_sessions': active_sessions,
            'session_statistics': session_stats,
            'supported_devices': len(self.device_database.devices),
            'available_exploits': len(self.exploit_manager.exploits)
        }


class BypassSession:
    """Sessão de bypass com histórico e controle"""
    
    def __init__(self, session_id: str, device: AndroidDevice, engine: FRPBypassEngine):
        self.session_id = session_id
        self.device = device
        self.engine = engine
        self.start_time = time.time()
        self.current_result: Optional[BypassResult] = None
        self.attempt_history: List[BypassResult] = []
        self.is_cancelled = False
    
    def execute_async(self, callback: Optional[Callable] = None) -> threading.Thread:
        """
        Executa bypass de forma assíncrona
        
        Args:
            callback: Função a ser chamada quando completar
            
        Returns:
            Thread de execução
        """
        def run_bypass():
            self.current_result = self.engine.execute_bypass(self.device)
            self.attempt_history.append(self.current_result)
            
            if callback:
                callback(self.current_result)
        
        thread = threading.Thread(target=run_bypass, name=f"bypass_{self.session_id}")
        thread.start()
        return thread
    
    def cancel(self) -> None:
        """Cancela a sessão de bypass"""
        self.is_cancelled = True
        if self.current_result:
            self.current_result.status = BypassStatus.CANCELLED
            self.current_result.add_log("Sessão cancelada pelo usuário")
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        Retorna informações da sessão
        
        Returns:
            Dicionário com informações da sessão
        """
        return {
            'session_id': self.session_id,
            'device_id': self.device.device_id,
            'start_time': self.start_time,
            'duration': time.time() - self.start_time,
            'current_status': self.current_result.status.value if self.current_result else 'not_started',
            'attempts': len(self.attempt_history),
            'is_cancelled': self.is_cancelled
        }


if __name__ == "__main__":
    # Teste básico do módulo
    print("=== FRP Bypass Professional - Engine Test ===")
    
    from .device_detection import DeviceDetector
    
    # Inicializa componentes
    device_db = DeviceDatabase()
    comm_manager = CommunicationManager()
    engine = FRPBypassEngine(device_db, comm_manager)
    
    print(f"Engine inicializado com:")
    stats = engine.get_engine_statistics()
    print(f"- Dispositivos suportados: {stats['supported_devices']}")
    print(f"- Exploits disponíveis: {stats['available_exploits']}")
    print(f"- Sessões ativas: {stats['active_sessions']}")
    
    # Detecta dispositivos
    detector = DeviceDetector()
    devices = detector.scan_usb_devices()
    
    if devices:
        device = devices[0]
        print(f"\nDispositivo detectado: {device.device_id}")
        print(f"Modo: {device.mode.value}")
        print(f"FRP Bloqueado: {device.frp_locked}")
        
        if device.frp_locked:
            print("\n⚠️  Para executar bypass real, descomente as linhas abaixo:")
            print("# session_id = engine.start_bypass_session(device)")
            print("# session = engine.get_session(session_id)")
            print("# result = engine.execute_bypass(device)")
            print("# print(f'Resultado: {result.status.value}')")
    else:
        print("\nNenhum dispositivo detectado para teste")
