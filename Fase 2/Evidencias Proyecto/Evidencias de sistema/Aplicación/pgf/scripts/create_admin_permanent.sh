#!/bin/bash
# Script para crear el usuario admin permanente con credenciales admin/admin123

echo "🔧 Creando usuario admin permanente..."

# Intentar con Docker (si está disponible)
if command -v docker &> /dev/null && docker ps &> /dev/null; then
    echo "📦 Ejecutando con Docker..."
    docker compose exec api poetry run python manage.py create_permanent_admin
    exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo "✅ Comando ejecutado exitosamente"
        exit 0
    fi
fi

# Intentar con Poetry directamente
if command -v poetry &> /dev/null; then
    echo "📦 Ejecutando con Poetry..."
    poetry run python manage.py create_permanent_admin
    exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo "✅ Comando ejecutado exitosamente"
        exit 0
    fi
fi

# Intentar con Python directamente (si el entorno virtual está activado)
echo "🐍 Ejecutando con Python..."
python manage.py create_permanent_admin
exit_code=$?
if [ $exit_code -eq 0 ]; then
    echo "✅ Comando ejecutado exitosamente"
    exit 0
fi

echo "❌ Error: No se pudo ejecutar el comando"
echo "💡 Asegúrate de tener:"
echo "   - Docker y docker-compose instalados, O"
echo "   - Poetry instalado y el entorno activado, O"
echo "   - Un entorno virtual de Python activado con Django instalado"
echo ""
echo "📝 Ejecuta manualmente:"
echo "   docker compose exec api poetry run python manage.py create_permanent_admin"
echo "   O"
echo "   poetry run python manage.py create_permanent_admin"
echo "   O"
echo "   python manage.py create_permanent_admin"

exit 1

