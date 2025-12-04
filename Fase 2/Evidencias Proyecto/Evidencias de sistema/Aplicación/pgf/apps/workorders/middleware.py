# apps/workorders/middleware.py
from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone
import hashlib

class RateLimitMiddleware:
    """
    Middleware para rate limiting simple basado en IP
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Configuración: requests por minuto (aumentado para evitar bloqueos en uso normal)
        self.requests_per_minute = 300  # Aumentado de 60 a 300 (5 por segundo)
        self.window_seconds = 60
        
        # Endpoints excluidos del rate limiting (endpoints de solo lectura frecuentes)
        self.excluded_paths = [
            '/api/v1/work/evidencias/',  # Listado de evidencias
            '/api/v1/work/evidencias/',  # Descarga de evidencias (presigned URLs)
            '/api/v1/work/ordenes/',  # Listado de OTs
            '/api/v1/vehicles/',  # Listado de vehículos
        ]

    def __call__(self, request):
        # Solo aplicar rate limiting a endpoints de API
        if not request.path.startswith('/api/'):
            return self.get_response(request)
        
        # Excluir completamente los métodos GET de solo lectura del rate limiting
        # Estos endpoints se llaman frecuentemente y no deberían ser bloqueados
        if request.method == 'GET':
            # Para GET requests, no aplicar rate limiting (solo lectura)
            response = self.get_response(request)
            return response
        
        # Para métodos de escritura (POST, PUT, PATCH, DELETE), aplicar límite normal
        ip = self.get_client_ip(request)
        cache_key = f"ratelimit:{ip}"
        
        # Obtener contador actual
        current_count = cache.get(cache_key, 0)
        
        if current_count >= self.requests_per_minute:
            # Registrar intento de rate limiting
            from apps.core.monitoring import MetricsCollector
            MetricsCollector.increment_rate_limited()
            
            # Log de seguridad
            import logging
            logger = logging.getLogger("apps.workorders.middleware")
            logger.warning(
                f"Rate limit exceeded for IP {ip} on {request.path} - "
                f"Count: {current_count}/{self.requests_per_minute}"
            )
            
            return JsonResponse(
                {"detail": "Rate limit exceeded. Please try again later."},
                status=429
            )
        
        # Incrementar contador
        cache.set(cache_key, current_count + 1, self.window_seconds)
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """Obtiene la IP del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


def validate_file_upload(file, max_size_mb=3072, allowed_types=None):
    """
    Valida un archivo subido para evidencias.
    
    Parámetros:
    - max_size_mb: Tamaño máximo en MB (default: 3072 = 3GB)
    - allowed_types: Lista de tipos MIME permitidos (opcional)
    
    Tipos permitidos por defecto:
    - Imágenes: JPEG, PNG, GIF, WebP
    - Documentos: PDF, DOC, DOCX
    - Hojas de cálculo: XLSX, XLS, CSV
    - Otros: Cualquier archivo hasta 3GB
    
    Retorna:
    - dict con 'valid' (bool) y 'errors' (list)
    """
    if allowed_types is None:
        # Tipos MIME permitidos (más permisivo para soportar cualquier archivo)
        allowed_types = [
            # Imágenes
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/bmp',
            # Documentos PDF
            'application/pdf',
            # Documentos Word
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
            'application/msword',  # .doc
            # Hojas de cálculo Excel
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
            'application/vnd.ms-excel',  # .xls
            'text/csv',  # .csv
            # Otros tipos comunes
            'application/zip',  # Archivos comprimidos
            'application/x-zip-compressed',
            'application/octet-stream',  # Archivos binarios genéricos
        ]
    
    errors = []
    
    # Validar tamaño (3GB = 3072 MB)
    max_size_bytes = max_size_mb * 1024 * 1024
    if file.size > max_size_bytes:
        # Formatear tamaño en GB para mensaje más legible
        max_size_gb = max_size_mb / 1024
        file_size_gb = file.size / (1024 * 1024 * 1024)
        errors.append(f"El archivo excede el tamaño máximo de {max_size_gb:.1f}GB. Tamaño actual: {file_size_gb:.2f}GB")
    
    # Validar tipo MIME (más permisivo - acepta cualquier tipo si es application/octet-stream)
    if hasattr(file, 'content_type') and file.content_type:
        # Si es application/octet-stream, aceptar cualquier extensión conocida
        if file.content_type == 'application/octet-stream':
            # Validar por extensión en lugar de tipo MIME
            allowed_extensions = [
                '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp',  # Imágenes
                '.pdf',  # PDFs
                '.doc', '.docx',  # Word
                '.xls', '.xlsx', '.csv',  # Excel
                '.zip', '.rar', '.7z',  # Comprimidos
                '.txt', '.rtf',  # Texto
            ]
            file_name = file.name.lower()
            if not any(file_name.endswith(ext) for ext in allowed_extensions):
                # Si no tiene extensión conocida pero es octet-stream, permitirlo (archivo genérico)
                pass  # Permitir archivos genéricos
        elif file.content_type not in allowed_types:
            errors.append(f"Tipo de archivo no permitido: {file.content_type}. Tipos permitidos: imágenes, PDFs, documentos Word, hojas de cálculo Excel, archivos comprimidos")
    
    # Validar extensión (backup - más permisivo)
    allowed_extensions = [
        # Imágenes
        '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp',
        # Documentos
        '.pdf', '.doc', '.docx', '.txt', '.rtf',
        # Hojas de cálculo
        '.xls', '.xlsx', '.csv',
        # Comprimidos
        '.zip', '.rar', '.7z', '.tar', '.gz',
        # Otros
        '.mp4', '.avi', '.mov',  # Videos (opcional)
    ]
    file_name = file.name.lower()
    
    # Si no tiene extensión conocida, permitirlo si es menor a 3GB (archivo genérico)
    if not any(file_name.endswith(ext) for ext in allowed_extensions):
        # Permitir archivos sin extensión conocida (pueden ser archivos genéricos)
        pass  # No bloquear por extensión desconocida
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

