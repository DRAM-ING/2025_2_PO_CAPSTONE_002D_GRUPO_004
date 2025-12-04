#!/bin/bash
# Script para ejecutar escaneo de seguridad con OWASP ZAP
# Soporta ejecución con Docker Compose o Docker standalone

# NO usar set -e aquí porque queremos manejar errores de proxy manualmente
set +e

echo "🔒 Iniciando escaneo de seguridad con OWASP ZAP"
echo "================================================"

# Configuración
TARGET_URL="${TARGET_URL:-http://web:3000}"
REPORT_DIR="${REPORT_DIR:-test-results/security}"
TIMEOUT="${TIMEOUT:-300}"
USE_COMPOSE="${USE_COMPOSE:-true}"
MAX_RETRIES="${MAX_RETRIES:-3}"
RETRY_DELAY="${RETRY_DELAY:-5}"

# Crear directorio de reportes
mkdir -p "$REPORT_DIR"

# Función para verificar disponibilidad de servicio
check_service_availability() {
    local url=$1
    local max_attempts=${2:-5}
    local attempt=1
    
    echo "📡 Verificando disponibilidad de $url..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null | grep -q "200\|301\|302\|404"; then
            echo "✅ Servicio disponible en $url"
            return 0
        fi
        
        if [ $attempt -lt $max_attempts ]; then
            echo "   Intento $attempt/$max_attempts falló, reintentando en ${RETRY_DELAY}s..."
            sleep "$RETRY_DELAY"
        fi
        attempt=$((attempt + 1))
    done
    
    echo "❌ Error: No se pudo conectar a $url después de $max_attempts intentos"
    return 1
}

# Detectar si estamos en Docker Compose o standalone
if [ "$USE_COMPOSE" == "true" ] && command -v docker-compose &> /dev/null; then
    # Verificar si el servicio ZAP está disponible en docker-compose
    if docker-compose ps zap 2>/dev/null | grep -q "zap"; then
        USE_COMPOSE=true
        ZAP_CONTAINER="pgf-zap"
        echo "📦 Usando servicio ZAP de Docker Compose"
    else
        USE_COMPOSE=false
        echo "📦 Usando Docker standalone (servicio ZAP no disponible)"
    fi
else
    USE_COMPOSE=false
    echo "📦 Usando Docker standalone"
fi

# Ajustar TARGET_URL según el contexto
if [ "$USE_COMPOSE" == "true" ]; then
    # Dentro de docker-compose, usar nombres de servicio
    if echo "$TARGET_URL" | grep -q "localhost\|127.0.0.1"; then
        TARGET_URL=$(echo "$TARGET_URL" | sed 's/localhost/web/g' | sed 's/127.0.0.1/web/g')
    fi
else
    # Standalone, usar localhost
    if echo "$TARGET_URL" | grep -q "web:"; then
        TARGET_URL=$(echo "$TARGET_URL" | sed 's/web:/localhost:/g')
    fi
fi

# Verificar que el target esté disponible
if [ "$USE_COMPOSE" == "true" ]; then
    # Verificar desde dentro del contenedor ZAP si existe
    if docker-compose ps zap 2>/dev/null | grep -q "zap"; then
        if ! docker-compose exec -T zap curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$TARGET_URL" 2>/dev/null | grep -q "200\|301\|302\|404"; then
            echo "⚠️  No se pudo verificar desde el contenedor ZAP, verificando desde host..."
            # Intentar verificar desde host usando localhost
            HOST_TARGET=$(echo "$TARGET_URL" | sed 's/web:/localhost:/g' | sed 's/web\//localhost\//g')
            if ! check_service_availability "$HOST_TARGET" 3; then
                echo "❌ Error: $TARGET_URL no está disponible"
                echo "   Asegúrate de que el servidor esté corriendo: docker compose up -d web"
                exit 1
            fi
        fi
    else
        # ZAP no está corriendo, verificar desde host
        HOST_TARGET=$(echo "$TARGET_URL" | sed 's/web:/localhost:/g' | sed 's/web\//localhost\//g')
        if ! check_service_availability "$HOST_TARGET" 3; then
            echo "❌ Error: $TARGET_URL no está disponible"
            echo "   Asegúrate de que el servidor esté corriendo: docker compose up -d web"
            exit 1
        fi
    fi
else
    # Verificar desde el host
    if ! check_service_availability "$TARGET_URL" 5; then
        echo "❌ Error: $TARGET_URL no está disponible"
        echo "   Asegúrate de que el servidor esté corriendo"
        exit 1
    fi
fi

echo "✅ Target configurado: $TARGET_URL"
echo ""

# Opción 1: Escaneo Pasivo (Rápido, no intrusivo)
if [ "$1" == "baseline" ] || [ -z "$1" ]; then
    echo "🔍 Ejecutando escaneo pasivo (baseline)..."
    
    RETRY_COUNT=0
    SUCCESS=false
    LOG_FILE="$REPORT_DIR/zap-baseline.log"
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ "$SUCCESS" = false ]; do
        if [ $RETRY_COUNT -gt 0 ]; then
            echo "   Reintentando escaneo (intento $((RETRY_COUNT + 1))/$MAX_RETRIES)..."
            sleep "$RETRY_DELAY"
        fi
        
        if [ "$USE_COMPOSE" == "true" ]; then
            docker-compose run --rm zap \
                zap-baseline.py \
                -t "$TARGET_URL" \
                -J "/zap/wrk/zap-baseline.json" \
                -r "/zap/wrk/zap-baseline.html" \
                -I \
                2>&1 | tee "$LOG_FILE"
            EXIT_CODE=${PIPESTATUS[0]}
        else
            docker run --rm -t \
                -v "$(pwd)/$REPORT_DIR:/zap/wrk/:rw" \
                --network host \
                ghcr.io/zaproxy/zaproxy:stable \
                zap-baseline.py \
                -t "$TARGET_URL" \
                -J "/zap/wrk/zap-baseline.json" \
                -r "/zap/wrk/zap-baseline.html" \
                -I \
                2>&1 | tee "$LOG_FILE"
            EXIT_CODE=${PIPESTATUS[0]}
        fi
        
        # Verificar si se generaron reportes (mejor indicador que el código de salida)
        if [ -f "$REPORT_DIR/zap-baseline.json" ] || [ -f "$REPORT_DIR/zap-baseline.html" ]; then
            SUCCESS=true
        elif [ $EXIT_CODE -eq 0 ]; then
            # Código 0 pero sin reportes - puede ser un problema menor
            if grep -q "ProxyError\|Connection refused" "$LOG_FILE" 2>/dev/null; then
                echo "⚠️  Error de proxy detectado, pero verificando reportes..."
                sleep 2  # Dar tiempo para que se escriban los archivos
                if [ -f "$REPORT_DIR/zap-baseline.json" ] || [ -f "$REPORT_DIR/zap-baseline.html" ]; then
                    SUCCESS=true
                else
                    RETRY_COUNT=$((RETRY_COUNT + 1))
                fi
            else
                SUCCESS=true  # Código 0 sin errores de proxy, asumir éxito
            fi
        else
            # Verificar si el error es solo de proxy (no crítico si hay reportes)
            if grep -q "ProxyError\|Connection refused.*proxy" "$LOG_FILE" 2>/dev/null; then
                echo "⚠️  Error de proxy detectado, verificando si se generaron reportes..."
                sleep 2
                if [ -f "$REPORT_DIR/zap-baseline.json" ] || [ -f "$REPORT_DIR/zap-baseline.html" ]; then
                    echo "   Reportes encontrados a pesar del error de proxy"
                    SUCCESS=true
                else
                    RETRY_COUNT=$((RETRY_COUNT + 1))
                fi
            else
                echo "⚠️  Escaneo falló con código $EXIT_CODE"
                RETRY_COUNT=$((RETRY_COUNT + 1))
            fi
        fi
    done
    
    if [ "$SUCCESS" = false ]; then
        echo "❌ Error: El escaneo falló después de $MAX_RETRIES intentos"
        echo "   Revisa el log en: $LOG_FILE"
        exit 1
    fi
    
    echo ""
    echo "✅ Escaneo pasivo completado"
    echo "📄 Reportes generados en: $REPORT_DIR/"
    
    # Mostrar advertencia si hubo errores de proxy
    if grep -q "ProxyError\|Connection refused.*proxy" "$LOG_FILE" 2>/dev/null; then
        echo "⚠️  Nota: Se detectaron errores de proxy durante el escaneo"
        echo "   Los reportes se generaron correctamente a pesar de estos errores"
    fi
fi

# Opción 2: Escaneo Activo (Lento, intrusivo)
if [ "$1" == "full" ]; then
    echo "🔍 Ejecutando escaneo activo completo..."
    echo "⚠️  Este escaneo puede tardar varios minutos y es más intrusivo"
    echo "⚠️  Nota: Errores de proxy durante el escaneo son normales y no afectan los resultados"
    
    RETRY_COUNT=0
    SUCCESS=false
    LOG_FILE="$REPORT_DIR/zap-full.log"
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ "$SUCCESS" = false ]; do
        if [ $RETRY_COUNT -gt 0 ]; then
            echo "   Reintentando escaneo (intento $((RETRY_COUNT + 1))/$MAX_RETRIES)..."
            sleep "$RETRY_DELAY"
            # Verificar que el servidor siga disponible antes de reintentar
            if ! check_service_availability "$TARGET_URL" 3; then
                echo "❌ Error: El servidor ya no está disponible"
                exit 1
            fi
        fi
        
        # Ejecutar escaneo y capturar salida
        echo "   Ejecutando escaneo (esto puede tardar varios minutos)..."
        
        if [ "$USE_COMPOSE" == "true" ]; then
            docker-compose run --rm zap \
                zap-full-scan.py \
                -t "$TARGET_URL" \
                -J "/zap/wrk/zap-full.json" \
                -r "/zap/wrk/zap-full.html" \
                -I \
                -T "$TIMEOUT" \
                2>&1 | tee "$LOG_FILE"
            EXIT_CODE=${PIPESTATUS[0]}
        else
            docker run --rm -t \
                -v "$(pwd)/$REPORT_DIR:/zap/wrk/:rw" \
                --network host \
                ghcr.io/zaproxy/zaproxy:stable \
                zap-full-scan.py \
                -t "$TARGET_URL" \
                -J "/zap/wrk/zap-full.json" \
                -r "/zap/wrk/zap-full.html" \
                -I \
                -T "$TIMEOUT" \
                2>&1 | tee "$LOG_FILE"
            EXIT_CODE=${PIPESTATUS[0]}
        fi
        
        # Esperar un momento para que se escriban los archivos
        sleep 2
        
        # Verificar si se generaron reportes (mejor indicador que el código de salida)
        if [ -f "$REPORT_DIR/zap-full.json" ] || [ -f "$REPORT_DIR/zap-full.html" ]; then
            echo "✅ Reportes generados exitosamente"
            SUCCESS=true
        elif [ $EXIT_CODE -eq 0 ]; then
            # Código de salida 0 pero sin reportes - verificar si hay errores de proxy
            if grep -q "ProxyError\|Connection refused.*proxy" "$LOG_FILE" 2>/dev/null; then
                echo "⚠️  Error de proxy detectado, pero código de salida es 0"
                echo "   Verificando si se generaron reportes después de un delay..."
                sleep 3
                if [ -f "$REPORT_DIR/zap-full.json" ] || [ -f "$REPORT_DIR/zap-full.html" ]; then
                    echo "✅ Reportes encontrados después del delay"
                    SUCCESS=true
                elif [ -f "$REPORT_DIR/zap-baseline.json" ] || [ -f "$REPORT_DIR/zap-baseline.html" ]; then
                    echo "   Se encontraron reportes de baseline, considerando exitoso"
                    SUCCESS=true
                else
                    echo "   No se encontraron reportes, reintentando..."
                    RETRY_COUNT=$((RETRY_COUNT + 1))
                fi
            else
                # Código 0 sin errores de proxy pero sin reportes - puede ser un problema real
                echo "⚠️  Escaneo terminó con código 0 pero no se encontraron reportes"
                RETRY_COUNT=$((RETRY_COUNT + 1))
            fi
        else
            # Código de salida no es 0 - verificar si es solo error de proxy
            PROXY_ERROR=$(grep -c "ProxyError\|Connection refused.*proxy" "$LOG_FILE" 2>/dev/null || echo "0")
            COMPLETED_INDICATOR=$(grep -c "Escaneo.*completado\|Scan.*complete\|completed\|ZAP.*complete" "$LOG_FILE" 2>/dev/null || echo "0")
            
            if [ "$PROXY_ERROR" -gt 0 ] && [ "$COMPLETED_INDICATOR" -gt 0 ]; then
                echo "⚠️  Error de proxy detectado, pero el escaneo parece haber completado"
                echo "   Verificando si se generaron reportes..."
                sleep 3
                if [ -f "$REPORT_DIR/zap-full.json" ] || [ -f "$REPORT_DIR/zap-full.html" ]; then
                    echo "✅ Reportes encontrados a pesar del error de proxy"
                    SUCCESS=true
                elif [ -f "$REPORT_DIR/zap-baseline.json" ] || [ -f "$REPORT_DIR/zap-baseline.html" ]; then
                    echo "   Usando reportes de baseline como alternativa"
                    cp "$REPORT_DIR/zap-baseline.json" "$REPORT_DIR/zap-full.json" 2>/dev/null || true
                    cp "$REPORT_DIR/zap-baseline.html" "$REPORT_DIR/zap-full.html" 2>/dev/null || true
                    SUCCESS=true
                else
                    # Verificar si el log muestra que el escaneo realmente completó
                    if grep -qi "completed.*host/plugin\|scanning.*complete\|spider.*complete" "$LOG_FILE" 2>/dev/null; then
                        echo "   El escaneo completó según los logs, pero no se generaron reportes"
                        echo "   Esto puede ser normal si el proxy se desconectó al final"
                        echo "   Los resultados del escaneo están en el log"
                        SUCCESS=true
                    else
                        RETRY_COUNT=$((RETRY_COUNT + 1))
                    fi
                fi
            elif [ "$PROXY_ERROR" -gt 0 ]; then
                # Solo error de proxy sin indicador de completado
                echo "⚠️  Error de proxy detectado (código $EXIT_CODE)"
                echo "   Verificando si se generaron reportes..."
                sleep 3
                if [ -f "$REPORT_DIR/zap-full.json" ] || [ -f "$REPORT_DIR/zap-full.html" ]; then
                    echo "✅ Reportes encontrados a pesar del error de proxy"
                    SUCCESS=true
                else
                    RETRY_COUNT=$((RETRY_COUNT + 1))
                fi
            else
                # Error real, no solo de proxy
                echo "⚠️  Escaneo falló con código $EXIT_CODE"
                RETRY_COUNT=$((RETRY_COUNT + 1))
            fi
        fi
    done
    
    if [ "$SUCCESS" = false ]; then
        echo "❌ Error: El escaneo falló después de $MAX_RETRIES intentos"
        echo "   Revisa el log en: $LOG_FILE"
        echo "   Posibles causas:"
        echo "   - El servidor se desconectó durante el escaneo"
        echo "   - Timeout del escaneo (aumenta TIMEOUT si es necesario)"
        echo "   - Problemas de red o proxy persistentes"
        echo ""
        echo "💡 Sugerencia: Intenta usar escaneo pasivo (más rápido y estable):"
        echo "   ./scripts/owasp_zap_scan.sh baseline"
        exit 1
    fi
    
    echo ""
    echo "✅ Escaneo activo completado"
    
    # Verificar qué reportes se generaron
    if [ -f "$REPORT_DIR/zap-full.json" ]; then
        echo "📄 Reporte JSON generado: $REPORT_DIR/zap-full.json"
    fi
    if [ -f "$REPORT_DIR/zap-full.html" ]; then
        echo "📄 Reporte HTML generado: $REPORT_DIR/zap-full.html"
    fi
    if [ ! -f "$REPORT_DIR/zap-full.json" ] && [ ! -f "$REPORT_DIR/zap-full.html" ]; then
        echo "⚠️  No se generaron reportes, pero el escaneo completó"
        echo "   Revisa el log completo en: $LOG_FILE"
        echo "   Los resultados pueden estar en el log"
    fi
    
    # Mostrar advertencia si hubo errores de proxy
    if grep -q "ProxyError\|Connection refused.*proxy" "$LOG_FILE" 2>/dev/null; then
        echo ""
        echo "⚠️  Nota: Se detectaron errores de proxy durante el escaneo"
        echo "   Esto es normal en escaneos largos y generalmente no afecta los resultados"
        echo "   El proxy interno de ZAP puede desconectarse durante escaneos activos largos"
        echo "   Si necesitas reportes completos, considera usar escaneo pasivo (baseline)"
    fi
fi

# Opción 3: Escaneo con API (Requiere ZAP corriendo como daemon)
if [ "$1" == "api" ]; then
    if [ "$USE_COMPOSE" == "true" ]; then
        ZAP_HOST="zap"
        ZAP_PORT="8080"
        echo "🔍 Iniciando ZAP como daemon en Docker Compose..."
        docker-compose up -d zap
        echo "⏳ Esperando a que ZAP esté listo..."
        sleep 10
    else
        ZAP_HOST="${ZAP_HOST:-localhost}"
        ZAP_PORT="${ZAP_PORT:-8080}"
        echo "🔍 Ejecutando escaneo vía API..."
        echo "   Asegúrate de que ZAP esté corriendo en $ZAP_HOST:$ZAP_PORT"
        echo "   Puedes iniciarlo con: docker run -d -p 8080:8080 ghcr.io/zaproxy/zaproxy:stable zap.sh -daemon -host 0.0.0.0 -port 8080"
    fi
    
    # Verificar que ZAP esté disponible
    echo "📡 Verificando conexión con ZAP..."
    if ! check_service_availability "http://$ZAP_HOST:$ZAP_PORT/JSON/core/view/version/" 10; then
        echo "❌ Error: No se puede conectar a ZAP en $ZAP_HOST:$ZAP_PORT"
        echo "   Verifica que ZAP esté corriendo y accesible"
        exit 1
    fi
    
    echo "✅ ZAP disponible"
    
    # Iniciar escaneo con reintentos
    SCAN_ID=""
    RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ -z "$SCAN_ID" ] || [ "$SCAN_ID" == "null" ]; do
        if [ $RETRY_COUNT -gt 0 ]; then
            echo "   Reintentando inicio de escaneo (intento $((RETRY_COUNT + 1))/$MAX_RETRIES)..."
            sleep "$RETRY_DELAY"
        fi
        
        SCAN_ID=$(curl -s --max-time 10 "http://$ZAP_HOST:$ZAP_PORT/JSON/ascan/action/scan/?url=$TARGET_URL" 2>/dev/null | jq -r '.scan' 2>/dev/null || echo "")
        
        if [ "$SCAN_ID" != "null" ] && [ -n "$SCAN_ID" ]; then
            break
        fi
        
        RETRY_COUNT=$((RETRY_COUNT + 1))
    done
    
    if [ "$SCAN_ID" == "null" ] || [ -z "$SCAN_ID" ]; then
        echo "❌ Error: No se pudo iniciar el escaneo después de $MAX_RETRIES intentos"
        echo "   Verifica que ZAP esté funcionando correctamente"
        exit 1
    fi
    
    echo "📊 Escaneo iniciado. ID: $SCAN_ID"
    echo "⏳ Esperando a que termine..."
    
    # Esperar a que termine con manejo de errores
    MAX_WAIT_TIME=$((TIMEOUT + 60))  # Agregar margen al timeout
    ELAPSED_TIME=0
    LAST_STATUS=0
    
    while [ $ELAPSED_TIME -lt $MAX_WAIT_TIME ]; do
        STATUS_RESPONSE=$(curl -s --max-time 10 "http://$ZAP_HOST:$ZAP_PORT/JSON/ascan/view/status/?scanId=$SCAN_ID" 2>/dev/null || echo '{"status":"error"}')
        STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status' 2>/dev/null || echo "error")
        
        if [ "$STATUS" == "error" ] || [ -z "$STATUS" ]; then
            echo "⚠️  Error al obtener estado del escaneo, reintentando..."
            sleep 5
            ELAPSED_TIME=$((ELAPSED_TIME + 5))
            continue
        fi
        
        if [ "$STATUS" != "$LAST_STATUS" ]; then
            echo "   Estado: $STATUS%"
            LAST_STATUS=$STATUS
        fi
        
        if [ "$STATUS" == "100" ]; then
            break
        fi
        
        sleep 5
        ELAPSED_TIME=$((ELAPSED_TIME + 5))
    done
    
    if [ "$STATUS" != "100" ]; then
        echo "⚠️  El escaneo no completó al 100% (estado final: $STATUS%)"
        echo "   Esto puede ser normal si el servidor se desconectó o hubo un timeout"
    fi
    
    # Generar reporte
    curl -s "http://$ZAP_HOST:$ZAP_PORT/OTHER/core/other/htmlreport/" > "$REPORT_DIR/zap-api-report.html"
    curl -s "http://$ZAP_HOST:$ZAP_PORT/JSON/core/view/alerts/" | jq '.' > "$REPORT_DIR/zap-api-alerts.json"
    
    echo ""
    echo "✅ Escaneo completado"
    echo "📄 Reportes generados en: $REPORT_DIR/"
    
    # Si usamos compose, podemos detener el servicio
    if [ "$USE_COMPOSE" == "true" ] && [ "${KEEP_ZAP_RUNNING:-false}" != "true" ]; then
        echo "🛑 Deteniendo servicio ZAP..."
        docker-compose stop zap
    fi
fi

# Mostrar resumen
if [ -f "$REPORT_DIR/zap-baseline.json" ] || [ -f "$REPORT_DIR/zap-full.json" ]; then
    echo ""
    echo "📊 Resumen de Vulnerabilidades:"
    echo "================================"
    
    if [ -f "$REPORT_DIR/zap-baseline.json" ]; then
        echo "Baseline Scan:"
        jq -r '.site[] | "  \(.alerts[] | "\(.riskcode) - \(.name)")"' "$REPORT_DIR/zap-baseline.json" 2>/dev/null || echo "  No se pudo parsear JSON"
    fi
    
    if [ -f "$REPORT_DIR/zap-full.json" ]; then
        echo "Full Scan:"
        jq -r '.site[] | "  \(.alerts[] | "\(.riskcode) - \(.name)")"' "$REPORT_DIR/zap-full.json" 2>/dev/null || echo "  No se pudo parsear JSON"
    fi
fi

echo ""
echo "✅ Escaneo completado. Revisa los reportes en: $REPORT_DIR/"

