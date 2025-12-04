#!/usr/bin/env python3
"""
Script de verificación de configuración del proyecto PGF.

Verifica que todas las variables de entorno necesarias estén configuradas
y que las relaciones entre componentes estén correctas.

Uso:
    python scripts/verificar-configuracion.py
"""

import os
import sys
from pathlib import Path

# Colores para output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

def check_env_var(var_name, required=True, default=None):
    """Verifica si una variable de entorno está configurada."""
    value = os.getenv(var_name, default)
    if value:
        print(f"{GREEN}✓{RESET} {var_name} = {value}")
        return True
    else:
        if required:
            print(f"{RED}✗{RESET} {var_name} NO CONFIGURADA (requerida)")
            return False
        else:
            print(f"{YELLOW}⚠{RESET} {var_name} NO CONFIGURADA (opcional)")
            return True

def check_file_exists(filepath, description):
    """Verifica si un archivo existe."""
    path = Path(filepath)
    if path.exists():
        print(f"{GREEN}✓{RESET} {description}: {filepath}")
        return True
    else:
        print(f"{YELLOW}⚠{RESET} {description} NO ENCONTRADO: {filepath}")
        return False

def main():
    print("=" * 60)
    print("VERIFICACIÓN DE CONFIGURACIÓN - PROYECTO PGF")
    print("=" * 60)
    print()
    
    errors = []
    warnings = []
    
    # Verificar variables de entorno críticas
    print("1. VARIABLES DE ENTORNO CRÍTICAS:")
    print("-" * 60)
    
    if not check_env_var("SECRET_KEY", required=True):
        errors.append("SECRET_KEY no configurada")
    
    if not check_env_var("DATABASE_URL", required=False, default="postgres://pgf:pgf@db:5432/pgf"):
        warnings.append("DATABASE_URL usando valor por defecto")
    
    # Verificar configuración de AWS/LocalStack
    print()
    print("2. CONFIGURACIÓN AWS/LOCALSTACK:")
    print("-" * 60)
    
    aws_public_url = os.getenv("AWS_PUBLIC_URL_PREFIX")
    cloudflare_url = os.getenv("CLOUDFLARE_TUNNEL_URL")
    
    if not aws_public_url and not cloudflare_url:
        print(f"{RED}✗{RESET} AWS_PUBLIC_URL_PREFIX o CLOUDFLARE_TUNNEL_URL deben estar configuradas")
        errors.append("Configuración de Cloudflare Tunnel faltante")
    elif aws_public_url:
        print(f"{GREEN}✓{RESET} AWS_PUBLIC_URL_PREFIX = {aws_public_url}")
    elif cloudflare_url:
        print(f"{GREEN}✓{RESET} CLOUDFLARE_TUNNEL_URL = {cloudflare_url}")
        print(f"{YELLOW}⚠{RESET} AWS_PUBLIC_URL_PREFIX se construirá automáticamente desde CLOUDFLARE_TUNNEL_URL")
        warnings.append("AWS_PUBLIC_URL_PREFIX se construirá automáticamente")
    
    check_env_var("AWS_STORAGE_BUCKET_NAME", required=False, default="pgf-evidencias-dev")
    check_env_var("AWS_S3_ENDPOINT_URL", required=False, default="http://localstack:4566")
    
    # Verificar configuración de Celery
    print()
    print("3. CONFIGURACIÓN CELERY:")
    print("-" * 60)
    
    check_env_var("CELERY_BROKER_URL", required=False, default="redis://redis:6379/0")
    check_env_var("CELERY_RESULT_BACKEND", required=False, default="redis://redis:6379/1")
    check_env_var("REDIS_HOST", required=False, default="redis")
    check_env_var("REDIS_PORT", required=False, default="6379")
    
    # Verificar configuración de CORS
    print()
    print("4. CONFIGURACIÓN CORS:")
    print("-" * 60)
    
    cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
    if cors_origins:
        print(f"{GREEN}✓{RESET} CORS_ALLOWED_ORIGINS = {cors_origins}")
    else:
        print(f"{YELLOW}⚠{RESET} CORS_ALLOWED_ORIGINS no configurada (usando valores por defecto)")
        warnings.append("CORS_ALLOWED_ORIGINS no configurada")
    
    # Verificar archivos importantes
    print()
    print("5. ARCHIVOS DE CONFIGURACIÓN:")
    print("-" * 60)
    
    check_file_exists(".env", "Archivo de variables de entorno")
    check_file_exists("docker-compose.yml", "Docker Compose")
    check_file_exists("docker-compose.cloudflare.yml", "Docker Compose Cloudflare")
    check_file_exists("pgf_core/settings/base.py", "Settings base")
    
    # Verificar configuración de producción
    print()
    print("6. CONFIGURACIÓN DE PRODUCCIÓN:")
    print("-" * 60)
    
    debug = os.getenv("DEBUG", "True")
    if debug == "True":
        print(f"{YELLOW}⚠{RESET} DEBUG=True (modo desarrollo)")
        warnings.append("DEBUG activado en producción")
    else:
        print(f"{GREEN}✓{RESET} DEBUG=False (modo producción)")
    
    allowed_hosts = os.getenv("ALLOWED_HOSTS", "")
    if allowed_hosts == "*":
        print(f"{RED}✗{RESET} ALLOWED_HOSTS='*' es inseguro en producción")
        errors.append("ALLOWED_HOSTS='*' es inseguro")
    elif allowed_hosts:
        print(f"{GREEN}✓{RESET} ALLOWED_HOSTS = {allowed_hosts}")
    else:
        print(f"{YELLOW}⚠{RESET} ALLOWED_HOSTS no configurada (usando valores por defecto)")
    
    # Resumen
    print()
    print("=" * 60)
    print("RESUMEN:")
    print("=" * 60)
    
    if errors:
        print(f"{RED}ERRORES ENCONTRADOS: {len(errors)}{RESET}")
        for error in errors:
            print(f"  {RED}✗{RESET} {error}")
        print()
    
    if warnings:
        print(f"{YELLOW}ADVERTENCIAS: {len(warnings)}{RESET}")
        for warning in warnings:
            print(f"  {YELLOW}⚠{RESET} {warning}")
        print()
    
    if not errors and not warnings:
        print(f"{GREEN}✓ CONFIGURACIÓN CORRECTA{RESET}")
        return 0
    elif not errors:
        print(f"{YELLOW}⚠ CONFIGURACIÓN CON ADVERTENCIAS (no críticas){RESET}")
        return 0
    else:
        print(f"{RED}✗ CONFIGURACIÓN CON ERRORES{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

