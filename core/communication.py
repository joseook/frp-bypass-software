"""
Communication Protocol Module
============================

Sistema de comunicação com dispositivos Android via USB, ADB e Fastboot.
Fornece interfaces padronizadas para diferentes protocolos de comunicação.

Classes:
- USBCommunicator: Comunicação USB de baixo nível
- ADBInterface: Interface para Android Debug Bridge
- FastbootInterface: Interface para modo Fastboot
- CommunicationManager: Gerenciador central de comunicação
"""

import subprocess
import time
import threading
import queue
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass
from enum import Enum
import usb.core
import usb.util
from loguru import logger

from .device_detection import AndroidDevice, DeviceMode


class CommandResult:
    """Resultado de um comando executado"""
    
    def __init__(self, success: bool, output: str = "", error: str = "", 
                 exit_code: int = 0, execution_time: float = 0.0):
        self.success = success
        self.output = output
        self.error = error
        self.exit_code = exit_code
        self.execution_time = execution_time
    
    def __bool__(self) -> bool:
        return self.success
    
    def __str__(self) -> str:
        return f"CommandResult(success={self.success}, exit_code={self.exit_code})"


class CommunicationError(Exception):
    """Exceção base para erros de comunicação"""
    pass


class ADBError(CommunicationError):
    """Erro específico do ADB"""
    pass


class FastbootError(CommunicationError):
    """Erro específico do Fastboot"""
    pass


class USBError(CommunicationError):
    """Erro específico de comunicação USB"""
    pass


class USBCommunicator:
    """Comunicação USB de baixo nível"""
    
    def __init__(self, device: AndroidDevice):
        """
        Inicializa comunicador USB
        
        Args:
            device: Dispositivo Android para comunicação
        """
        self.device = device
        self.usb_device = None
        self.endpoint_in = None
        self.endpoint_out = None
        self._connect_usb()
    
    def _connect_usb(self) -> None:
        """Conecta ao dispositivo USB"""
        try:
            # Encontra o dispositivo USB
            self.usb_device = usb.core.find(
                idVendor=self.device.vendor_id,
                idProduct=self.device.product_id
            )
            
            if self.usb_device is None:
                raise USBError(f"Dispositivo USB não encontrado: {self.device.device_id}")
            
            # Configura o dispositivo
            try:
                self.usb_device.set_configuration()
            except usb.core.USBError as e:
                logger.warning(f"Não foi possível configurar dispositivo USB: {e}")
            
            # Encontra endpoints
            self._find_endpoints()
            
            logger.info(f"Conexão USB estabelecida com {self.device.device_id}")
            
        except Exception as e:
            raise USBError(f"Erro ao conectar USB: {e}")
    
    def _find_endpoints(self) -> None:
        """Encontra endpoints de entrada e saída"""
        try:
            config = self.usb_device.get_active_configuration()
            interface = config[(0, 0)]
            
            for endpoint in interface:
                if usb.util.endpoint_direction(endpoint.bEndpointAddress) == usb.util.ENDPOINT_OUT:
                    self.endpoint_out = endpoint
                elif usb.util.endpoint_direction(endpoint.bEndpointAddress) == usb.util.ENDPOINT_IN:
                    self.endpoint_in = endpoint
            
            logger.debug(f"Endpoints encontrados - IN: {self.endpoint_in}, OUT: {self.endpoint_out}")
            
        except Exception as e:
            logger.warning(f"Erro ao encontrar endpoints: {e}")
    
    def send_data(self, data: bytes, timeout: int = 5000) -> bool:
        """
        Envia dados via USB
        
        Args:
            data: Dados para enviar
            timeout: Timeout em millisegundos
            
        Returns:
            True se enviado com sucesso
        """
        try:
            if self.endpoint_out:
                bytes_written = self.endpoint_out.write(data, timeout)
                return bytes_written == len(data)
            return False
        except Exception as e:
            logger.error(f"Erro ao enviar dados USB: {e}")
            return False
    
    def receive_data(self, size: int = 1024, timeout: int = 5000) -> Optional[bytes]:
        """
        Recebe dados via USB
        
        Args:
            size: Tamanho máximo dos dados
            timeout: Timeout em millisegundos
            
        Returns:
            Dados recebidos ou None se erro
        """
        try:
            if self.endpoint_in:
                data = self.endpoint_in.read(size, timeout)
                return bytes(data)
            return None
        except Exception as e:
            logger.error(f"Erro ao receber dados USB: {e}")
            return None
    
    def disconnect(self) -> None:
        """Desconecta do dispositivo USB"""
        try:
            if self.usb_device:
                usb.util.dispose_resources(self.usb_device)
                self.usb_device = None
                logger.info(f"Desconectado do dispositivo USB: {self.device.device_id}")
        except Exception as e:
            logger.error(f"Erro ao desconectar USB: {e}")


class ADBInterface:
    """Interface para Android Debug Bridge"""
    
    def __init__(self, device: AndroidDevice):
        """
        Inicializa interface ADB
        
        Args:
            device: Dispositivo Android
        """
        self.device = device
        self.serial = device.serial
        self._verify_adb_connection()
    
    def _verify_adb_connection(self) -> None:
        """Verifica se o dispositivo está acessível via ADB"""
        result = self.execute_command("get-state")
        if not result.success or "device" not in result.output:
            raise ADBError(f"Dispositivo {self.serial} não acessível via ADB")
    
    def execute_command(self, command: str, timeout: int = 30) -> CommandResult:
        """
        Executa comando ADB
        
        Args:
            command: Comando ADB (sem 'adb -s serial')
            timeout: Timeout em segundos
            
        Returns:
            Resultado do comando
        """
        start_time = time.time()
        
        try:
            # Constrói comando completo
            full_command = ['adb', '-s', self.serial] + command.split()
            
            logger.debug(f"Executando ADB: {' '.join(full_command)}")
            
            # Executa comando
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr,
                exit_code=result.returncode,
                execution_time=execution_time
            )
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            logger.error(f"Timeout no comando ADB: {command}")
            return CommandResult(
                success=False,
                error=f"Timeout após {timeout}s",
                exit_code=-1,
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Erro ao executar comando ADB: {e}")
            return CommandResult(
                success=False,
                error=str(e),
                exit_code=-1,
                execution_time=execution_time
            )
    
    def shell_command(self, command: str, timeout: int = 30) -> CommandResult:
        """
        Executa comando shell no dispositivo
        
        Args:
            command: Comando shell
            timeout: Timeout em segundos
            
        Returns:
            Resultado do comando
        """
        return self.execute_command(f"shell {command}", timeout)
    
    def get_property(self, prop: str) -> Optional[str]:
        """
        Obtém propriedade do sistema
        
        Args:
            prop: Nome da propriedade
            
        Returns:
            Valor da propriedade ou None
        """
        result = self.shell_command(f"getprop {prop}")
        if result.success:
            return result.output.strip()
        return None
    
    def install_apk(self, apk_path: str, replace: bool = True) -> CommandResult:
        """
        Instala APK no dispositivo
        
        Args:
            apk_path: Caminho para o APK
            replace: Se deve substituir app existente
            
        Returns:
            Resultado da instalação
        """
        flags = "-r" if replace else ""
        return self.execute_command(f"install {flags} {apk_path}")
    
    def push_file(self, local_path: str, remote_path: str) -> CommandResult:
        """
        Envia arquivo para o dispositivo
        
        Args:
            local_path: Caminho local do arquivo
            remote_path: Caminho remoto no dispositivo
            
        Returns:
            Resultado da operação
        """
        return self.execute_command(f"push {local_path} {remote_path}")
    
    def pull_file(self, remote_path: str, local_path: str) -> CommandResult:
        """
        Baixa arquivo do dispositivo
        
        Args:
            remote_path: Caminho remoto no dispositivo
            local_path: Caminho local para salvar
            
        Returns:
            Resultado da operação
        """
        return self.execute_command(f"pull {remote_path} {local_path}")
    
    def reboot(self, mode: str = "") -> CommandResult:
        """
        Reinicia o dispositivo
        
        Args:
            mode: Modo de reinicialização (bootloader, recovery, etc.)
            
        Returns:
            Resultado da operação
        """
        command = f"reboot {mode}".strip()
        return self.execute_command(command)
    
    def is_root(self) -> bool:
        """
        Verifica se tem acesso root
        
        Returns:
            True se tem acesso root
        """
        result = self.shell_command("id")
        return result.success and "uid=0" in result.output


class FastbootInterface:
    """Interface para modo Fastboot"""
    
    def __init__(self, device: AndroidDevice):
        """
        Inicializa interface Fastboot
        
        Args:
            device: Dispositivo Android
        """
        self.device = device
        self.serial = device.serial
        self._verify_fastboot_connection()
    
    def _verify_fastboot_connection(self) -> None:
        """Verifica se o dispositivo está acessível via Fastboot"""
        result = self.execute_command("devices")
        if not result.success or self.serial not in result.output:
            raise FastbootError(f"Dispositivo {self.serial} não acessível via Fastboot")
    
    def execute_command(self, command: str, timeout: int = 60) -> CommandResult:
        """
        Executa comando Fastboot
        
        Args:
            command: Comando Fastboot (sem 'fastboot -s serial')
            timeout: Timeout em segundos
            
        Returns:
            Resultado do comando
        """
        start_time = time.time()
        
        try:
            # Constrói comando completo
            full_command = ['fastboot', '-s', self.serial] + command.split()
            
            logger.debug(f"Executando Fastboot: {' '.join(full_command)}")
            
            # Executa comando
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            # Fastboot às vezes retorna saída no stderr
            output = result.stdout or result.stderr
            
            return CommandResult(
                success=result.returncode == 0,
                output=output,
                error=result.stderr if result.stdout else "",
                exit_code=result.returncode,
                execution_time=execution_time
            )
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            logger.error(f"Timeout no comando Fastboot: {command}")
            return CommandResult(
                success=False,
                error=f"Timeout após {timeout}s",
                exit_code=-1,
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Erro ao executar comando Fastboot: {e}")
            return CommandResult(
                success=False,
                error=str(e),
                exit_code=-1,
                execution_time=execution_time
            )
    
    def get_variable(self, var: str) -> Optional[str]:
        """
        Obtém variável do bootloader
        
        Args:
            var: Nome da variável
            
        Returns:
            Valor da variável ou None
        """
        result = self.execute_command(f"getvar {var}")
        if result.success:
            # Procura pela linha com a variável
            for line in result.output.split('\n'):
                if f"{var}:" in line:
                    return line.split(':', 1)[1].strip()
        return None
    
    def flash_partition(self, partition: str, image_path: str) -> CommandResult:
        """
        Grava imagem em partição
        
        Args:
            partition: Nome da partição
            image_path: Caminho para a imagem
            
        Returns:
            Resultado da operação
        """
        return self.execute_command(f"flash {partition} {image_path}")
    
    def erase_partition(self, partition: str) -> CommandResult:
        """
        Apaga partição
        
        Args:
            partition: Nome da partição
            
        Returns:
            Resultado da operação
        """
        return self.execute_command(f"erase {partition}")
    
    def unlock_bootloader(self) -> CommandResult:
        """
        Desbloqueia o bootloader
        
        Returns:
            Resultado da operação
        """
        return self.execute_command("oem unlock")
    
    def reboot(self, mode: str = "") -> CommandResult:
        """
        Reinicia o dispositivo
        
        Args:
            mode: Modo de reinicialização (bootloader, etc.)
            
        Returns:
            Resultado da operação
        """
        command = f"reboot {mode}".strip()
        return self.execute_command(command)
    
    def is_unlocked(self) -> bool:
        """
        Verifica se o bootloader está desbloqueado
        
        Returns:
            True se desbloqueado
        """
        unlocked = self.get_variable("unlocked")
        return unlocked == "yes" if unlocked else False


class CommunicationManager:
    """Gerenciador central de comunicação"""
    
    def __init__(self):
        """Inicializa o gerenciador de comunicação"""
        self.active_connections: Dict[str, Any] = {}
        self.connection_lock = threading.Lock()
        logger.info("CommunicationManager inicializado")
    
    def get_interface(self, device: AndroidDevice) -> Union[ADBInterface, FastbootInterface, USBCommunicator]:
        """
        Obtém interface apropriada para o dispositivo
        
        Args:
            device: Dispositivo Android
            
        Returns:
            Interface de comunicação apropriada
            
        Raises:
            CommunicationError: Se não conseguir criar interface
        """
        with self.connection_lock:
            device_id = device.device_id
            
            # Verifica se já existe conexão ativa
            if device_id in self.active_connections:
                return self.active_connections[device_id]
            
            # Cria nova interface baseada no modo do dispositivo
            try:
                if device.mode == DeviceMode.ADB:
                    interface = ADBInterface(device)
                elif device.mode == DeviceMode.FASTBOOT:
                    interface = FastbootInterface(device)
                else:
                    interface = USBCommunicator(device)
                
                self.active_connections[device_id] = interface
                logger.info(f"Interface criada para {device_id}: {type(interface).__name__}")
                
                return interface
                
            except Exception as e:
                logger.error(f"Erro ao criar interface para {device_id}: {e}")
                raise CommunicationError(f"Não foi possível criar interface: {e}")
    
    def close_connection(self, device: AndroidDevice) -> None:
        """
        Fecha conexão com dispositivo
        
        Args:
            device: Dispositivo para fechar conexão
        """
        with self.connection_lock:
            device_id = device.device_id
            
            if device_id in self.active_connections:
                interface = self.active_connections[device_id]
                
                # Fecha conexão se for USB
                if isinstance(interface, USBCommunicator):
                    interface.disconnect()
                
                del self.active_connections[device_id]
                logger.info(f"Conexão fechada para {device_id}")
    
    def close_all_connections(self) -> None:
        """Fecha todas as conexões ativas"""
        with self.connection_lock:
            for device_id, interface in self.active_connections.items():
                if isinstance(interface, USBCommunicator):
                    interface.disconnect()
                logger.info(f"Conexão fechada para {device_id}")
            
            self.active_connections.clear()
            logger.info("Todas as conexões foram fechadas")
    
    def test_connection(self, device: AndroidDevice) -> bool:
        """
        Testa conexão com dispositivo
        
        Args:
            device: Dispositivo para testar
            
        Returns:
            True se conexão está funcionando
        """
        try:
            interface = self.get_interface(device)
            
            if isinstance(interface, ADBInterface):
                result = interface.execute_command("get-state")
                return result.success
            elif isinstance(interface, FastbootInterface):
                result = interface.execute_command("devices")
                return result.success and device.serial in result.output
            else:
                # Para USB, tenta enviar dados de teste
                return interface.usb_device is not None
                
        except Exception as e:
            logger.error(f"Erro ao testar conexão: {e}")
            return False
    
    def get_connection_status(self) -> Dict[str, Dict]:
        """
        Obtém status de todas as conexões
        
        Returns:
            Dicionário com status das conexões
        """
        status = {}
        
        with self.connection_lock:
            for device_id, interface in self.active_connections.items():
                status[device_id] = {
                    'type': type(interface).__name__,
                    'connected': True,
                    'timestamp': time.time()
                }
        
        return status


# Funções utilitárias
def check_adb_available() -> bool:
    """
    Verifica se ADB está disponível
    
    Returns:
        True se ADB está instalado e funcionando
    """
    try:
        result = subprocess.run(['adb', 'version'], capture_output=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_fastboot_available() -> bool:
    """
    Verifica se Fastboot está disponível
    
    Returns:
        True se Fastboot está instalado e funcionando
    """
    try:
        result = subprocess.run(['fastboot', '--version'], capture_output=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_adb_devices() -> List[str]:
    """
    Lista dispositivos conectados via ADB
    
    Returns:
        Lista de serials dos dispositivos
    """
    devices = []
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Pula header
            for line in lines:
                if '\tdevice' in line:
                    serial = line.split('\t')[0]
                    devices.append(serial)
    except Exception as e:
        logger.error(f"Erro ao listar dispositivos ADB: {e}")
    
    return devices


def get_fastboot_devices() -> List[str]:
    """
    Lista dispositivos conectados via Fastboot
    
    Returns:
        Lista de serials dos dispositivos
    """
    devices = []
    try:
        result = subprocess.run(['fastboot', 'devices'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if '\tfastboot' in line:
                    serial = line.split('\t')[0]
                    devices.append(serial)
    except Exception as e:
        logger.error(f"Erro ao listar dispositivos Fastboot: {e}")
    
    return devices


if __name__ == "__main__":
    # Teste básico do módulo
    print("=== FRP Bypass Professional - Communication Test ===")
    
    print(f"ADB disponível: {check_adb_available()}")
    print(f"Fastboot disponível: {check_fastboot_available()}")
    
    adb_devices = get_adb_devices()
    fastboot_devices = get_fastboot_devices()
    
    print(f"\nDispositivos ADB: {len(adb_devices)}")
    for device in adb_devices:
        print(f"  - {device}")
    
    print(f"\nDispositivos Fastboot: {len(fastboot_devices)}")
    for device in fastboot_devices:
        print(f"  - {device}")
    
    # Teste do gerenciador
    manager = CommunicationManager()
    status = manager.get_connection_status()
    print(f"\nStatus das conexões: {len(status)} ativas")
