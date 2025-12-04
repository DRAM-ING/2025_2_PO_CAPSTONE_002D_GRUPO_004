# pgf_core/settings/dev.py
from .base import *
import os

DEBUG = True
ALLOWED_HOSTS = ["*"]

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

# Celery Beat Schedule (tareas periódicas)
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Colación automática: iniciar a las 12:30
    'iniciar-colacion-automatica': {
        'task': 'apps.workorders.tasks_colacion.iniciar_colacion_automatica',
        'schedule': crontab(hour=12, minute=30),  # Todos los días a las 12:30
    },
    # Colación automática: finalizar a las 13:15
    'finalizar-colacion-automatica': {
        'task': 'apps.workorders.tasks_colacion.finalizar_colacion_automatica',
        'schedule': crontab(hour=13, minute=15),  # Todos los días a las 13:15
    },
}

CELERY_TIMEZONE = 'America/Santiago'
CELERY_ENABLE_UTC = False
