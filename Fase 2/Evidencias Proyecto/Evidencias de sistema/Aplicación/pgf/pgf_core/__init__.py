# pgf_core/__init__.py
from .celery import celery_app as app  # noqa
__all__ = ("app",)