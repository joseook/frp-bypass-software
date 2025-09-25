"""
Performance Cache System
========================

Sistema de cache inteligente para otimização de performance do FRP Bypass Professional.
Implementa cache em memória e persistente para operações custosas.

Classes:
- CacheEntry: Entrada individual do cache
- MemoryCache: Cache em memória com TTL
- PersistentCache: Cache persistente em disco
- DeviceCache: Cache específico para dispositivos
- CacheManager: Gerenciador central de cache
"""

import json
import time
import hashlib
import pickle
import threading
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import weakref
from loguru import logger


class CacheLevel(Enum):
    """Níveis de cache"""
    MEMORY_ONLY = "memory_only"
    PERSISTENT_ONLY = "persistent_only"
    BOTH = "both"


@dataclass
class CacheEntry:
    """Entrada do cache"""
    
    key: str
    value: Any
    timestamp: float
    ttl: int  # Time to live em segundos
    access_count: int = 0
    last_access: float = 0
    
    def __post_init__(self):
        if self.last_access == 0:
            self.last_access = self.timestamp
    
    @property
    def is_expired(self) -> bool:
        """Verifica se a entrada expirou"""
        if self.ttl <= 0:  # TTL 0 = nunca expira
            return False
        return time.time() - self.timestamp > self.ttl
    
    @property
    def age_seconds(self) -> int:
        """Idade da entrada em segundos"""
        return int(time.time() - self.timestamp)
    
    def access(self) -> Any:
        """Registra acesso e retorna valor"""
        self.access_count += 1
        self.last_access = time.time()
        return self.value
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário (para serialização)"""
        return {
            'key': self.key,
            'value': self.value,
            'timestamp': self.timestamp,
            'ttl': self.ttl,
            'access_count': self.access_count,
            'last_access': self.last_access
        }


class MemoryCache:
    """Cache em memória com TTL"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Inicializa cache em memória
        
        Args:
            max_size: Tamanho máximo do cache
            default_ttl: TTL padrão em segundos
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expires': 0
        }
        
        logger.debug(f"MemoryCache inicializado: max_size={max_size}, ttl={default_ttl}s")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtém valor do cache
        
        Args:
            key: Chave do cache
            
        Returns:
            Valor ou None se não encontrado/expirado
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats['misses'] += 1
                return None
            
            if entry.is_expired:
                del self._cache[key]
                self._stats['expires'] += 1
                self._stats['misses'] += 1
                logger.debug(f"Cache entry expired: {key}")
                return None
            
            self._stats['hits'] += 1
            return entry.access()
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Define valor no cache
        
        Args:
            key: Chave do cache
            value: Valor a armazenar
            ttl: TTL específico (usa default se None)
        """
        with self._lock:
            if ttl is None:
                ttl = self.default_ttl
            
            # Remove entrada antiga se existir
            if key in self._cache:
                del self._cache[key]
            
            # Verifica se precisa fazer eviction
            if len(self._cache) >= self.max_size:
                self._evict_lru()
            
            # Adiciona nova entrada
            entry = CacheEntry(
                key=key,
                value=value,
                timestamp=time.time(),
                ttl=ttl
            )
            
            self._cache[key] = entry
            logger.debug(f"Cache set: {key} (ttl={ttl}s)")
    
    def delete(self, key: str) -> bool:
        """
        Remove entrada do cache
        
        Args:
            key: Chave a remover
            
        Returns:
            True se removida, False se não existia
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache deleted: {key}")
                return True
            return False
    
    def clear(self) -> None:
        """Limpa todo o cache"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.debug(f"Cache cleared: {count} entries removed")
    
    def _evict_lru(self) -> None:
        """Remove entrada menos recentemente usada"""
        if not self._cache:
            return
        
        # Encontra entrada com menor last_access
        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].last_access)
        del self._cache[lru_key]
        self._stats['evictions'] += 1
        logger.debug(f"Cache evicted LRU: {lru_key}")
    
    def cleanup_expired(self) -> int:
        """
        Remove entradas expiradas
        
        Returns:
            Número de entradas removidas
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired
            ]
            
            for key in expired_keys:
                del self._cache[key]
                self._stats['expires'] += 1
            
            if expired_keys:
                logger.debug(f"Cache cleanup: {len(expired_keys)} expired entries removed")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas do cache
        
        Returns:
            Dicionário com estatísticas
        """
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': round(hit_rate, 2),
                'evictions': self._stats['evictions'],
                'expires': self._stats['expires'],
                'total_requests': total_requests
            }
    
    def get_entries_info(self) -> List[Dict[str, Any]]:
        """
        Obtém informações de todas as entradas
        
        Returns:
            Lista com informações das entradas
        """
        with self._lock:
            return [
                {
                    'key': key,
                    'age_seconds': entry.age_seconds,
                    'access_count': entry.access_count,
                    'ttl': entry.ttl,
                    'is_expired': entry.is_expired
                }
                for key, entry in self._cache.items()
            ]


class PersistentCache:
    """Cache persistente em disco"""
    
    def __init__(self, cache_dir: str = "cache", default_ttl: int = 86400):
        """
        Inicializa cache persistente
        
        Args:
            cache_dir: Diretório do cache
            default_ttl: TTL padrão em segundos (24h)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.default_ttl = default_ttl
        self._lock = threading.RLock()
        
        logger.debug(f"PersistentCache inicializado: dir={cache_dir}, ttl={default_ttl}s")
    
    def _get_cache_file(self, key: str) -> Path:
        """Obtém caminho do arquivo de cache para uma chave"""
        # Hash da chave para nome de arquivo seguro
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtém valor do cache persistente
        
        Args:
            key: Chave do cache
            
        Returns:
            Valor ou None se não encontrado/expirado
        """
        with self._lock:
            cache_file = self._get_cache_file(key)
            
            if not cache_file.exists():
                return None
            
            try:
                with open(cache_file, 'rb') as f:
                    entry_data = pickle.load(f)
                
                entry = CacheEntry(**entry_data)
                
                if entry.is_expired:
                    cache_file.unlink(missing_ok=True)
                    logger.debug(f"Persistent cache entry expired: {key}")
                    return None
                
                # Atualiza estatísticas de acesso
                entry.access()
                
                # Salva estatísticas atualizadas
                with open(cache_file, 'wb') as f:
                    pickle.dump(entry.to_dict(), f)
                
                return entry.value
                
            except Exception as e:
                logger.error(f"Erro ao ler cache persistente {key}: {e}")
                cache_file.unlink(missing_ok=True)
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Define valor no cache persistente
        
        Args:
            key: Chave do cache
            value: Valor a armazenar
            ttl: TTL específico
        """
        with self._lock:
            if ttl is None:
                ttl = self.default_ttl
            
            cache_file = self._get_cache_file(key)
            
            entry = CacheEntry(
                key=key,
                value=value,
                timestamp=time.time(),
                ttl=ttl
            )
            
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump(entry.to_dict(), f)
                
                logger.debug(f"Persistent cache set: {key}")
                
            except Exception as e:
                logger.error(f"Erro ao salvar cache persistente {key}: {e}")
    
    def delete(self, key: str) -> bool:
        """
        Remove entrada do cache persistente
        
        Args:
            key: Chave a remover
            
        Returns:
            True se removida, False se não existia
        """
        with self._lock:
            cache_file = self._get_cache_file(key)
            
            if cache_file.exists():
                cache_file.unlink()
                logger.debug(f"Persistent cache deleted: {key}")
                return True
            return False
    
    def clear(self) -> None:
        """Limpa todo o cache persistente"""
        with self._lock:
            count = 0
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()
                count += 1
            
            logger.debug(f"Persistent cache cleared: {count} files removed")
    
    def cleanup_expired(self) -> int:
        """
        Remove arquivos de cache expirados
        
        Returns:
            Número de arquivos removidos
        """
        with self._lock:
            removed_count = 0
            
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    with open(cache_file, 'rb') as f:
                        entry_data = pickle.load(f)
                    
                    entry = CacheEntry(**entry_data)
                    
                    if entry.is_expired:
                        cache_file.unlink()
                        removed_count += 1
                        
                except Exception:
                    # Remove arquivo corrompido
                    cache_file.unlink()
                    removed_count += 1
            
            if removed_count > 0:
                logger.debug(f"Persistent cache cleanup: {removed_count} files removed")
            
            return removed_count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas do cache persistente
        
        Returns:
            Dicionário com estatísticas
        """
        with self._lock:
            cache_files = list(self.cache_dir.glob("*.cache"))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                'files': len(cache_files),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'cache_dir': str(self.cache_dir)
            }


class DeviceCache:
    """Cache específico para informações de dispositivos"""
    
    def __init__(self, cache_manager: 'CacheManager'):
        """
        Inicializa cache de dispositivos
        
        Args:
            cache_manager: Gerenciador de cache principal
        """
        self.cache_manager = cache_manager
        self.device_info_ttl = 1800  # 30 minutos
        self.device_scan_ttl = 300   # 5 minutos
        
    def cache_device_info(self, device_id: str, device_info: Dict[str, Any]) -> None:
        """
        Armazena informações detalhadas do dispositivo
        
        Args:
            device_id: ID único do dispositivo
            device_info: Informações do dispositivo
        """
        key = f"device_info:{device_id}"
        self.cache_manager.set(key, device_info, ttl=self.device_info_ttl, level=CacheLevel.BOTH)
    
    def get_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações do dispositivo do cache
        
        Args:
            device_id: ID único do dispositivo
            
        Returns:
            Informações do dispositivo ou None
        """
        key = f"device_info:{device_id}"
        return self.cache_manager.get(key)
    
    def cache_scan_result(self, scan_hash: str, devices: List[Dict[str, Any]]) -> None:
        """
        Armazena resultado de scan de dispositivos
        
        Args:
            scan_hash: Hash único do scan
            devices: Lista de dispositivos encontrados
        """
        key = f"device_scan:{scan_hash}"
        self.cache_manager.set(key, devices, ttl=self.device_scan_ttl, level=CacheLevel.MEMORY_ONLY)
    
    def get_scan_result(self, scan_hash: str) -> Optional[List[Dict[str, Any]]]:
        """
        Obtém resultado de scan do cache
        
        Args:
            scan_hash: Hash único do scan
            
        Returns:
            Lista de dispositivos ou None
        """
        key = f"device_scan:{scan_hash}"
        return self.cache_manager.get(key)
    
    def cache_bypass_result(self, device_id: str, method: str, result: Dict[str, Any]) -> None:
        """
        Armazena resultado de bypass
        
        Args:
            device_id: ID do dispositivo
            method: Método utilizado
            result: Resultado do bypass
        """
        key = f"bypass_result:{device_id}:{method}"
        # Resultados de bypass são persistidos por mais tempo
        self.cache_manager.set(key, result, ttl=7200, level=CacheLevel.PERSISTENT_ONLY)  # 2 horas
    
    def get_bypass_result(self, device_id: str, method: str) -> Optional[Dict[str, Any]]:
        """
        Obtém resultado de bypass do cache
        
        Args:
            device_id: ID do dispositivo
            method: Método utilizado
            
        Returns:
            Resultado do bypass ou None
        """
        key = f"bypass_result:{device_id}:{method}"
        return self.cache_manager.get(key)


class CacheManager:
    """Gerenciador central de cache"""
    
    def __init__(self, cache_dir: str = "cache", memory_size: int = 1000):
        """
        Inicializa gerenciador de cache
        
        Args:
            cache_dir: Diretório para cache persistente
            memory_size: Tamanho máximo do cache em memória
        """
        self.memory_cache = MemoryCache(max_size=memory_size)
        self.persistent_cache = PersistentCache(cache_dir)
        self.device_cache = DeviceCache(self)
        
        # Cache de funções com decoradores
        self._function_cache: Dict[str, weakref.WeakKeyDictionary] = {}
        
        # Thread para limpeza automática
        self._cleanup_thread = None
        self._start_cleanup_thread()
        
        logger.info(f"CacheManager inicializado: memory_size={memory_size}, cache_dir={cache_dir}")
    
    def get(self, key: str, level: CacheLevel = CacheLevel.BOTH) -> Optional[Any]:
        """
        Obtém valor do cache
        
        Args:
            key: Chave do cache
            level: Nível de cache a consultar
            
        Returns:
            Valor ou None se não encontrado
        """
        if level in (CacheLevel.MEMORY_ONLY, CacheLevel.BOTH):
            value = self.memory_cache.get(key)
            if value is not None:
                return value
        
        if level in (CacheLevel.PERSISTENT_ONLY, CacheLevel.BOTH):
            value = self.persistent_cache.get(key)
            if value is not None:
                # Promove para cache em memória se encontrado no persistente
                if level == CacheLevel.BOTH:
                    self.memory_cache.set(key, value)
                return value
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, 
            level: CacheLevel = CacheLevel.BOTH) -> None:
        """
        Define valor no cache
        
        Args:
            key: Chave do cache
            value: Valor a armazenar
            ttl: TTL específico
            level: Nível de cache a usar
        """
        if level in (CacheLevel.MEMORY_ONLY, CacheLevel.BOTH):
            self.memory_cache.set(key, value, ttl)
        
        if level in (CacheLevel.PERSISTENT_ONLY, CacheLevel.BOTH):
            self.persistent_cache.set(key, value, ttl)
    
    def delete(self, key: str, level: CacheLevel = CacheLevel.BOTH) -> bool:
        """
        Remove entrada do cache
        
        Args:
            key: Chave a remover
            level: Nível de cache
            
        Returns:
            True se removida de pelo menos um nível
        """
        removed = False
        
        if level in (CacheLevel.MEMORY_ONLY, CacheLevel.BOTH):
            removed |= self.memory_cache.delete(key)
        
        if level in (CacheLevel.PERSISTENT_ONLY, CacheLevel.BOTH):
            removed |= self.persistent_cache.delete(key)
        
        return removed
    
    def clear(self, level: CacheLevel = CacheLevel.BOTH) -> None:
        """
        Limpa cache
        
        Args:
            level: Nível de cache a limpar
        """
        if level in (CacheLevel.MEMORY_ONLY, CacheLevel.BOTH):
            self.memory_cache.clear()
        
        if level in (CacheLevel.PERSISTENT_ONLY, CacheLevel.BOTH):
            self.persistent_cache.clear()
    
    def cleanup_expired(self) -> Dict[str, int]:
        """
        Remove entradas expiradas de todos os níveis
        
        Returns:
            Dicionário com contadores de limpeza
        """
        return {
            'memory': self.memory_cache.cleanup_expired(),
            'persistent': self.persistent_cache.cleanup_expired()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas de todos os caches
        
        Returns:
            Dicionário com estatísticas completas
        """
        return {
            'memory': self.memory_cache.get_stats(),
            'persistent': self.persistent_cache.get_stats(),
            'device_cache_keys': len([k for k in self.memory_cache._cache.keys() if k.startswith('device_')])
        }
    
    def cached_function(self, ttl: int = 3600, level: CacheLevel = CacheLevel.MEMORY_ONLY):
        """
        Decorador para cache de funções
        
        Args:
            ttl: TTL do cache
            level: Nível de cache
            
        Returns:
            Decorador
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                # Gera chave única para a função e argumentos
                key_data = {
                    'function': func.__name__,
                    'args': args,
                    'kwargs': kwargs
                }
                key = f"func:{hashlib.md5(json.dumps(key_data, sort_keys=True, default=str).encode()).hexdigest()}"
                
                # Tenta obter do cache
                cached_result = self.get(key, level)
                if cached_result is not None:
                    logger.debug(f"Function cache hit: {func.__name__}")
                    return cached_result
                
                # Executa função e armazena resultado
                result = func(*args, **kwargs)
                self.set(key, result, ttl, level)
                logger.debug(f"Function cache miss: {func.__name__}")
                
                return result
            
            wrapper.__wrapped__ = func
            return wrapper
        
        return decorator
    
    def _start_cleanup_thread(self) -> None:
        """Inicia thread de limpeza automática"""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(300)  # Cleanup a cada 5 minutos
                    cleaned = self.cleanup_expired()
                    if cleaned['memory'] > 0 or cleaned['persistent'] > 0:
                        logger.debug(f"Auto cleanup: memory={cleaned['memory']}, persistent={cleaned['persistent']}")
                except Exception as e:
                    logger.error(f"Erro no cleanup automático: {e}")
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()


# Instância global do cache manager
_global_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """
    Obtém instância global do cache manager
    
    Returns:
        Instância do CacheManager
    """
    global _global_cache_manager
    
    if _global_cache_manager is None:
        _global_cache_manager = CacheManager()
    
    return _global_cache_manager


# Decoradores de conveniência
def cached(ttl: int = 3600, level: CacheLevel = CacheLevel.MEMORY_ONLY):
    """
    Decorador de conveniência para cache de funções
    
    Args:
        ttl: TTL do cache
        level: Nível de cache
        
    Returns:
        Decorador
    """
    return get_cache_manager().cached_function(ttl, level)


if __name__ == "__main__":
    # Teste básico do sistema de cache
    print("=== FRP Bypass Professional - Cache System Test ===")
    
    cache_manager = CacheManager()
    
    # Teste cache básico
    print("\n1. Teste de Cache Básico:")
    cache_manager.set("test_key", "test_value", ttl=60)
    value = cache_manager.get("test_key")
    print(f"   Valor armazenado/recuperado: {value}")
    
    # Teste cache de dispositivos
    print("\n2. Teste de Cache de Dispositivos:")
    device_info = {
        'model': 'Galaxy S20',
        'android_version': '11',
        'frp_locked': True
    }
    cache_manager.device_cache.cache_device_info("test_device", device_info)
    cached_info = cache_manager.device_cache.get_device_info("test_device")
    print(f"   Device info cached: {cached_info}")
    
    # Teste decorador de função
    print("\n3. Teste de Decorador de Função:")
    
    @cached(ttl=60)
    def expensive_function(x, y):
        print(f"   Executando função custosa com {x}, {y}")
        time.sleep(0.1)  # Simula operação custosa
        return x + y
    
    # Primeira chamada (cache miss)
    result1 = expensive_function(1, 2)
    print(f"   Resultado 1: {result1}")
    
    # Segunda chamada (cache hit)
    result2 = expensive_function(1, 2)
    print(f"   Resultado 2: {result2}")
    
    # Estatísticas
    print("\n4. Estatísticas do Cache:")
    stats = cache_manager.get_stats()
    print(f"   Memory cache: {stats['memory']['size']} entradas, {stats['memory']['hit_rate']}% hit rate")
    print(f"   Persistent cache: {stats['persistent']['files']} arquivos, {stats['persistent']['total_size_mb']} MB")
    
    print("\n✅ Teste do sistema de cache concluído!")
