#!/bin/bash
# Script para ejecutar pytest desde Docker
# Uso: ./scripts/run_pytest.sh [opciones]

set -e

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Ejecutando pruebas con pytest${NC}"

# Verificar que Docker está corriendo
if ! docker compose ps api > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  El contenedor 'api' no está corriendo. Iniciando contenedores...${NC}"
    docker compose up -d
    sleep 5
fi

# Si no se pasan argumentos, ejecutar todas las pruebas
if [ $# -eq 0 ]; then
    echo -e "${GREEN}Ejecutando todas las pruebas...${NC}"
    docker compose exec api poetry run pytest apps/ -v
else
    # Pasar todos los argumentos a pytest
    echo -e "${GREEN}Ejecutando pytest con argumentos: $@${NC}"
    docker compose exec api poetry run pytest "$@"
fi

echo -e "${GREEN}✅ Pruebas completadas${NC}"

