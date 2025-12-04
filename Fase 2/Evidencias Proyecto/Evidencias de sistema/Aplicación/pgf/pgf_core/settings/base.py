# pgf_core/settings/base.py ESTE ES EL SETTIGS PRINCIPAL, LOS DEMÁS IMPORTAN DESDE AQUÍ
import os
from pathlib import Path
from datetime import timedelta
from urllib.parse import urlparse
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def get_env_variable(var_name, default=None):
    """Obtiene una variable de entorno o lanza ImproperlyConfigured."""
    try:
        return os.environ[var_name]
    except KeyError:
        if default is not None:
            return default
        error_msg = f"Set the {var_name} environment variable"
        raise ImproperlyConfigured(error_msg)

# -------- Core --------
DEBUG = os.getenv("DEBUG", "True") == "True"

# SECRET_KEY: Nunca usar default inseguro en producción
# En desarrollo local, generar automáticamente si no está configurado
if DEBUG and not os.getenv("SECRET_KEY"):
    import secrets
    SECRET_KEY = secrets.token_urlsafe(50)
    print("⚠️  WARNING: Using auto-generated SECRET_KEY. Set SECRET_KEY in .env for production!")
else:
    SECRET_KEY = get_env_variable("SECRET_KEY")

# ALLOWED_HOSTS: NUNCA usar "*" como default - riesgo de Host Header Injection
# En desarrollo, usar localhost por defecto
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if os.getenv("ALLOWED_HOSTS") else ["localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",  # Django Channels para WebSockets
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "django_filters",
    "corsheaders",
    "apps.core",  # App core para funcionalidades compartidas (monitoreo, logging, etc.)
    "apps.users",
    "apps.vehicles",
    "apps.workorders",
    "apps.inventory",
    "apps.reports",
    "apps.drivers",
    "apps.scheduling",
    # "apps.emergencies",  # App de emergencias deshabilitada
    "apps.notifications",
]

AUTH_USER_MODEL = "users.User"
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "apps.core.middleware.RequestLoggingMiddleware",  # Logging de requests y métricas
    "apps.workorders.middleware.RateLimitMiddleware",  # Rate limiting habilitado para protección contra ataques
    "apps.core.middleware.SecurityHeadersMiddleware",  # Headers de seguridad adicionales
    "django.contrib.sessions.middleware.SessionMiddleware",         # ✔ requerido
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",                    # opcional pero recomendado
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",       # ✔ requerido
    "django.contrib.messages.middleware.MessageMiddleware",          # ✔ requerido
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "pgf_core.urls"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

WSGI_APPLICATION = "pgf_core.wsgi.application"
ASGI_APPLICATION = "pgf_core.asgi.application"

# -------- DB --------
db_url = os.getenv("DATABASE_URL", "postgres://pgf:pgf@db:5432/pgf")
u = urlparse(db_url)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": u.path[1:], "USER": u.username, "PASSWORD": u.password,
        "HOST": u.hostname, "PORT": u.port or 5432,
        "CONN_MAX_AGE": 60,
    }
}

# -------- i18n --------
LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

# -------- Static --------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# -------- DRF --------

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",  
    "DEFAULT_AUTHENTICATION_CLASSES": [
        
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    # DEFAULT_PERMISSION_CLASSES: Cambiar a IsAuthenticated por defecto
    # Esto previene exposición accidental de datos
    # Los endpoints públicos deben especificar explícitamente AllowAny
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    # Paginación global para todos los ViewSets
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,  # Tamaño de página por defecto
    "PAGE_SIZE_QUERY_PARAM": "page_size",  # Permitir personalizar tamaño de página
    "MAX_PAGE_SIZE": 200,  # Tamaño máximo de página permitido
}
SPECTACULAR_SETTINGS = {
    "TITLE": "PGF API",
    "DESCRIPTION": "Plataforma de Gestión de Flota",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api",
    "SERVERS": [{"url": os.getenv("PUBLIC_URL", "http://127.0.0.1:8000")}],
    "SECURITY": [{"BearerAuth": []}],
    "SWAGGER_UI_SETTINGS": {"persistAuthorization": True},
    "COMPONENT_SPLIT_REQUEST": True,
    
}

# -------- JWT --------
SIMPLE_JWT = {
    # Reducir tiempos de vida de tokens para mayor seguridad
    # Si un token es comprometido, permanece válido por menos tiempo
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),  # 1 hora (reducido de 8)
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),  # 1 día (reducido de 7)
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# -------- Logging Centralizado --------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "{levelname} {asctime} {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": LOG_LEVEL,
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "pgf.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 5,
            "formatter": "verbose",
            "level": LOG_LEVEL,
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "errors.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 5,
            "formatter": "verbose",
            "level": "ERROR",
        },
        "security_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "security.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 10,  # Mantener más backups de seguridad
            "formatter": "verbose",
            "level": "WARNING",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "django.request": {
            "handlers": ["error_file", "console"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["security_file", "console"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "apps.workorders": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "apps.workorders.middleware": {
            "handlers": ["security_file", "console"],
            "level": "WARNING",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": LOG_LEVEL,
    },
}

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

SESSION_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = "Lax"
CORS_ALLOW_ALL_ORIGINS = False

# CORS_ALLOW_HEADERS: No permitir "*" - especificar headers explícitamente
# Esto previene envío de headers maliciosos
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]

# -------- Channels (WebSockets) --------
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(os.getenv("REDIS_HOST", "redis"), int(os.getenv("REDIS_PORT", "6379")))],
        },
    },
}

# -------- AWS S3 --------


import os
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME", "pgf-evidencias-dev")
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "us-east-1")
AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL", "http://localstack:4566")
AWS_ACCESS_KEY_ID = get_env_variable("AWS_ACCESS_KEY_ID", "test" if DEBUG else None)
AWS_SECRET_ACCESS_KEY = get_env_variable("AWS_SECRET_ACCESS_KEY", "test" if DEBUG else None)
# URL pública para acceder a LocalStack desde el navegador
# En producción con Cloudflare Tunnel, debe ser la URL del túnel que expone LocalStack
# IMPORTANTE: Configurar en .env.prod:
# - AWS_PUBLIC_URL_PREFIX=https://random-name-localstack.trycloudflare.com
# O si LocalStack está en el mismo túnel con ruta:
# - AWS_PUBLIC_URL_PREFIX=https://random-name.trycloudflare.com/localstack
# 
# Si no está configurado, intenta construir desde CLOUDFLARE_TUNNEL_URL
# Por defecto usa localhost solo para desarrollo local
aws_public_url = os.getenv("AWS_PUBLIC_URL_PREFIX")
if not aws_public_url:
    cloudflare_url = os.getenv("CLOUDFLARE_TUNNEL_URL", "").rstrip("/")
    if cloudflare_url:
        # Construir URL asumiendo que LocalStack está en el mismo dominio con ruta /localstack
        aws_public_url = f"{cloudflare_url}/localstack"
    else:
        aws_public_url = "http://localhost:4566"

AWS_PUBLIC_URL_PREFIX = aws_public_url

# -------- EMAIL --------
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "kui.peer1402@gmail.com")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")  # Configurar en .env
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "kui.peer1402@gmail.com")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# URL del frontend para enlaces de recuperación
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# -------- CACHING (Redis) --------
# Nota: Requiere django-redis instalado
try:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": os.getenv("REDIS_URL", "redis://redis:6379/2"),  # DB 2 para cache (0 y 1 son para Celery)
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
            "KEY_PREFIX": "pgf",
            "TIMEOUT": 300,  # 5 minutos por defecto
        }
    }
except ImportError:
    # Fallback a cache en memoria si django-redis no está instalado
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
        }
    }