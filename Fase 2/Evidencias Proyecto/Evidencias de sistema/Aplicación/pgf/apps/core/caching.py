# apps/core/caching.py
"""
Utilidades para caching de consultas frecuentes.
"""

from django.core.cache import cache
from django.conf import settings
from functools import wraps
import hashlib
import json


def cache_result(key_prefix: str, timeout: int = 300):
    """
    Decorador para cachear resultados de funciones.
    
    Args:
        key_prefix: Prefijo para la clave de cache
        timeout: Tiempo de expiración en segundos (default: 5 minutos)
    
    Uso:
        @cache_result('dashboard_kpis', timeout=120)
        def get_dashboard_data(user_id):
            # ... código que genera datos ...
            return data
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave única basada en argumentos
            cache_key = f"{key_prefix}:{func.__name__}"
            
            # Agregar argumentos a la clave si existen
            if args or kwargs:
                key_data = json.dumps({
                    'args': str(args),
                    'kwargs': sorted(kwargs.items())
                }, sort_keys=True)
                key_hash = hashlib.md5(key_data.encode()).hexdigest()
                cache_key = f"{cache_key}:{key_hash}"
            
            # Intentar obtener del cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Ejecutar función y cachear resultado
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        
        return wrapper
    return decorator


def invalidate_cache(key_prefix: str):
    """
    Invalida todas las claves de cache que empiezan con el prefijo.
    
    Args:
        key_prefix: Prefijo de las claves a invalidar
    
    Uso:
        invalidate_cache('dashboard_kpis')
    """
    # Nota: Django cache no tiene método directo para invalidar por patrón
    # En producción, usar Redis con keys() o implementar un sistema de versionado
    # Por ahora, esta función es un placeholder para documentar la intención
    pass


def get_or_set_cache(key: str, callable_func, timeout: int = 300):
    """
    Obtiene un valor del cache o lo calcula y guarda si no existe.
    
    Args:
        key: Clave del cache
        callable_func: Función que calcula el valor si no está en cache
        timeout: Tiempo de expiración en segundos
    
    Returns:
        Valor del cache o resultado de callable_func
    """
    result = cache.get(key)
    if result is None:
        result = callable_func()
        cache.set(key, result, timeout)
    return result

