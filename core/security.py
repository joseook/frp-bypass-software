"""
Security and Compliance Module
==============================

Sistema de segurança e conformidade para o FRP Bypass Professional.
Implementa controles de acesso, auditoria, e verificações de conformidade legal.

Classes:
- AuditLogger: Sistema de auditoria e logs
- LicenseManager: Gerenciamento de licenças
- ComplianceChecker: Verificações de conformidade legal
- SecurityManager: Gerenciador central de segurança
"""

import hashlib
import json
import time
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from loguru import logger

from .device_detection import AndroidDevice


class AuditLevel(Enum):
    """Níveis de auditoria"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    SECURITY = "security"


class LicenseStatus(Enum):
    """Status da licença"""
    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    TRIAL = "trial"
    SUSPENDED = "suspended"


@dataclass
class AuditEntry:
    """Entrada de auditoria"""
    
    timestamp: float
    session_id: str
    user_id: str
    device_id: str
    action: str
    level: AuditLevel
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    result: Optional[str] = None
    
    def __post_init__(self):
        """Pós-inicialização"""
        if self.timestamp == 0:
            self.timestamp = time.time()
    
    @property
    def timestamp_iso(self) -> str:
        """Timestamp em formato ISO"""
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.timestamp))
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        data = asdict(self)
        data['level'] = self.level.value
        data['timestamp_iso'] = self.timestamp_iso
        return data


@dataclass
class LicenseInfo:
    """Informações da licença"""
    
    license_key: str
    user_name: str
    organization: str
    license_type: str
    issue_date: float
    expiry_date: float
    max_devices: int
    features: List[str]
    status: LicenseStatus = LicenseStatus.VALID
    
    @property
    def is_valid(self) -> bool:
        """Verifica se a licença é válida"""
        now = time.time()
        return (
            self.status == LicenseStatus.VALID and
            self.issue_date <= now <= self.expiry_date
        )
    
    @property
    def days_remaining(self) -> int:
        """Dias restantes da licença"""
        if self.expiry_date == 0:  # Licença perpétua
            return -1
        
        remaining = (self.expiry_date - time.time()) / (24 * 3600)
        return max(0, int(remaining))
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        data = asdict(self)
        data['status'] = self.status.value
        data['is_valid'] = self.is_valid
        data['days_remaining'] = self.days_remaining
        return data


class AuditLogger:
    """Sistema de auditoria e logs"""
    
    def __init__(self, log_directory: str = "logs"):
        """
        Inicializa o sistema de auditoria
        
        Args:
            log_directory: Diretório para armazenar logs
        """
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(exist_ok=True)
        
        self.current_session = str(uuid.uuid4())
        self.log_file = self.log_directory / f"audit_{time.strftime('%Y%m%d')}.json"
        
        logger.info(f"AuditLogger inicializado - Sessão: {self.current_session}")
    
    def log_action(self, user_id: str, device_id: str, action: str, 
                   level: AuditLevel = AuditLevel.INFO, details: Dict[str, Any] = None,
                   result: str = None) -> None:
        """
        Registra uma ação no log de auditoria
        
        Args:
            user_id: ID do usuário
            device_id: ID do dispositivo
            action: Ação realizada
            level: Nível de auditoria
            details: Detalhes adicionais
            result: Resultado da ação
        """
        entry = AuditEntry(
            timestamp=time.time(),
            session_id=self.current_session,
            user_id=user_id,
            device_id=device_id,
            action=action,
            level=level,
            details=details or {},
            result=result
        )
        
        self._write_audit_entry(entry)
        
        # Log também no sistema de logging principal
        log_message = f"AUDIT [{level.value.upper()}] {user_id}@{device_id}: {action}"
        if result:
            log_message += f" -> {result}"
        
        if level == AuditLevel.CRITICAL:
            logger.critical(log_message)
        elif level == AuditLevel.WARNING:
            logger.warning(log_message)
        elif level == AuditLevel.SECURITY:
            logger.error(f"SECURITY: {log_message}")
        else:
            logger.info(log_message)
    
    def _write_audit_entry(self, entry: AuditEntry) -> None:
        """Escreve entrada de auditoria no arquivo"""
        try:
            # Lê entradas existentes
            entries = []
            if self.log_file.exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    try:
                        entries = json.load(f)
                    except json.JSONDecodeError:
                        entries = []
            
            # Adiciona nova entrada
            entries.append(entry.to_dict())
            
            # Escreve de volta
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(entries, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Erro ao escrever log de auditoria: {e}")
    
    def get_audit_entries(self, start_date: Optional[str] = None, 
                         end_date: Optional[str] = None,
                         user_id: Optional[str] = None,
                         level: Optional[AuditLevel] = None) -> List[AuditEntry]:
        """
        Obtém entradas de auditoria com filtros
        
        Args:
            start_date: Data de início (YYYY-MM-DD)
            end_date: Data de fim (YYYY-MM-DD)
            user_id: Filtrar por usuário
            level: Filtrar por nível
            
        Returns:
            Lista de entradas de auditoria
        """
        entries = []
        
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    for entry_data in data:
                        # Aplicar filtros
                        if user_id and entry_data.get('user_id') != user_id:
                            continue
                        
                        if level and entry_data.get('level') != level.value:
                            continue
                        
                        # Converter de volta para AuditEntry
                        entry = AuditEntry(
                            timestamp=entry_data['timestamp'],
                            session_id=entry_data['session_id'],
                            user_id=entry_data['user_id'],
                            device_id=entry_data['device_id'],
                            action=entry_data['action'],
                            level=AuditLevel(entry_data['level']),
                            details=entry_data['details'],
                            result=entry_data.get('result')
                        )
                        
                        entries.append(entry)
        
        except Exception as e:
            logger.error(f"Erro ao ler logs de auditoria: {e}")
        
        return entries
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtém estatísticas dos logs de auditoria
        
        Returns:
            Dicionário com estatísticas
        """
        entries = self.get_audit_entries()
        
        if not entries:
            return {"total_entries": 0}
        
        # Estatísticas por nível
        level_stats = {}
        for level in AuditLevel:
            level_stats[level.value] = sum(1 for e in entries if e.level == level)
        
        # Usuários únicos
        unique_users = set(e.user_id for e in entries)
        
        # Dispositivos únicos
        unique_devices = set(e.device_id for e in entries)
        
        # Sessões únicas
        unique_sessions = set(e.session_id for e in entries)
        
        return {
            "total_entries": len(entries),
            "level_distribution": level_stats,
            "unique_users": len(unique_users),
            "unique_devices": len(unique_devices),
            "unique_sessions": len(unique_sessions),
            "date_range": {
                "start": min(e.timestamp_iso for e in entries),
                "end": max(e.timestamp_iso for e in entries)
            }
        }


class LicenseManager:
    """Gerenciador de licenças"""
    
    def __init__(self, license_file: str = "license.key"):
        """
        Inicializa o gerenciador de licenças
        
        Args:
            license_file: Arquivo de licença
        """
        self.license_file = Path(license_file)
        self.current_license: Optional[LicenseInfo] = None
        self.encryption_key = self._get_encryption_key()
        
        self._load_license()
        logger.info("LicenseManager inicializado")
    
    def _get_encryption_key(self) -> bytes:
        """Gera chave de criptografia baseada no sistema"""
        # Em produção, usar informações mais específicas do sistema
        system_info = f"{os.name}_{os.environ.get('USERNAME', 'user')}"
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'frp_bypass_salt',
            iterations=100000,
        )
        
        return base64.urlsafe_b64encode(kdf.derive(system_info.encode()))
    
    def _load_license(self) -> None:
        """Carrega licença do arquivo"""
        try:
            if not self.license_file.exists():
                logger.warning("Arquivo de licença não encontrado")
                return
            
            with open(self.license_file, 'rb') as f:
                encrypted_data = f.read()
            
            # Descriptografa
            fernet = Fernet(self.encryption_key)
            decrypted_data = fernet.decrypt(encrypted_data)
            license_data = json.loads(decrypted_data.decode())
            
            # Cria objeto LicenseInfo
            self.current_license = LicenseInfo(
                license_key=license_data['license_key'],
                user_name=license_data['user_name'],
                organization=license_data['organization'],
                license_type=license_data['license_type'],
                issue_date=license_data['issue_date'],
                expiry_date=license_data['expiry_date'],
                max_devices=license_data['max_devices'],
                features=license_data['features'],
                status=LicenseStatus(license_data.get('status', 'valid'))
            )
            
            logger.info(f"Licença carregada para: {self.current_license.user_name}")
            
        except Exception as e:
            logger.error(f"Erro ao carregar licença: {e}")
            self.current_license = None
    
    def install_license(self, license_key: str, user_name: str, organization: str) -> bool:
        """
        Instala uma nova licença
        
        Args:
            license_key: Chave da licença
            user_name: Nome do usuário
            organization: Organização
            
        Returns:
            True se instalada com sucesso
        """
        try:
            # Valida formato da chave (exemplo básico)
            if not self._validate_license_key(license_key):
                logger.error("Chave de licença inválida")
                return False
            
            # Cria licença (exemplo - em produção seria validada com servidor)
            license_info = LicenseInfo(
                license_key=license_key,
                user_name=user_name,
                organization=organization,
                license_type="professional",
                issue_date=time.time(),
                expiry_date=time.time() + (365 * 24 * 3600),  # 1 ano
                max_devices=10,
                features=["frp_bypass", "multi_device", "audit_logs"],
                status=LicenseStatus.VALID
            )
            
            # Salva licença criptografada
            license_data = license_info.to_dict()
            json_data = json.dumps(license_data).encode()
            
            fernet = Fernet(self.encryption_key)
            encrypted_data = fernet.encrypt(json_data)
            
            with open(self.license_file, 'wb') as f:
                f.write(encrypted_data)
            
            self.current_license = license_info
            logger.info(f"Licença instalada para: {user_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao instalar licença: {e}")
            return False
    
    def _validate_license_key(self, license_key: str) -> bool:
        """Valida formato da chave de licença"""
        # Validação básica - em produção seria mais complexa
        return (
            len(license_key) >= 20 and
            '-' in license_key and
            license_key.replace('-', '').isalnum()
        )
    
    def check_license(self) -> Tuple[bool, str]:
        """
        Verifica status da licença
        
        Returns:
            Tupla (válida, motivo)
        """
        if not self.current_license:
            return False, "Nenhuma licença instalada"
        
        if not self.current_license.is_valid:
            if self.current_license.status == LicenseStatus.EXPIRED:
                return False, "Licença expirada"
            elif self.current_license.status == LicenseStatus.SUSPENDED:
                return False, "Licença suspensa"
            else:
                return False, "Licença inválida"
        
        # Verifica se está próxima do vencimento
        days_remaining = self.current_license.days_remaining
        if 0 < days_remaining <= 30:
            logger.warning(f"Licença expira em {days_remaining} dias")
        
        return True, "Licença válida"
    
    def get_license_info(self) -> Optional[Dict[str, Any]]:
        """
        Obtém informações da licença atual
        
        Returns:
            Dicionário com informações ou None
        """
        if self.current_license:
            return self.current_license.to_dict()
        return None
    
    def has_feature(self, feature: str) -> bool:
        """
        Verifica se a licença possui uma funcionalidade
        
        Args:
            feature: Nome da funcionalidade
            
        Returns:
            True se possui a funcionalidade
        """
        if not self.current_license or not self.current_license.is_valid:
            return False
        
        return feature in self.current_license.features


class ComplianceChecker:
    """Verificações de conformidade legal"""
    
    def __init__(self, audit_logger: AuditLogger):
        """
        Inicializa verificador de conformidade
        
        Args:
            audit_logger: Sistema de auditoria
        """
        self.audit_logger = audit_logger
        self.disclaimers_accepted = set()
        logger.info("ComplianceChecker inicializado")
    
    def check_device_ownership(self, device: AndroidDevice, user_id: str) -> Tuple[bool, str]:
        """
        Verifica indicadores de propriedade do dispositivo
        
        Args:
            device: Dispositivo a verificar
            user_id: ID do usuário
            
        Returns:
            Tupla (pode_continuar, motivo)
        """
        self.audit_logger.log_action(
            user_id=user_id,
            device_id=device.device_id,
            action="ownership_check",
            level=AuditLevel.SECURITY,
            details={"device_info": device.to_dict()}
        )
        
        # Verificações básicas de propriedade
        warnings = []
        
        # Se o dispositivo está em modo normal e desbloqueado, é um bom sinal
        if device.mode.value == "normal" and device.usb_debugging:
            # Usuário teve que habilitar USB debugging manualmente
            pass
        elif device.mode.value in ["fastboot", "download", "recovery"]:
            warnings.append("Dispositivo em modo de recuperação/download")
        
        # Se há conta Google configurada, pode indicar uso ativo
        if device.google_account:
            warnings.append(f"Conta Google ativa: {device.google_account}")
        
        if warnings:
            warning_msg = "Possíveis indicadores de propriedade questionável: " + "; ".join(warnings)
            self.audit_logger.log_action(
                user_id=user_id,
                device_id=device.device_id,
                action="ownership_warning",
                level=AuditLevel.WARNING,
                details={"warnings": warnings}
            )
            
            return False, warning_msg
        
        return True, "Verificação de propriedade aprovada"
    
    def require_disclaimer_acceptance(self, user_id: str, disclaimer_type: str) -> bool:
        """
        Requer aceitação de termo de responsabilidade
        
        Args:
            user_id: ID do usuário
            disclaimer_type: Tipo do termo
            
        Returns:
            True se já foi aceito
        """
        disclaimer_key = f"{user_id}_{disclaimer_type}"
        
        if disclaimer_key in self.disclaimers_accepted:
            return True
        
        # Em implementação real, seria apresentado o termo ao usuário
        disclaimer_text = self._get_disclaimer_text(disclaimer_type)
        
        self.audit_logger.log_action(
            user_id=user_id,
            device_id="system",
            action="disclaimer_required",
            level=AuditLevel.INFO,
            details={"disclaimer_type": disclaimer_type}
        )
        
        return False
    
    def accept_disclaimer(self, user_id: str, disclaimer_type: str) -> None:
        """
        Registra aceitação de termo
        
        Args:
            user_id: ID do usuário
            disclaimer_type: Tipo do termo
        """
        disclaimer_key = f"{user_id}_{disclaimer_type}"
        self.disclaimers_accepted.add(disclaimer_key)
        
        self.audit_logger.log_action(
            user_id=user_id,
            device_id="system",
            action="disclaimer_accepted",
            level=AuditLevel.SECURITY,
            details={"disclaimer_type": disclaimer_type}
        )
        
        logger.info(f"Termo aceito: {disclaimer_type} por {user_id}")
    
    def _get_disclaimer_text(self, disclaimer_type: str) -> str:
        """Obtém texto do termo de responsabilidade"""
        disclaimers = {
            "frp_bypass": """
TERMO DE RESPONSABILIDADE - BYPASS FRP

ATENÇÃO: O uso deste software para bypass de FRP (Factory Reset Protection) 
deve estar em conformidade com as leis locais e internacionais.

VOCÊ DECLARA QUE:
1. É o proprietário legítimo do dispositivo OU tem autorização expressa
2. Não utilizará este software para atividades ilegais
3. Assume total responsabilidade pelo uso desta ferramenta
4. Entende os riscos envolvidos na modificação do dispositivo

O desenvolvedor não se responsabiliza por:
- Uso indevido do software
- Danos ao dispositivo
- Consequências legais do uso inadequado
- Violação de termos de serviço de terceiros

AO CONTINUAR, VOCÊ ACEITA TODOS OS TERMOS ACIMA.
""",
            "data_modification": """
AVISO - MODIFICAÇÃO DE DADOS DO DISPOSITIVO

Esta operação irá modificar dados do sistema do dispositivo Android.
Isso pode resultar em:
- Perda de dados do usuário
- Invalidação da garantia
- Problemas de funcionamento
- Necessidade de restauração completa

CONTINUE APENAS SE TIVER CERTEZA DO QUE ESTÁ FAZENDO.
"""
        }
        
        return disclaimers.get(disclaimer_type, "Termo não encontrado")
    
    def log_bypass_attempt(self, user_id: str, device: AndroidDevice, 
                          method: str, result: str) -> None:
        """
        Registra tentativa de bypass para auditoria
        
        Args:
            user_id: ID do usuário
            device: Dispositivo alvo
            method: Método utilizado
            result: Resultado da operação
        """
        self.audit_logger.log_action(
            user_id=user_id,
            device_id=device.device_id,
            action="frp_bypass_attempt",
            level=AuditLevel.CRITICAL,
            details={
                "method": method,
                "device_manufacturer": device.manufacturer.value,
                "device_model": device.model,
                "android_version": device.android_version,
                "frp_status_before": device.frp_locked
            },
            result=result
        )


class SecurityManager:
    """Gerenciador central de segurança"""
    
    def __init__(self, log_directory: str = "logs", license_file: str = "license.key"):
        """
        Inicializa o gerenciador de segurança
        
        Args:
            log_directory: Diretório de logs
            license_file: Arquivo de licença
        """
        self.audit_logger = AuditLogger(log_directory)
        self.license_manager = LicenseManager(license_file)
        self.compliance_checker = ComplianceChecker(self.audit_logger)
        
        logger.info("SecurityManager inicializado")
    
    def authorize_bypass(self, user_id: str, device: AndroidDevice) -> Tuple[bool, str]:
        """
        Autoriza operação de bypass
        
        Args:
            user_id: ID do usuário
            device: Dispositivo alvo
            
        Returns:
            Tupla (autorizado, motivo)
        """
        # Verifica licença
        license_valid, license_reason = self.license_manager.check_license()
        if not license_valid:
            return False, f"Licença inválida: {license_reason}"
        
        # Verifica funcionalidade
        if not self.license_manager.has_feature("frp_bypass"):
            return False, "Licença não possui funcionalidade de bypass FRP"
        
        # Verifica propriedade do dispositivo
        ownership_ok, ownership_reason = self.compliance_checker.check_device_ownership(device, user_id)
        if not ownership_ok:
            return False, f"Verificação de propriedade: {ownership_reason}"
        
        # Verifica aceitação de termos
        if not self.compliance_checker.require_disclaimer_acceptance(user_id, "frp_bypass"):
            return False, "É necessário aceitar o termo de responsabilidade"
        
        # Se chegou aqui, está autorizado
        self.audit_logger.log_action(
            user_id=user_id,
            device_id=device.device_id,
            action="bypass_authorized",
            level=AuditLevel.SECURITY,
            details={"authorization_checks_passed": True}
        )
        
        return True, "Operação autorizada"
    
    def get_security_status(self) -> Dict[str, Any]:
        """
        Obtém status geral de segurança
        
        Returns:
            Dicionário com status de segurança
        """
        license_info = self.license_manager.get_license_info()
        audit_stats = self.audit_logger.get_statistics()
        
        return {
            "license_status": {
                "valid": self.license_manager.check_license()[0],
                "info": license_info
            },
            "audit_statistics": audit_stats,
            "compliance_status": {
                "disclaimers_count": len(self.compliance_checker.disclaimers_accepted)
            }
        }


# Funções utilitárias
def generate_user_id() -> str:
    """
    Gera ID único para o usuário baseado no sistema
    
    Returns:
        ID único do usuário
    """
    system_info = f"{os.name}_{os.environ.get('USERNAME', 'user')}_{os.environ.get('COMPUTERNAME', 'computer')}"
    return hashlib.sha256(system_info.encode()).hexdigest()[:16]


def create_demo_license(license_file: str = "license.key") -> bool:
    """
    Cria licença de demonstração
    
    Args:
        license_file: Arquivo para salvar licença
        
    Returns:
        True se criada com sucesso
    """
    try:
        license_manager = LicenseManager(license_file)
        return license_manager.install_license(
            license_key="DEMO-FRP-2025-BYPASS-PROFESSIONAL",
            user_name="Demo User",
            organization="Demo Organization"
        )
    except Exception as e:
        logger.error(f"Erro ao criar licença demo: {e}")
        return False


if __name__ == "__main__":
    # Teste básico do módulo
    print("=== FRP Bypass Professional - Security Test ===")
    
    # Cria licença demo
    print("Criando licença de demonstração...")
    if create_demo_license():
        print("✓ Licença demo criada")
    else:
        print("✗ Erro ao criar licença demo")
    
    # Inicializa gerenciador de segurança
    security_manager = SecurityManager()
    
    # Status de segurança
    status = security_manager.get_security_status()
    print(f"\nStatus de Segurança:")
    print(f"- Licença válida: {status['license_status']['valid']}")
    print(f"- Entradas de auditoria: {status['audit_statistics']['total_entries']}")
    
    # Teste de autorização (dispositivo simulado)
    from .device_detection import AndroidDevice, DeviceMode, Manufacturer
    
    test_device = AndroidDevice(
        vendor_id=0x04e8,
        product_id=0x6860,
        manufacturer=Manufacturer.SAMSUNG,
        model="Galaxy S20",
        serial="test123456",
        mode=DeviceMode.ADB,
        frp_locked=True,
        usb_debugging=True
    )
    
    user_id = generate_user_id()
    print(f"\nTestando autorização para usuário: {user_id[:8]}...")
    
    # Aceita termo primeiro
    security_manager.compliance_checker.accept_disclaimer(user_id, "frp_bypass")
    
    authorized, reason = security_manager.authorize_bypass(user_id, test_device)
    print(f"Autorização: {'✓ Aprovada' if authorized else '✗ Negada'}")
    print(f"Motivo: {reason}")
