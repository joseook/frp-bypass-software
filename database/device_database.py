"""
Device Database Manager
======================

Sistema de gerenciamento da base de dados de dispositivos Android e exploits FRP.
Fornece acesso estruturado às informações de dispositivos e métodos de bypass.

Classes:
- DeviceProfile: Representa um perfil de dispositivo
- ExploitMethod: Representa um método de exploit
- DeviceDatabase: Gerenciador principal da base de dados
- ExploitManager: Gerenciador de exploits e métodos
"""

import json
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from loguru import logger
import time


class DifficultyLevel(Enum):
    """Níveis de dificuldade para bypass FRP"""
    VERY_EASY = "very_easy"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"
    EXTREMELY_HARD = "extremely_hard"


class RiskLevel(Enum):
    """Níveis de risco para métodos de bypass"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class DeviceProfile:
    """Perfil de um dispositivo Android"""
    
    name: str
    codename: str
    manufacturer: str
    series: str
    android_versions: List[str]
    api_levels: List[int]
    chipset: str
    supported_methods: List[str]
    frp_bypass_difficulty: str
    success_rate: int
    
    # Campos opcionais
    vendor_id: Optional[str] = None
    product_ids: Optional[List[str]] = None
    security_patch_level: Optional[str] = None
    bootloader_version: Optional[str] = None
    
    @property
    def difficulty_enum(self) -> DifficultyLevel:
        """Retorna enum de dificuldade"""
        try:
            return DifficultyLevel(self.frp_bypass_difficulty)
        except ValueError:
            return DifficultyLevel.MEDIUM
    
    @property
    def device_id(self) -> str:
        """ID único do dispositivo"""
        return f"{self.manufacturer}_{self.codename}"
    
    def supports_method(self, method: str) -> bool:
        """Verifica se o dispositivo suporta um método específico"""
        return method in self.supported_methods
    
    def supports_android_version(self, version: str) -> bool:
        """Verifica se o dispositivo suporta uma versão do Android"""
        return version in self.android_versions
    
    def get_best_methods(self, limit: int = 3) -> List[str]:
        """Retorna os melhores métodos baseado na taxa de sucesso"""
        # Por enquanto retorna os primeiros métodos
        # Em versão futura, pode ser baseado em estatísticas
        return self.supported_methods[:limit]


@dataclass
class ExploitMethod:
    """Método de exploit/bypass"""
    
    name: str
    type: str
    description: str
    requirements: List[str]
    steps: List[str]
    compatibility: List[str]
    risk_level: str
    
    # Campos opcionais
    success_rate: Optional[int] = None
    execution_time: Optional[int] = None  # em minutos
    tools_required: Optional[List[str]] = None
    cve_references: Optional[List[str]] = None
    
    @property
    def risk_enum(self) -> RiskLevel:
        """Retorna enum de risco"""
        try:
            return RiskLevel(self.risk_level)
        except ValueError:
            return RiskLevel.MEDIUM
    
    def is_compatible_with(self, device_series: str) -> bool:
        """Verifica compatibilidade com série de dispositivos"""
        return device_series in self.compatibility or "all_series" in self.compatibility
    
    def get_estimated_time(self) -> str:
        """Retorna tempo estimado de execução"""
        if self.execution_time:
            if self.execution_time < 60:
                return f"{self.execution_time} minutos"
            else:
                hours = self.execution_time // 60
                minutes = self.execution_time % 60
                return f"{hours}h {minutes}m"
        return "Tempo indeterminado"


class DeviceDatabase:
    """Gerenciador da base de dados de dispositivos"""
    
    def __init__(self, database_path: str = None):
        """
        Inicializa a base de dados
        
        Args:
            database_path: Caminho para o arquivo JSON da base de dados
        """
        if database_path is None:
            database_path = os.path.join(os.path.dirname(__file__), "device_profiles.json")
        
        self.database_path = Path(database_path)
        self.data: Dict[str, Any] = {}
        self.devices: Dict[str, DeviceProfile] = {}
        self.last_loaded: float = 0
        
        self.load_database()
        logger.info(f"DeviceDatabase inicializada com {len(self.devices)} dispositivos")
    
    def load_database(self) -> None:
        """Carrega a base de dados do arquivo JSON"""
        try:
            if not self.database_path.exists():
                logger.error(f"Arquivo de base de dados não encontrado: {self.database_path}")
                self.data = {}
                return
            
            with open(self.database_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            self._parse_devices()
            self.last_loaded = time.time()
            
            logger.info(f"Base de dados carregada: versão {self.data.get('version', 'unknown')}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON: {e}")
            self.data = {}
        except Exception as e:
            logger.error(f"Erro ao carregar base de dados: {e}")
            self.data = {}
    
    def _parse_devices(self) -> None:
        """Converte dados JSON em objetos DeviceProfile"""
        self.devices = {}
        
        manufacturers = self.data.get('manufacturers', {})
        
        for manufacturer, manufacturer_data in manufacturers.items():
            vendor_id = manufacturer_data.get('vendor_id')
            
            for series_name, series_data in manufacturer_data.get('series', {}).items():
                for model_data in series_data.get('models', []):
                    device = DeviceProfile(
                        name=model_data['name'],
                        codename=model_data['codename'],
                        manufacturer=manufacturer,
                        series=series_name,
                        android_versions=model_data['android_versions'],
                        api_levels=model_data['api_levels'],
                        chipset=model_data['chipset'],
                        supported_methods=model_data['supported_methods'],
                        frp_bypass_difficulty=model_data['frp_bypass_difficulty'],
                        success_rate=model_data['success_rate'],
                        vendor_id=vendor_id
                    )
                    
                    self.devices[device.device_id] = device
    
    def find_device_by_name(self, name: str) -> Optional[DeviceProfile]:
        """
        Busca dispositivo pelo nome
        
        Args:
            name: Nome do dispositivo
            
        Returns:
            DeviceProfile se encontrado
        """
        name_lower = name.lower()
        for device in self.devices.values():
            if name_lower in device.name.lower() or name_lower in device.codename.lower():
                return device
        return None
    
    def find_devices_by_manufacturer(self, manufacturer: str) -> List[DeviceProfile]:
        """
        Busca dispositivos por fabricante
        
        Args:
            manufacturer: Nome do fabricante
            
        Returns:
            Lista de dispositivos do fabricante
        """
        manufacturer_lower = manufacturer.lower()
        return [
            device for device in self.devices.values()
            if device.manufacturer.lower() == manufacturer_lower
        ]
    
    def find_devices_by_android_version(self, version: str) -> List[DeviceProfile]:
        """
        Busca dispositivos por versão do Android
        
        Args:
            version: Versão do Android (ex: "11", "12")
            
        Returns:
            Lista de dispositivos que suportam a versão
        """
        return [
            device for device in self.devices.values()
            if device.supports_android_version(version)
        ]
    
    def find_devices_by_method(self, method: str) -> List[DeviceProfile]:
        """
        Busca dispositivos que suportam um método específico
        
        Args:
            method: Nome do método de bypass
            
        Returns:
            Lista de dispositivos que suportam o método
        """
        return [
            device for device in self.devices.values()
            if device.supports_method(method)
        ]
    
    def get_device_by_id(self, device_id: str) -> Optional[DeviceProfile]:
        """
        Obtém dispositivo por ID
        
        Args:
            device_id: ID único do dispositivo
            
        Returns:
            DeviceProfile se encontrado
        """
        return self.devices.get(device_id)
    
    def get_all_manufacturers(self) -> List[str]:
        """
        Retorna lista de todos os fabricantes
        
        Returns:
            Lista de nomes de fabricantes
        """
        return list(set(device.manufacturer for device in self.devices.values()))
    
    def get_all_methods(self) -> List[str]:
        """
        Retorna lista de todos os métodos de bypass
        
        Returns:
            Lista de métodos únicos
        """
        methods = set()
        for device in self.devices.values():
            methods.update(device.supported_methods)
        return list(methods)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas da base de dados
        
        Returns:
            Dicionário com estatísticas
        """
        total_devices = len(self.devices)
        manufacturers = self.get_all_manufacturers()
        methods = self.get_all_methods()
        
        # Estatísticas por dificuldade
        difficulty_stats = {}
        for difficulty in DifficultyLevel:
            count = sum(1 for d in self.devices.values() if d.difficulty_enum == difficulty)
            difficulty_stats[difficulty.value] = count
        
        # Taxa de sucesso média
        avg_success_rate = sum(d.success_rate for d in self.devices.values()) / total_devices if total_devices > 0 else 0
        
        return {
            'total_devices': total_devices,
            'manufacturers': len(manufacturers),
            'manufacturer_list': manufacturers,
            'total_methods': len(methods),
            'method_list': methods,
            'difficulty_distribution': difficulty_stats,
            'average_success_rate': round(avg_success_rate, 2),
            'database_version': self.data.get('version', 'unknown'),
            'last_updated': self.data.get('last_updated', 'unknown'),
            'last_loaded': time.ctime(self.last_loaded)
        }
    
    def search_devices(self, query: str, limit: int = 10) -> List[DeviceProfile]:
        """
        Busca dispositivos por texto livre
        
        Args:
            query: Texto de busca
            limit: Limite de resultados
            
        Returns:
            Lista de dispositivos encontrados
        """
        query_lower = query.lower()
        results = []
        
        for device in self.devices.values():
            # Busca em nome, codename, chipset
            searchable_text = f"{device.name} {device.codename} {device.chipset}".lower()
            
            if query_lower in searchable_text:
                results.append(device)
                
                if len(results) >= limit:
                    break
        
        # Ordena por relevância (nome primeiro, depois codename)
        results.sort(key=lambda d: (
            query_lower not in d.name.lower(),
            query_lower not in d.codename.lower(),
            d.name
        ))
        
        return results
    
    def reload_database(self) -> bool:
        """
        Recarrega a base de dados
        
        Returns:
            True se recarregado com sucesso
        """
        try:
            old_count = len(self.devices)
            self.load_database()
            new_count = len(self.devices)
            
            logger.info(f"Base de dados recarregada: {old_count} -> {new_count} dispositivos")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao recarregar base de dados: {e}")
            return False


class ExploitManager:
    """Gerenciador de exploits e métodos de bypass"""
    
    def __init__(self, database: DeviceDatabase):
        """
        Inicializa o gerenciador de exploits
        
        Args:
            database: Instância da DeviceDatabase
        """
        self.database = database
        self.exploits: Dict[str, ExploitMethod] = {}
        self._load_exploits()
        
        logger.info(f"ExploitManager inicializado com {len(self.exploits)} exploits")
    
    def _load_exploits(self) -> None:
        """Carrega exploits da base de dados"""
        self.exploits = {}
        
        manufacturers = self.database.data.get('manufacturers', {})
        
        for manufacturer, manufacturer_data in manufacturers.items():
            common_exploits = manufacturer_data.get('common_exploits', [])
            
            for exploit_data in common_exploits:
                exploit = ExploitMethod(
                    name=exploit_data['name'],
                    type=exploit_data['type'],
                    description=exploit_data['description'],
                    requirements=exploit_data['requirements'],
                    steps=exploit_data['steps'],
                    compatibility=exploit_data['compatibility'],
                    risk_level=exploit_data['risk_level']
                )
                
                self.exploits[f"{manufacturer}_{exploit.type}"] = exploit
        
        # Carrega categorias de exploits globais
        exploit_categories = self.database.data.get('exploit_categories', {})
        for category, category_data in exploit_categories.items():
            if category not in [e.type for e in self.exploits.values()]:
                exploit = ExploitMethod(
                    name=category_data['name'],
                    type=category,
                    description=category_data['description'],
                    requirements=category_data['requirements'],
                    steps=[],  # Será preenchido por métodos específicos
                    compatibility=['all_series'],
                    risk_level=category_data['risk_level']
                )
                
                self.exploits[f"global_{category}"] = exploit
    
    def get_exploits_for_device(self, device: DeviceProfile) -> List[ExploitMethod]:
        """
        Obtém exploits compatíveis com um dispositivo
        
        Args:
            device: Dispositivo para buscar exploits
            
        Returns:
            Lista de exploits compatíveis
        """
        compatible_exploits = []
        
        for exploit in self.exploits.values():
            # Verifica compatibilidade por série
            if exploit.is_compatible_with(device.series):
                compatible_exploits.append(exploit)
            # Verifica compatibilidade por método suportado
            elif exploit.type in device.supported_methods:
                compatible_exploits.append(exploit)
        
        # Remove duplicatas e ordena por risco (menor risco primeiro)
        unique_exploits = list({e.name: e for e in compatible_exploits}.values())
        unique_exploits.sort(key=lambda e: e.risk_enum.value)
        
        return unique_exploits
    
    def get_exploit_by_type(self, exploit_type: str) -> Optional[ExploitMethod]:
        """
        Busca exploit por tipo
        
        Args:
            exploit_type: Tipo do exploit
            
        Returns:
            ExploitMethod se encontrado
        """
        for exploit in self.exploits.values():
            if exploit.type == exploit_type:
                return exploit
        return None
    
    def get_exploits_by_risk_level(self, risk_level: RiskLevel) -> List[ExploitMethod]:
        """
        Busca exploits por nível de risco
        
        Args:
            risk_level: Nível de risco
            
        Returns:
            Lista de exploits com o nível de risco especificado
        """
        return [
            exploit for exploit in self.exploits.values()
            if exploit.risk_enum == risk_level
        ]
    
    def get_recommended_exploits(self, device: DeviceProfile, max_risk: RiskLevel = RiskLevel.MEDIUM) -> List[ExploitMethod]:
        """
        Obtém exploits recomendados para um dispositivo
        
        Args:
            device: Dispositivo alvo
            max_risk: Nível máximo de risco aceitável
            
        Returns:
            Lista de exploits recomendados ordenados por segurança
        """
        compatible_exploits = self.get_exploits_for_device(device)
        
        # Filtra por nível de risco máximo
        safe_exploits = [
            exploit for exploit in compatible_exploits
            if exploit.risk_enum.value <= max_risk.value
        ]
        
        # Ordena por risco (menor primeiro) e depois por nome
        safe_exploits.sort(key=lambda e: (e.risk_enum.value, e.name))
        
        return safe_exploits
    
    def get_exploit_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas dos exploits
        
        Returns:
            Dicionário com estatísticas
        """
        total_exploits = len(self.exploits)
        
        # Distribuição por risco
        risk_distribution = {}
        for risk in RiskLevel:
            count = sum(1 for e in self.exploits.values() if e.risk_enum == risk)
            risk_distribution[risk.value] = count
        
        # Tipos únicos
        unique_types = list(set(e.type for e in self.exploits.values()))
        
        return {
            'total_exploits': total_exploits,
            'unique_types': len(unique_types),
            'type_list': unique_types,
            'risk_distribution': risk_distribution
        }


# Funções utilitárias
def get_android_version_info(version: str, database: DeviceDatabase) -> Optional[Dict[str, Any]]:
    """
    Obtém informações sobre uma versão do Android
    
    Args:
        version: Versão do Android
        database: Instância da DeviceDatabase
        
    Returns:
        Informações da versão ou None
    """
    version_info = database.data.get('android_version_compatibility', {}).get(version)
    return version_info


def check_security_patch_impact(patch_date: str, database: DeviceDatabase) -> Optional[str]:
    """
    Verifica impacto de um patch de segurança
    
    Args:
        patch_date: Data do patch (YYYY-MM-DD)
        database: Instância da DeviceDatabase
        
    Returns:
        Descrição do impacto ou None
    """
    patch_impact = database.data.get('security_patches', {}).get('patch_impact', {})
    return patch_impact.get(patch_date)


if __name__ == "__main__":
    # Teste básico do módulo
    print("=== FRP Bypass Professional - Database Test ===")
    
    # Inicializa base de dados
    db = DeviceDatabase()
    exploit_manager = ExploitManager(db)
    
    # Estatísticas
    stats = db.get_statistics()
    print(f"\nEstatísticas da Base de Dados:")
    print(f"- Dispositivos: {stats['total_devices']}")
    print(f"- Fabricantes: {stats['manufacturers']}")
    print(f"- Métodos: {stats['total_methods']}")
    print(f"- Taxa de sucesso média: {stats['average_success_rate']}%")
    
    # Teste de busca
    samsung_devices = db.find_devices_by_manufacturer("samsung")
    print(f"\nDispositivos Samsung: {len(samsung_devices)}")
    
    if samsung_devices:
        device = samsung_devices[0]
        print(f"- Exemplo: {device.name}")
        print(f"  Dificuldade: {device.frp_bypass_difficulty}")
        print(f"  Taxa de sucesso: {device.success_rate}%")
        
        # Exploits compatíveis
        exploits = exploit_manager.get_exploits_for_device(device)
        print(f"  Exploits compatíveis: {len(exploits)}")
        for exploit in exploits[:3]:
            print(f"    - {exploit.name} (risco: {exploit.risk_level})")
    
    # Estatísticas de exploits
    exploit_stats = exploit_manager.get_exploit_statistics()
    print(f"\nEstatísticas de Exploits:")
    print(f"- Total: {exploit_stats['total_exploits']}")
    print(f"- Tipos únicos: {exploit_stats['unique_types']}")
