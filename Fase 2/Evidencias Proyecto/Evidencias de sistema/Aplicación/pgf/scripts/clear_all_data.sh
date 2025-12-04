#!/bin/bash
# Script para borrar todos los datos de la base de datos
# Mantiene el usuario admin permanente

set -e

echo "🗑️  Script de limpieza de base de datos"
echo "========================================"
echo ""
echo "Este script borrará TODOS los datos de la base de datos"
echo "excepto el usuario admin permanente."
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Este script debe ejecutarse desde la raíz del proyecto"
    exit 1
fi

# Verificar que el contenedor está corriendo
if ! docker compose ps api | grep -q "Up"; then
    echo "❌ Error: El contenedor 'api' no está corriendo"
    echo "   Ejecuta: docker compose up -d"
    exit 1
fi

# Ejecutar el comando de Django
echo "Ejecutando limpieza de datos..."
echo ""

docker compose exec -T api poetry run python manage.py clear_all_data "$@"

echo ""
echo "✅ Limpieza completada"

