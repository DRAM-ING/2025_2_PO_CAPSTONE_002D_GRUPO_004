# Manual de Usuario General - Plataforma de Gestión de Flota (PGF)

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Acceso al Sistema](#acceso-al-sistema)
3. [Interfaz Principal](#interfaz-principal)
4. [Módulos Principales](#módulos-principales)
5. [Funcionalidades Comunes](#funcionalidades-comunes)
6. [Sistema de Notificaciones](#sistema-de-notificaciones)
7. [Reportes](#reportes)
8. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## Introducción

La **Plataforma de Gestión de Flota (PGF)** es un sistema integral desarrollado para PepsiCo que permite gestionar toda la operación de mantenimiento y reparación de vehículos de la flota. El sistema incluye gestión de órdenes de trabajo, programación de mantenimientos, emergencias en ruta, choferes, inventario y reportes ejecutivos.

### Objetivos del Sistema

- Centralizar la gestión de la flota vehicular
- Optimizar los tiempos de mantenimiento y reparación
- Mejorar la trazabilidad de las operaciones
- Generar reportes y métricas en tiempo real
- Facilitar la comunicación entre diferentes roles

---

## Acceso al Sistema

### Requisitos

- Navegador web moderno (Chrome, Firefox, Edge, Safari)
- Conexión a internet estable
- Credenciales de acceso proporcionadas por el administrador

### Inicio de Sesión

1. Acceda a la URL del sistema proporcionada por su administrador
2. Ingrese su **correo electrónico** y **contraseña**
3. Haga clic en el botón **"Iniciar Sesión"**

### Recuperación de Contraseña

Si olvidó su contraseña:

1. En la pantalla de login, haga clic en **"¿Olvidaste tu contraseña?"**
2. Ingrese su correo electrónico
3. Revise su bandeja de entrada (y spam) para el enlace de recuperación
4. El enlace expira en 24 horas
5. Siga las instrucciones para crear una nueva contraseña

### Cambio de Contraseña

Para cambiar su contraseña mientras está logueado:

1. Haga clic en su perfil (esquina superior derecha)
2. Seleccione **"Configuración"** o **"Cambiar Contraseña"**
3. Ingrese su contraseña actual y la nueva contraseña
4. Confirme la nueva contraseña
5. Haga clic en **"Guardar"**

---

## Interfaz Principal

### Componentes de la Interfaz

#### 1. Barra Superior (Header)
- **Logo de PepsiCo**: Identificación del sistema
- **Menú de Notificaciones**: Icono de campana con contador de notificaciones no leídas
- **Perfil de Usuario**: Acceso a configuración y cierre de sesión

#### 2. Menú Lateral (Sidebar)
- Navegación principal del sistema
- Se colapsa/expande con el botón de menú
- Muestra solo las opciones disponibles según su rol

#### 3. Área de Contenido Principal
- Muestra la información y funcionalidades según la sección seleccionada
- Incluye filtros, búsquedas y acciones contextuales

### Navegación

- **Dashboard**: Vista general según su rol
- **Vehículos**: Gestión de la flota
- **Órdenes de Trabajo**: Gestión de mantenimientos
- **Programación**: Agenda de mantenimientos
- **Emergencias**: Gestión de emergencias en ruta
- **Choferes**: Gestión de conductores
- **Inventario**: Gestión de repuestos
- **Reportes**: Generación de reportes
- **Usuarios**: (Solo Admin) Gestión de usuarios

---

## Módulos Principales

### 1. Dashboard

El dashboard proporciona una vista general del estado del sistema según su rol:

- **Dashboard Ejecutivo**: KPIs en tiempo real, métricas de productividad, vehículos en taller
- **Dashboard Zona**: Vista para supervisores con información de su zona
- **Dashboard Taller**: Vista para jefes de taller con OTs activas y pendientes

### 2. Vehículos

Gestión completa de la flota vehicular:

#### Funcionalidades:
- **Listado de Vehículos**: Ver todos los vehículos con filtros por estado, tipo, zona, etc.
- **Crear Vehículo**: Registrar nuevo vehículo en la flota
- **Editar Vehículo**: Modificar información del vehículo
- **Historial**: Ver historial completo de mantenimientos y eventos
- **Ingreso al Taller**: Registrar ingreso de vehículo (rol Guardia)
- **Salida del Taller**: Registrar salida de vehículo (rol Guardia)
- **Ticket de Ingreso**: Generar PDF del ticket de ingreso

#### Información del Vehículo:
- Patente, VIN, Marca, Modelo, Año
- Tipo (Eléctrico, Diésel, Utilitario, etc.)
- Categoría (Reparto, Ventas, Respaldo)
- Estado (Activo, En Espera, En Mantenimiento, Baja)
- Zona, Sucursal, Site
- Supervisor asignado
- Kilometraje actual y promedio mensual
- Fechas de última y próxima revisión

### 3. Órdenes de Trabajo (OT)

Gestión del ciclo completo de mantenimiento:

#### Estados de la OT:
1. **ABIERTA**: Recién creada, pendiente de diagnóstico
2. **EN_DIAGNOSTICO**: Jefe de Taller realizando diagnóstico
3. **EN_EJECUCION**: Mecánico trabajando en la OT
4. **EN_PAUSA**: Trabajo pausado (manual o automática por colación)
5. **EN_QA**: En control de calidad
6. **RETRABAJO**: Requiere corrección después de QA
7. **CERRADA**: Finalizada exitosamente
8. **ANULADA**: Cancelada antes de completarse

#### Funcionalidades:
- **Crear OT**: Crear nueva orden de trabajo
- **Ver Detalle**: Ver información completa de la OT
- **Timeline**: Ver historial consolidado de cambios, comentarios y evidencias
- **Comentarios**: Agregar comentarios con menciones (@usuario)
- **Items de Trabajo**: Agregar repuestos y servicios
- **Presupuesto**: Crear y gestionar presupuestos
- **Evidencias**: Subir fotos y documentos (hasta 3GB por archivo)
- **Checklist QA**: Realizar control de calidad
- **Pausas**: Pausar/reanudar trabajo
- **Cerrar OT**: Finalizar orden de trabajo

#### Pausas Automáticas:
- El sistema pausa automáticamente las OTs en ejecución durante la colación (12:30 - 13:15)
- Las pausas se reanudan automáticamente al finalizar el horario

### 4. Programación

Gestión de agenda de mantenimientos preventivos:

#### Funcionalidades:
- **Crear Programación**: Programar mantenimiento para un vehículo
- **Ver Agenda**: Ver programaciones por fecha, zona, vehículo
- **Cupos Diarios**: Ver y gestionar cupos disponibles por día
- **Confirmar Programación**: Confirmar que el vehículo asistirá
- **Reprogramar**: Cambiar fecha de programación
- **Cancelar**: Cancelar programación

#### Estados:
- **PROGRAMADA**: Programada pero no confirmada
- **CONFIRMADA**: Confirmada por el coordinador
- **EN_PROCESO**: Vehículo ingresó al taller
- **COMPLETADA**: Mantenimiento completado
- **CANCELADA**: Cancelada
- **REPROGRAMADA**: Fecha cambiada

### 5. Emergencias en Ruta

Gestión de emergencias que requieren atención inmediata:

#### Flujo de Emergencia:
1. **SOLICITADA**: Emergencia solicitada
2. **APROBADA**: Aprobada por Jefe de Taller
3. **ASIGNADA**: Mecánico asignado
4. **EN_CAMINO**: Mecánico en camino
5. **EN_REPARACION**: Reparación en curso
6. **RESUELTA**: Emergencia resuelta
7. **CERRADA**: Cerrada y documentada

#### Funcionalidades:
- **Crear Emergencia**: Solicitar atención de emergencia
- **Aprobar/Rechazar**: (Jefe de Taller) Aprobar o rechazar solicitud
- **Asignar Mecánico**: (Supervisor) Asignar mecánico disponible
- **Actualizar Estado**: Actualizar estado de la emergencia
- **Ver Detalle**: Ver información completa de la emergencia

### 6. Choferes

Gestión de conductores y asignaciones:

#### Funcionalidades:
- **Listado de Choferes**: Ver todos los choferes
- **Crear Chofer**: Registrar nuevo chofer
- **Editar Chofer**: Modificar información del chofer
- **Asignar Vehículo**: Asignar vehículo a chofer
- **Historial de Asignaciones**: Ver historial de vehículos asignados
- **Vista Chofer**: (Rol Chofer) Ver estado de su vehículo asignado

### 7. Inventario

Gestión de repuestos y stock:

#### Funcionalidades:
- **Catálogo de Repuestos**: Ver y gestionar repuestos disponibles
- **Stock Actual**: Ver stock disponible por repuesto
- **Movimientos**: Ver historial de entradas y salidas
- **Solicitudes**: Gestionar solicitudes de repuestos desde OTs
- **Reorden**: Ver repuestos que necesitan reorden
- **Entradas**: Registrar entrada de repuestos al stock
- **Ajustes**: Ajustar stock manualmente

### 8. Reportes

Generación de reportes en PDF:

#### Tipos de Reportes:
1. **Estado de Flota (General)**: Estado general de todos los vehículos
2. **Órdenes de Trabajo**: Reporte de OTs por período
3. **Uso/Comportamiento Operativo**: Análisis de uso de vehículos
4. **Mantenimientos Recurrentes**: Vehículos con mantenimientos frecuentes
5. **Por Site/Zona/Supervisor**: Reportes filtrados por criterios
6. **Cumplimiento y Política**: Análisis de cumplimiento
7. **Inventario/Características**: Características de vehículos

#### Funcionalidades:
- **Seleccionar Tipo**: Elegir tipo de reporte
- **Filtrar por Fechas**: Seleccionar rango de fechas
- **Filtrar por Criterios**: Filtrar por zona, site, supervisor, etc.
- **Generar PDF**: Descargar reporte en formato PDF
- **Vista Previa**: Ver resumen antes de generar

---

## Funcionalidades Comunes

### Búsqueda y Filtros

La mayoría de las listas incluyen:

- **Búsqueda**: Campo de búsqueda para encontrar registros rápidamente
- **Filtros**: Filtros por estado, fecha, zona, etc.
- **Ordenamiento**: Ordenar por diferentes columnas
- **Paginación**: Navegar entre páginas de resultados

### Acciones en Lote

Algunas secciones permiten acciones en lote:

- Seleccionar múltiples registros
- Aplicar acciones a todos los seleccionados

### Exportación de Datos

- Exportar listados a Excel/CSV (según disponibilidad)
- Generar reportes en PDF

### Evidencias Fotográficas

- Subir múltiples archivos
- Tamaño máximo: 3GB por archivo
- Formatos soportados: Imágenes (JPG, PNG, etc.) y documentos (PDF)
- Las evidencias se almacenan en AWS S3
- Invalidación de evidencias con historial de versiones

---

## Sistema de Notificaciones

### Tipos de Notificaciones

El sistema envía notificaciones para:

- **OT Creada**: Nueva orden de trabajo creada
- **OT Asignada**: OT asignada a un mecánico
- **OT Cerrada**: OT finalizada
- **OT en Pausa**: OT pausada
- **OT en QA**: OT enviada a control de calidad
- **OT Aprobada/Rechazada**: Presupuesto aprobado o rechazado
- **Evidencia Subida**: Nueva evidencia agregada
- **Menciones**: Mencionado en un comentario (@usuario)
- **Emergencia**: Nueva emergencia o cambio de estado

### Configuración de Notificaciones

Puede configurar sus preferencias de notificaciones:

1. Haga clic en su perfil
2. Seleccione **"Configuración"**
3. Configure:
   - **Notificaciones por Email**: Recibir notificaciones por correo
   - **Notificaciones de Sonido**: Reproducir sonido al recibir notificación
   - **Notificaciones Push**: Recibir notificaciones del navegador

### Ver Notificaciones

- Haga clic en el icono de campana en la barra superior
- Verá todas sus notificaciones no leídas
- Haga clic en una notificación para marcarla como leída
- Puede marcar todas como leídas

---

## Reportes

### Acceso a Reportes

1. Navegue a **"Reportes"** en el menú lateral
2. Seleccione el tipo de reporte deseado
3. Configure los filtros (fechas, zona, site, etc.)
4. Haga clic en **"Generar Reporte"**
5. El PDF se descargará automáticamente

### Filtros Comunes

- **Rango de Fechas**: Fecha inicio y fecha fin
- **Zona**: Filtrar por zona geográfica
- **Site**: Filtrar por site específico
- **Supervisor**: Filtrar por supervisor
- **Estado**: Filtrar por estado de vehículo/OT

### Permisos de Reportes

- **Ejecutivos**: Acceso a todos los reportes
- **Supervisores**: Solo reportes de su zona/site
- **Guardias**: Sin acceso a reportes
- **Otros roles**: Según configuración

---

## Preguntas Frecuentes

### ¿Cómo creo una nueva OT?

1. Vaya a **"Órdenes de Trabajo"**
2. Haga clic en **"Nueva OT"**
3. Complete los campos obligatorios (vehículo, motivo, supervisor, etc.)
4. Haga clic en **"Guardar"**

### ¿Cómo subo evidencias a una OT?

1. Abra el detalle de la OT
2. Vaya a la pestaña **"Evidencias"**
3. Haga clic en **"Subir Evidencia"**
4. Seleccione los archivos (hasta 3GB cada uno)
5. Agregue descripción si es necesario
6. Haga clic en **"Subir"**

### ¿Cómo comento en una OT?

1. Abra el detalle de la OT
2. Vaya a la pestaña **"Comentarios"** o **"Timeline"**
3. Escriba su comentario
4. Puede mencionar usuarios con @usuario
5. Haga clic en **"Enviar"**

### ¿Cómo pauso una OT?

1. Abra el detalle de la OT
2. Si está en estado **EN_EJECUCION**, verá el botón **"Pausar"**
3. Seleccione el tipo de pausa y motivo
4. Haga clic en **"Confirmar"**
5. Para reanudar, haga clic en **"Reanudar"**

### ¿Cómo registro el ingreso de un vehículo?

1. Vaya a **"Vehículos"** → **"Ingreso"**
2. Busque el vehículo por patente, VIN o escanee el QR
3. Complete los datos (kilometraje, observaciones)
4. Opcionalmente suba evidencias fotográficas
5. Haga clic en **"Registrar Ingreso"**
6. Se generará automáticamente una OT

### ¿Cómo genero un ticket de ingreso?

1. Vaya a **"Vehículos"** → **"Ingresos de Hoy"**
2. Busque el ingreso deseado
3. Haga clic en **"Generar Ticket"** o el icono de PDF
4. El PDF se descargará automáticamente

### ¿Cómo solicito un repuesto?

1. Abra el detalle de una OT
2. Vaya a **"Items de Trabajo"**
3. Agregue un item de tipo **"REPUESTO"**
4. El sistema creará automáticamente una solicitud de repuesto
5. La solicitud será revisada por el encargado de bodega

### ¿Cómo veo mi historial de actividades?

1. Vaya a **"Órdenes de Trabajo"**
2. Abra el detalle de una OT
3. Vaya a la pestaña **"Timeline"**
4. Verá todos los eventos, comentarios y cambios de estado

### ¿Cómo cambio mi contraseña?

1. Haga clic en su perfil (esquina superior derecha)
2. Seleccione **"Configuración"**
3. Busque la sección **"Cambiar Contraseña"**
4. Ingrese su contraseña actual y la nueva
5. Haga clic en **"Guardar"**

### ¿Qué hago si no puedo iniciar sesión?

1. Verifique que su usuario esté activo (contacte al administrador)
2. Use la opción **"¿Olvidaste tu contraseña?"**
3. Revise su correo (incluida la carpeta de spam)
4. Si el problema persiste, contacte al administrador del sistema

---

## Soporte y Contacto

Para soporte técnico o consultas:

- **Email de Soporte**: [email de soporte]
- **Teléfono**: [teléfono de soporte]
- **Horario de Atención**: [horario]

---

## Glosario de Términos

- **OT**: Orden de Trabajo
- **VIN**: Vehicle Identification Number (Número de identificación del vehículo)
- **QA**: Quality Assurance (Control de Calidad)
- **SLA**: Service Level Agreement (Acuerdo de Nivel de Servicio)
- **TCT**: Bloqueo Temporal
- **Backup**: Vehículo de respaldo asignado cuando el principal está en taller
- **Site**: Ubicación física del vehículo
- **Zona**: Área geográfica de operación

---

**Última actualización**: [Fecha]
**Versión del Manual**: 1.0

