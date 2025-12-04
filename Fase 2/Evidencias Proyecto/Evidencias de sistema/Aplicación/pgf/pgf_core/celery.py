# pgf_core/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pgf_core.settings")

celery_app = Celery("pgf")
celery_app.config_from_object("django.conf:settings", namespace="CELERY")

# Autodiscover tasks - busca tasks.py en todas las apps
celery_app.autodiscover_tasks()



@celery_app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
