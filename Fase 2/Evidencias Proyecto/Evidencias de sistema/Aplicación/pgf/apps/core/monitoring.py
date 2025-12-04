"""
Sistema de monitoreo básico para el proyecto PGF.

Proporciona funciones para monitorear:
- Salud de la aplicación
- Métricas de rendimiento
- Estado de servicios externos
- Uso de recursos
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from django.core.cache import cache
from django.db import connection
from django.conf import settings

logger = logging.getLogger(__name__)


class HealthCheck:
    """Clase para verificar la salud de la aplicación."""
    
    @staticmethod
    def check_database() -> Dict[str, Any]:
        """Verifica la conexión a la base de datos."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            return {
                "status": "healthy",
                "response_time_ms": 0,  # Se puede mejorar midiendo el tiempo
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
            }
    
    @staticmethod
    def check_cache() -> Dict[str, Any]:
        """Verifica la conexión al cache (Redis)."""
        try:
            start = time.time()
            cache.set("health_check", "ok", 10)
            value = cache.get("health_check")
            response_time = (time.time() - start) * 1000
            
            if value == "ok":
                return {
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2),
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": "Cache value mismatch",
                }
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
            }
    
    @staticmethod
    def check_storage() -> Dict[str, Any]:
        """Verifica el acceso a almacenamiento (S3/LocalStack)."""
        try:
            import boto3
            import os
            from botocore.config import Config
            
            endpoint_url = os.getenv("AWS_S3_ENDPOINT_URL", "http://localstack:4566")
            bucket = os.getenv("AWS_STORAGE_BUCKET_NAME", "pgf-evidencias-dev")
            
            use_local = "localstack" in endpoint_url.lower() or "localhost:4566" in endpoint_url.lower()
            s3 = boto3.client(
                "s3",
                endpoint_url=endpoint_url if use_local else None,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
                region_name=os.getenv("AWS_S3_REGION_NAME", "us-east-1"),
                config=Config(s3={"addressing_style": "path"}) if use_local else None
            )
            
            start = time.time()
            s3.head_bucket(Bucket=bucket)
            response_time = (time.time() - start) * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
            }
        except Exception as e:
            logger.error(f"Storage health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
            }
    
    @staticmethod
    def check_all() -> Dict[str, Any]:
        """Verifica todos los componentes del sistema."""
        checks = {
            "database": HealthCheck.check_database(),
            "cache": HealthCheck.check_cache(),
            "storage": HealthCheck.check_storage(),
            "timestamp": datetime.now().isoformat(),
        }
        
        # Determinar estado general
        all_healthy = all(
            check.get("status") == "healthy"
            for check in checks.values()
            if isinstance(check, dict) and "status" in check
        )
        
        checks["overall_status"] = "healthy" if all_healthy else "degraded"
        
        return checks


class MetricsCollector:
    """Recolector de métricas básicas."""
    
    @staticmethod
    def get_request_metrics() -> Dict[str, Any]:
        """Obtiene métricas de requests."""
        # Esto se puede mejorar usando middleware para contar requests
        return {
            "total_requests": cache.get("metrics:total_requests", 0),
            "failed_requests": cache.get("metrics:failed_requests", 0),
            "rate_limited_requests": cache.get("metrics:rate_limited", 0),
        }
    
    @staticmethod
    def increment_request(success: bool = True):
        """Incrementa contador de requests."""
        cache.set(
            "metrics:total_requests",
            cache.get("metrics:total_requests", 0) + 1,
            timeout=None
        )
        if not success:
            cache.set(
                "metrics:failed_requests",
                cache.get("metrics:failed_requests", 0) + 1,
                timeout=None
            )
    
    @staticmethod
    def increment_rate_limited():
        """Incrementa contador de requests bloqueados por rate limiting."""
        cache.set(
            "metrics:rate_limited",
            cache.get("metrics:rate_limited", 0) + 1,
            timeout=None
        )


class PerformanceMonitor:
    """Monitor de rendimiento."""
    
    @staticmethod
    def measure_time(func):
        """Decorador para medir tiempo de ejecución de funciones."""
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = (time.time() - start) * 1000
                logger.info(f"{func.__name__} executed in {execution_time:.2f}ms")
                return result
            except Exception as e:
                execution_time = (time.time() - start) * 1000
                logger.error(f"{func.__name__} failed after {execution_time:.2f}ms: {e}")
                raise
        return wrapper

