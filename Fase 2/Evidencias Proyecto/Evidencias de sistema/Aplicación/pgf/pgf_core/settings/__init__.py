import os

# Determinar qué configuración usar basado en la variable de entorno
ENVIRONMENT = os.getenv("DJANGO_ENV", "dev").lower()

if ENVIRONMENT == "prod" or ENVIRONMENT == "production":
    from .prod import *
else:
    from .dev import *
