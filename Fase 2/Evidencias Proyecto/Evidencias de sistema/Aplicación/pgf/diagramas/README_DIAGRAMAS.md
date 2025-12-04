# 📊 Diagramas de Flujo de Trabajo OT - Guía de Uso

Este documento explica cómo visualizar los diagramas del flujo de trabajo de una OT en diferentes plataformas.

## 📁 Archivos Disponibles

Todos los archivos están en la carpeta `diagramas/`:

1. **`diagramas-mermaid-para-notion.md`** - Código Mermaid listo para copiar a Notion
2. **`visualizar-diagramas.html`** - Archivo HTML interactivo para abrir en el navegador
3. **`DIAGRAMA_FLUJO_TRABAJO_OT.md`** - Documentación completa en texto
4. **`DIAGRAMA_FLUJO_TRABAJO_OT_MERMAID.md`** - Versión con diagramas Mermaid
5. **`README_DIAGRAMAS.md`** - Esta guía de uso

## 🎯 Opciones para Visualizar

### 1. Notion (Recomendado)

**Pasos:**
1. Abre Notion y crea una nueva página
2. Escribe `/code` o `/mermaid` para crear un bloque de código
3. Selecciona el lenguaje **"Mermaid"**
4. Abre el archivo `diagramas-mermaid-para-notion.md`
5. Copia el código del diagrama que quieras (está entre bloques de código)
6. Pégalo en el bloque de código de Notion
7. Notion renderizará el diagrama automáticamente

**Ventajas:**
- ✅ Renderizado automático
- ✅ Colores y estilos preservados
- ✅ Fácil de compartir
- ✅ Editable directamente en Notion

### 2. Navegador Web (HTML)

**Pasos:**
1. Abre el archivo `diagramas/visualizar-diagramas.html` en tu navegador
2. Los diagramas se renderizarán automáticamente
3. Puedes hacer zoom con Ctrl + Rueda del mouse
4. Todos los diagramas están en una sola página con navegación

**Ventajas:**
- ✅ No requiere conexión a internet (después de cargar Mermaid.js)
- ✅ Todos los diagramas en un solo lugar
- ✅ Interactivo y fácil de navegar
- ✅ Funciona offline después de la primera carga

### 3. Mermaid Live Editor

**Pasos:**
1. Ve a [https://mermaid.live/](https://mermaid.live/)
2. Abre el archivo `diagramas/diagramas-mermaid-para-notion.md`
3. Copia el código del diagrama que quieras
4. Pégalo en el editor
5. El diagrama se renderizará en tiempo real

**Ventajas:**
- ✅ Previsualización instantánea
- ✅ Puedes editar y experimentar
- ✅ Exporta como PNG o SVG
- ✅ Comparte con URL

### 4. GitHub

**Pasos:**
1. Sube los archivos `.md` a tu repositorio
2. GitHub renderiza automáticamente los bloques Mermaid
3. Los diagramas se verán directamente en el README o en los archivos `.md`

**Ventajas:**
- ✅ Integrado con tu repositorio
- ✅ Renderizado automático
- ✅ Fácil de compartir con el equipo

### 5. VS Code (Con extensión)

**Pasos:**
1. Instala la extensión "Markdown Preview Mermaid Support"
2. Abre cualquier archivo `.md` con diagramas Mermaid
3. Usa la vista previa de Markdown (Ctrl+Shift+V)
4. Los diagramas se renderizarán

**Ventajas:**
- ✅ Integrado en tu editor
- ✅ Edición y visualización simultánea
- ✅ Útil para desarrollo

## 📋 Diagramas Disponibles

1. **Diagrama Completo (3 Capas)** - Vista general del sistema
2. **Diagrama de Estados** - Transiciones de estado de una OT
3. **Diagrama de Secuencia** - Interacciones temporales
4. **Diagrama de Componentes** - Arquitectura por capas
5. **Flujo de Creación de OT** - Proceso de creación
6. **Flujo de Subida de Evidencia** - Proceso de subida de archivos
7. **Flujo de Generación de PDF** - Proceso asíncrono de PDF
8. **Arquitectura Completa** - Vista general del sistema

## 🔧 Solución de Problemas

### Notion no renderiza el diagrama
- Asegúrate de seleccionar el lenguaje "Mermaid" en el bloque de código
- Verifica que el código esté completo (sin cortes)
- Prueba con un diagrama más simple primero

### El HTML no muestra los diagramas
- Verifica que tengas conexión a internet (para cargar Mermaid.js)
- Abre la consola del navegador (F12) para ver errores
- Prueba en otro navegador (Chrome, Firefox, Edge)

### Los diagramas se ven pequeños
- En Notion: Haz clic en el diagrama para expandirlo
- En HTML: Usa Ctrl + Rueda del mouse para hacer zoom
- En Mermaid Live: Usa el botón de zoom en el editor

## 💡 Tips

- **Para presentaciones**: Usa Mermaid Live Editor para exportar como PNG
- **Para documentación**: Usa Notion para tener todo centralizado
- **Para desarrollo**: Usa VS Code con la extensión
- **Para compartir rápido**: Usa el HTML y compártelo por email o Drive

## 📚 Recursos Adicionales

- [Documentación oficial de Mermaid](https://mermaid.js.org/)
- [Mermaid Live Editor](https://mermaid.live/)
- [Notion - Bloques de código](https://www.notion.so/help/code-blocks)

## 🎨 Personalización

Si quieres modificar los colores o estilos:

1. **En Notion**: Edita el código Mermaid directamente
2. **En HTML**: Modifica las variables `themeVariables` en el script
3. **En Mermaid Live**: Usa el panel de configuración

Los colores actuales son:
- 🔵 Azul claro: Capa de Presentación
- 🟡 Amarillo claro: Capa de Negocio
- 🟢 Verde claro: Capa de Datos

---

**¿Necesitas ayuda?** Revisa la documentación completa en `diagramas/DIAGRAMA_FLUJO_TRABAJO_OT.md`

