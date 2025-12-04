# apps/core/serializers.py
from rest_framework import serializers

class EmptySerializer(serializers.Serializer):
    """Útil para acciones POST/DELETE sin body.
    Evita errores de schema y AutoSchema cuando no hay request body."""
    pass
