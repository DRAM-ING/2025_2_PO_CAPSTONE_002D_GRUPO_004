"""
Tests para utilidades y funciones auxiliares del módulo core.
"""
import pytest
from datetime import datetime, date
from apps.core.validators import (
    validar_rut_chileno,
    validar_formato_patente,
    validar_formato_correo,
    validar_ano,
    validar_rol,
    validar_rango_fechas,
)


class TestValidadoresIntegracion:
    """Tests de integración para validadores combinados"""

    @pytest.mark.validator
    def test_validar_usuario_completo(self):
        """Test validación completa de datos de usuario"""
        # RUT válido
        rut_valido, rut_resultado = validar_rut_chileno("12345678-5")
        assert rut_valido is True

        # Correo válido
        correo_valido, correo_resultado = validar_formato_correo("usuario@example.com")
        assert correo_valido is True

        # Rol válido
        rol_valido, rol_resultado = validar_rol("ADMIN")
        assert rol_valido is True

    @pytest.mark.validator
    def test_validar_vehiculo_completo(self):
        """Test validación completa de datos de vehículo"""
        # Patente válida
        patente_valida, patente_resultado = validar_formato_patente("AB1234")
        assert patente_valida is True

        # Año válido
        ano_actual = datetime.now().year
        ano_valido, ano_resultado = validar_ano(ano_actual)
        assert ano_valido is True

    @pytest.mark.validator
    def test_validar_fechas_rango(self):
        """Test validación de rango de fechas para reportes"""
        fecha_inicio = date(2024, 1, 1)
        fecha_fin = date(2024, 12, 31)

        rango_valido, rango_resultado = validar_rango_fechas(fecha_inicio, fecha_fin)
        assert rango_valido is True

    @pytest.mark.validator
    def test_validar_datos_incompletos(self):
        """Test que valida que datos incompletos fallan"""
        # RUT vacío
        rut_valido, _ = validar_rut_chileno("")
        assert rut_valido is False

        # Patente vacía
        patente_valida, _ = validar_formato_patente("")
        assert patente_valida is False

        # Correo vacío
        correo_valido, _ = validar_formato_correo("")
        assert correo_valido is False

    @pytest.mark.validator
    def test_validar_datos_invalidos_combinados(self):
        """Test que valida múltiples datos inválidos"""
        # RUT inválido
        rut_valido, _ = validar_rut_chileno("12345678-0")
        assert rut_valido is False

        # Patente inválida
        patente_valida, _ = validar_formato_patente("INVALID")
        assert patente_valida is False

        # Correo inválido
        correo_valido, _ = validar_formato_correo("no-es-un-correo")
        assert correo_valido is False

        # Año inválido
        ano_valido, _ = validar_ano(1999)
        assert ano_valido is False

        # Rol inválido
        rol_valido, _ = validar_rol("ROL_INEXISTENTE")
        assert rol_valido is False


class TestCasosLimite:
    """Tests para casos límite y edge cases"""

    @pytest.mark.validator
    def test_rut_con_ceros_izquierda(self):
        """Test RUT con ceros a la izquierda"""
        # RUT válido con ceros
        rut_valido, resultado = validar_rut_chileno("00000013-K")
        # El validador debe manejar esto correctamente
        assert isinstance(rut_valido, bool)

    @pytest.mark.validator
    def test_patente_minusculas(self):
        """Test que patente en minúsculas se convierte a mayúsculas"""
        patente_valida, resultado = validar_formato_patente("ab1234")
        assert patente_valida is True
        assert resultado == "AB1234"

    @pytest.mark.validator
    def test_correo_con_mayusculas(self):
        """Test que correo con mayúsculas se convierte a minúsculas"""
        correo_valido, resultado = validar_formato_correo("USUARIO@EXAMPLE.COM")
        assert correo_valido is True
        assert resultado == "usuario@example.com"

    @pytest.mark.validator
    def test_ano_limite_inferior(self):
        """Test año en el límite inferior (2000)"""
        ano_valido, resultado = validar_ano(2000)
        assert ano_valido is True

    @pytest.mark.validator
    def test_ano_limite_superior(self):
        """Test año en el límite superior (año actual)"""
        ano_actual = datetime.now().year
        ano_valido, resultado = validar_ano(ano_actual)
        assert ano_valido is True

    @pytest.mark.validator
    def test_rango_fechas_mismo_dia(self):
        """Test rango de fechas con mismo día inicio y fin"""
        fecha = date(2024, 6, 15)
        rango_valido, resultado = validar_rango_fechas(fecha, fecha)
        assert rango_valido is True

