# apps/core/tests/test_validators.py
"""
Tests para los validadores reutilizables en apps/core/validators.py
"""

import pytest
from datetime import datetime, date
from apps.core.validators import (
    validar_rut_chileno,
    validar_formato_patente,
    validar_formato_correo,
    validar_ano,
    validar_rol,
    validar_rango_fechas
)


class TestValidarRutChileno:
    """Tests para validar_rut_chileno"""
    
    @pytest.mark.validator
    def test_rut_valido_con_guion(self):
        """Test RUT válido con guión"""
        # RUT válido: 12345678-5 (DV calculado correctamente)
        es_valido, resultado = validar_rut_chileno("12345678-5")
        assert es_valido is True
        assert resultado == "12345678-5"
    
    @pytest.mark.validator
    def test_rut_valido_sin_guion(self):
        """Test RUT válido sin guión (se agrega automáticamente)"""
        # RUT válido: 12345678-5
        es_valido, resultado = validar_rut_chileno("123456785")
        assert es_valido is True
        assert resultado == "12345678-5"
    
    @pytest.mark.validator
    def test_rut_valido_con_puntos(self):
        """Test RUT válido con puntos (se limpian)"""
        # RUT válido: 12345678-5
        es_valido, resultado = validar_rut_chileno("12.345.678-5")
        assert es_valido is True
        assert resultado == "12345678-5"
    
    @pytest.mark.validator
    def test_rut_valido_con_k(self):
        """Test RUT válido con K como dígito verificador"""
        # RUT válido con K: 10000013-K (DV calculado correctamente)
        es_valido, resultado = validar_rut_chileno("10000013-K")
        assert es_valido is True
        assert resultado == "10000013-K"
    
    @pytest.mark.validator
    def test_rut_invalido_digito_verificador(self):
        """Test RUT con dígito verificador incorrecto"""
        es_valido, resultado = validar_rut_chileno("12345678-0")
        assert es_valido is False
        assert "dígito verificador" in resultado.lower()
    
    @pytest.mark.validator
    def test_rut_vacio(self):
        """Test RUT vacío"""
        es_valido, resultado = validar_rut_chileno("")
        assert es_valido is False
        assert "vacío" in resultado.lower()
    
    @pytest.mark.validator
    def test_rut_muy_corto(self):
        """Test RUT con menos de 8 caracteres"""
        es_valido, resultado = validar_rut_chileno("12345")
        assert es_valido is False
        assert "8 y 9 caracteres" in resultado
    
    @pytest.mark.validator
    def test_rut_muy_largo(self):
        """Test RUT con más de 9 caracteres"""
        es_valido, resultado = validar_rut_chileno("1234567890")
        assert es_valido is False
        assert "8 y 9 caracteres" in resultado


class TestValidarFormatoPatente:
    """Tests para validar_formato_patente"""
    
    @pytest.mark.validator
    def test_patente_valida_aa1234(self):
        """Test patente válida formato AA1234"""
        es_valido, resultado = validar_formato_patente("AA1234")
        assert es_valido is True
        assert resultado == "AA1234"
    
    @pytest.mark.validator
    def test_patente_valida_aaaa12(self):
        """Test patente válida formato AAAA12"""
        es_valido, resultado = validar_formato_patente("AAAA12")
        assert es_valido is True
        assert resultado == "AAAA12"
    
    @pytest.mark.validator
    def test_patente_valida_aaab12(self):
        """Test patente válida formato AAAB12"""
        es_valido, resultado = validar_formato_patente("AAAB12")
        assert es_valido is True
        assert resultado == "AAAB12"
    
    @pytest.mark.validator
    def test_patente_valida_con_espacios(self):
        """Test patente válida con espacios (se limpian)"""
        es_valido, resultado = validar_formato_patente("AA 1234")
        assert es_valido is True
        assert resultado == "AA1234"
    
    @pytest.mark.validator
    def test_patente_valida_minusculas(self):
        """Test patente válida en minúsculas (se convierten)"""
        es_valido, resultado = validar_formato_patente("aa1234")
        assert es_valido is True
        assert resultado == "AA1234"
    
    @pytest.mark.validator
    def test_patente_invalida_formato(self):
        """Test patente con formato inválido"""
        es_valido, resultado = validar_formato_patente("1234AA")
        assert es_valido is False
        assert "inválido" in resultado.lower()
    
    @pytest.mark.validator
    def test_patente_vacia(self):
        """Test patente vacía"""
        es_valido, resultado = validar_formato_patente("")
        assert es_valido is False
        assert "vacía" in resultado.lower()
    
    @pytest.mark.validator
    def test_patente_muy_corta(self):
        """Test patente con menos de 6 caracteres"""
        es_valido, resultado = validar_formato_patente("AA123")
        assert es_valido is False
        assert "6 caracteres" in resultado
    
    @pytest.mark.validator
    def test_patente_muy_larga(self):
        """Test patente con más de 6 caracteres"""
        es_valido, resultado = validar_formato_patente("AA12345")
        assert es_valido is False
        assert "6 caracteres" in resultado


class TestValidarFormatoCorreo:
    """Tests para validar_formato_correo"""
    
    @pytest.mark.validator
    def test_correo_valido(self):
        """Test correo válido"""
        es_valido, resultado = validar_formato_correo("test@example.com")
        assert es_valido is True
        assert resultado == "test@example.com"
    
    @pytest.mark.validator
    def test_correo_valido_mayusculas(self):
        """Test correo válido en mayúsculas (se convierte a minúsculas)"""
        es_valido, resultado = validar_formato_correo("TEST@EXAMPLE.COM")
        assert es_valido is True
        assert resultado == "test@example.com"
    
    @pytest.mark.validator
    def test_correo_valido_con_puntos(self):
        """Test correo válido con puntos"""
        es_valido, resultado = validar_formato_correo("test.user@example.com")
        assert es_valido is True
        assert resultado == "test.user@example.com"
    
    @pytest.mark.validator
    def test_correo_invalido_sin_arroba(self):
        """Test correo sin @"""
        es_valido, resultado = validar_formato_correo("testexample.com")
        assert es_valido is False
        assert "inválido" in resultado.lower()
    
    @pytest.mark.validator
    def test_correo_invalido_sin_dominio(self):
        """Test correo sin dominio"""
        es_valido, resultado = validar_formato_correo("test@")
        assert es_valido is False
        assert "inválido" in resultado.lower()
    
    @pytest.mark.validator
    def test_correo_vacio(self):
        """Test correo vacío"""
        es_valido, resultado = validar_formato_correo("")
        assert es_valido is False
        assert "vacío" in resultado.lower()


class TestValidarAno:
    """Tests para validar_ano"""
    
    @pytest.mark.validator
    def test_ano_valido_2000(self):
        """Test año válido 2000"""
        es_valido, resultado = validar_ano(2000)
        assert es_valido is True
        assert resultado is None
    
    @pytest.mark.validator
    def test_ano_valido_actual(self):
        """Test año válido (año actual)"""
        ano_actual = datetime.now().year
        es_valido, resultado = validar_ano(ano_actual)
        assert es_valido is True
        assert resultado is None
    
    @pytest.mark.validator
    def test_ano_invalido_menor_2000(self):
        """Test año menor a 2000"""
        es_valido, resultado = validar_ano(1999)
        assert es_valido is False
        assert "2000" in resultado
    
    @pytest.mark.validator
    def test_ano_invalido_futuro(self):
        """Test año mayor al actual"""
        ano_futuro = datetime.now().year + 1
        es_valido, resultado = validar_ano(ano_futuro)
        assert es_valido is False
        assert "mayor al año actual" in resultado.lower()


class TestValidarRol:
    """Tests para validar_rol"""
    
    @pytest.mark.validator
    def test_rol_valido_admin(self):
        """Test rol válido ADMIN"""
        es_valido, resultado = validar_rol("ADMIN")
        assert es_valido is True
        assert resultado is None
    
    @pytest.mark.validator
    def test_rol_valido_supervisor(self):
        """Test rol válido SUPERVISOR"""
        es_valido, resultado = validar_rol("SUPERVISOR")
        assert es_valido is True
        assert resultado is None
    
    @pytest.mark.validator
    def test_rol_valido_mecanico(self):
        """Test rol válido MECANICO"""
        es_valido, resultado = validar_rol("MECANICO")
        assert es_valido is True
        assert resultado is None
    
    @pytest.mark.validator
    def test_rol_invalido(self):
        """Test rol inválido"""
        es_valido, resultado = validar_rol("ROL_INEXISTENTE")
        assert es_valido is False
        assert "no es válido" in resultado.lower()
        assert "Roles permitidos" in resultado


class TestValidarRangoFechas:
    """Tests para validar_rango_fechas"""
    
    @pytest.mark.validator
    def test_rango_valido(self):
        """Test rango de fechas válido"""
        fecha_inicio = date(2024, 1, 1)
        fecha_fin = date(2024, 12, 31)
        es_valido, resultado = validar_rango_fechas(fecha_inicio, fecha_fin)
        assert es_valido is True
        assert resultado is None
    
    @pytest.mark.validator
    def test_rango_valido_mismo_dia(self):
        """Test rango válido (mismo día)"""
        fecha = date(2024, 1, 1)
        es_valido, resultado = validar_rango_fechas(fecha, fecha)
        assert es_valido is True
        assert resultado is None
    
    @pytest.mark.validator
    def test_rango_invalido_fin_antes_inicio(self):
        """Test rango inválido (fin antes de inicio)"""
        fecha_inicio = date(2024, 12, 31)
        fecha_fin = date(2024, 1, 1)
        es_valido, resultado = validar_rango_fechas(fecha_inicio, fecha_fin)
        assert es_valido is False
        assert "mayor que la fecha de fin" in resultado.lower()
    
    @pytest.mark.validator
    def test_rango_con_none(self):
        """Test rango con None (válido, no valida)"""
        es_valido, resultado = validar_rango_fechas(None, None)
        assert es_valido is True
        assert resultado is None

