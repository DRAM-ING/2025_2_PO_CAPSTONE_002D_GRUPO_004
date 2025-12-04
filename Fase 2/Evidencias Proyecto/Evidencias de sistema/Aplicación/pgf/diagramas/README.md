# 📊 Diagramas del Proyecto PGF

Esta carpeta contiene todos los diagramas relacionados con el flujo de trabajo de las Órdenes de Trabajo (OT) del sistema PGF.

## 📁 Contenido

### Archivos Principales

1. **`DIAGRAMA_FLUJO_TRABAJO_OT.md`**
   - Documentación completa del flujo de trabajo
   - Incluye descripciones detalladas de cada proceso
   - Diagramas en formato texto ASCII

2. **`DIAGRAMA_FLUJO_TRABAJO_OT_MERMAID.md`**
   - Versión con diagramas en formato Mermaid
   - Listo para visualizar en GitHub o editores compatibles

3. **`diagramas-mermaid-para-notion.md`**
   - Código Mermaid listo para copiar y pegar
   - Optimizado para Notion
   - Incluye 8 diagramas diferentes

4. **`visualizar-diagramas.html`**
   - Archivo HTML interactivo
   - Abre directamente en el navegador
   - Todos los diagramas renderizados automáticamente

5. **`README_DIAGRAMAS.md`**
   - Guía completa de uso
   - Instrucciones para cada plataforma
   - Solución de problemas

## 🚀 Inicio Rápido

### Para Notion
1. Abre `diagramas-mermaid-para-notion.md`
2. Copia el código del diagrama que quieras
3. Pégalo en un bloque de código Mermaid en Notion

### Para Navegador
1. Abre `visualizar-diagramas.html` en tu navegador
2. Navega por los diagramas usando el índice

### Para GitHub
1. Los archivos `.md` se renderizan automáticamente
2. Los diagramas Mermaid se muestran directamente

## 📋 Diagramas Disponibles

1. **Diagrama Completo (3 Capas)** - Vista general del sistema
2. **Diagrama de Estados** - Transiciones de estado de una OT
3. **Diagrama de Secuencia** - Interacciones temporales
4. **Diagrama de Componentes** - Arquitectura por capas
5. **Flujo de Creación de OT** - Proceso de creación
6. **Flujo de Subida de Evidencia** - Proceso de subida de archivos
7. **Flujo de Generación de PDF** - Proceso asíncrono de PDF
8. **Arquitectura Completa** - Vista general del sistema

## 🎯 Capas del Sistema

- **🎨 Capa de Presentación**: Frontend Next.js, Cloudflare Tunnel
- **⚙️ Capa de Negocio**: API Django, Worker Celery, Celery Beat
- **💾 Capa de Datos**: PostgreSQL, LocalStack S3, Redis

## 📚 Más Información

Para instrucciones detalladas sobre cómo usar estos diagramas en diferentes plataformas, consulta `README_DIAGRAMAS.md`.

