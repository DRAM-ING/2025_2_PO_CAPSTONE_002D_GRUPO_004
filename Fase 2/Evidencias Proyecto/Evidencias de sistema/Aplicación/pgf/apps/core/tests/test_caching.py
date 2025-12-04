# apps/core/tests/test_caching.py
"""
Tests para utilidades de caching.
"""

import pytest
from django.core.cache import cache
from apps.core.caching import cache_result, get_or_set_cache


class TestCaching:
    """Tests para funciones de caching"""
    
    @pytest.mark.unit
    def test_cache_result_decorator(self):
        """Test que el decorador cache_result funciona correctamente"""
        call_count = [0]  # Usar lista para poder modificar desde función interna
        
        @cache_result('test_cache', timeout=60)
        def test_function(arg1, arg2):
            call_count[0] += 1
            return arg1 + arg2
        
        # Primera llamada: debe ejecutar la función
        result1 = test_function(1, 2)
        assert result1 == 3
        assert call_count[0] == 1
        
        # Segunda llamada con mismos argumentos: debe usar cache
        result2 = test_function(1, 2)
        assert result2 == 3
        assert call_count[0] == 1  # No debe incrementar
        
        # Tercera llamada con diferentes argumentos: debe ejecutar
        result3 = test_function(3, 4)
        assert result3 == 7
        assert call_count[0] == 2
    
    @pytest.mark.unit
    def test_get_or_set_cache(self):
        """Test función get_or_set_cache"""
        cache_key = "test_get_or_set"
        call_count = [0]
        
        def calculate_value():
            call_count[0] += 1
            return "calculated_value"
        
        # Primera llamada: debe calcular
        result1 = get_or_set_cache(cache_key, calculate_value, timeout=60)
        assert result1 == "calculated_value"
        assert call_count[0] == 1
        
        # Segunda llamada: debe usar cache
        result2 = get_or_set_cache(cache_key, calculate_value, timeout=60)
        assert result2 == "calculated_value"
        assert call_count[0] == 1  # No debe incrementar
        
        # Limpiar cache
        cache.delete(cache_key)
        
        # Tercera llamada: debe calcular de nuevo
        result3 = get_or_set_cache(cache_key, calculate_value, timeout=60)
        assert result3 == "calculated_value"
        assert call_count[0] == 2

