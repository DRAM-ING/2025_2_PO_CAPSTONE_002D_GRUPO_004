# apps/core/validators.py
"""
Validadores reutilizables para el sistema PGF.

Este módulo contiene funciones de validación que pueden ser usadas
en serializers, modelos y views para validar datos de entrada.
"""

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validar_rut_chileno(rut: str) -> tuple[bool, str]:
    """
    Valida un RUT chileno.
    
    Parámetros:
    - rut: String con el RUT (puede tener o no puntos y guión)
    
    Retorna:
    - (True, rut_limpio) si es válido
    - (False, mensaje_error) si es inválido
    
    Formato esperado: XXXXXXXXX-X (sin puntos, con guión)
    """
    if not rut:
        return False, "El RUT no puede estar vacío."
    
    # Limpiar RUT: quitar puntos, espacios y convertir a mayúsculas
    rut_limpio = rut.replace(".", "").replace(" ", "").replace("-", "").upper()
    
    if len(rut_limpio) < 8 or len(rut_limpio) > 9:
        return False, "El RUT debe tener entre 8 y 9 caracteres (sin puntos ni guión)."
    
    # Separar número y dígito verificador
    if len(rut_limpio) == 8:
        # RUT sin dígito verificador (agregar 0 al inicio)
        numero = rut_limpio[:-1]
        dv = rut_limpio[-1]
    else:
        numero = rut_limpio[:-1]
        dv = rut_limpio[-1]
    
    # Validar que el número sea solo dígitos
    if not numero.isdigit():
        return False, "El RUT debe contener solo números (excepto el dígito verificador)."
    
    # Validar dígito verificador
    if dv not in "0123456789K":
        return False, "El dígito verificador debe ser un número o K."
    
    # Calcular dígito verificador
    multiplicadores = [2, 3, 4, 5, 6, 7, 2, 3]
    suma = 0
    numero_reverso = numero[::-1]
    
    for i, digito in enumerate(numero_reverso):
        suma += int(digito) * multiplicadores[i % len(multiplicadores)]
    
    resto = suma % 11
    dv_calculado = 11 - resto
    
    if dv_calculado == 11:
        dv_calculado = "0"
    elif dv_calculado == 10:
        dv_calculado = "K"
    else:
        dv_calculado = str(dv_calculado)
    
    if dv != dv_calculado:
        return False, f"El dígito verificador es inválido. Debería ser {dv_calculado}."
    
    # Retornar RUT en formato estándar: XXXXXXXXX-X
    rut_formateado = f"{numero}-{dv}"
    return True, rut_formateado


def validar_formato_patente(patente: str) -> tuple[bool, str]:
    """
    Valida y normaliza el formato de una patente chilena.
    
    Formatos válidos (todos se normalizan al mismo formato sin guión):
    - AA1234 (2 letras + 4 números) → AA1234
    - AA-1234 (con guión) → AA1234
    - AAAA12 (4 letras + 2 números) → AAAA12
    - AAAA-12 (con guión) → AAAA12
    - AAAB12 (3 letras + 1 letra + 2 números) → AAAB12
    - AAAB-12 (con guión) → AAAB12
    
    Retorna:
    - (True, patente_normalizada) si es válido (siempre sin guiones, mayúsculas)
    - (False, mensaje_error) si es inválido
    
    IMPORTANTE: Todas las patentes se normalizan al formato SIN GUIONES.
    """
    if not patente:
        return False, "La patente no puede estar vacía."
    
    # Limpiar patente: quitar espacios, guiones y convertir a mayúsculas
    # Esto normaliza todos los formatos al mismo (sin guiones)
    patente_limpia = patente.replace(" ", "").replace("-", "").replace("_", "").upper()
    
    # Validar longitud (debe tener exactamente 6 caracteres después de limpiar)
    if len(patente_limpia) != 6:
        return False, f"La patente debe tener exactamente 6 caracteres (sin guiones). Recibido: {len(patente_limpia)} caracteres."
    
    # Patrón 1: AA1234 (2 letras + 4 números)
    patron1 = re.compile(r'^[A-Z]{2}\d{4}$')
    # Patrón 2: AAAA12 (4 letras + 2 números)
    patron2 = re.compile(r'^[A-Z]{4}\d{2}$')
    # Patrón 3: AAAB12 (3 letras + 1 letra + 2 números)
    patron3 = re.compile(r'^[A-Z]{3}[A-Z]\d{2}$')
    
    if patron1.match(patente_limpia) or patron2.match(patente_limpia) or patron3.match(patente_limpia):
        # Retornar patente normalizada (sin guiones, mayúsculas)
        return True, patente_limpia
    
    return False, "Formato de patente inválido. Debe ser: AA1234, AAAA12 o AAAB12 (con o sin guión)."


def validar_formato_correo(correo: str) -> tuple[bool, str]:
    """
    Valida el formato de un correo electrónico.
    
    Retorna:
    - (True, correo_limpio) si es válido
    - (False, mensaje_error) si es inválido
    """
    if not correo:
        return False, "El correo no puede estar vacío."
    
    correo_limpio = correo.strip().lower()
    
    # Patrón básico de correo
    patron = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    if not patron.match(correo_limpio):
        return False, "Formato de correo inválido."
    
    return True, correo_limpio


def validar_ano(ano: int) -> tuple[bool, str]:
    """
    Valida que el año sea válido (entre 2000 y el año actual).
    
    Retorna:
    - (True, None) si es válido
    - (False, mensaje_error) si es inválido
    """
    from datetime import datetime
    
    ano_actual = datetime.now().year
    
    if ano < 2000:
        return False, f"El año debe ser mayor o igual a 2000."
    
    if ano > ano_actual:
        return False, f"El año no puede ser mayor al año actual ({ano_actual})."
    
    return True, None


def validar_rol(rol: str) -> tuple[bool, str]:
    """
    Valida que el rol sea uno de los permitidos.
    
    Retorna:
    - (True, None) si es válido
    - (False, mensaje_error) si es inválido
    """
    # Todos los roles disponibles en el sistema
    roles_validos = [
        "GUARDIA", "SUPERVISOR", "MECANICO", "JEFE_TALLER", "ADMIN",
        "COORDINADOR_ZONA", "EJECUTIVO", "SPONSOR", "CHOFER",
        "ADMINISTRATIVO_TALLER", "BODEGA"
    ]
    
    if rol not in roles_validos:
        return False, f"El rol '{rol}' no es válido. Roles permitidos: {', '.join(roles_validos)}."
    
    return True, None


def validar_rango_fechas(fecha_inicio, fecha_fin) -> tuple[bool, str]:
    """
    Valida que fecha_inicio <= fecha_fin.
    
    Retorna:
    - (True, None) si es válido
    - (False, mensaje_error) si es inválido
    """
    if fecha_inicio and fecha_fin:
        if fecha_inicio > fecha_fin:
            return False, "La fecha de inicio no puede ser mayor que la fecha de fin."
    
    return True, None

