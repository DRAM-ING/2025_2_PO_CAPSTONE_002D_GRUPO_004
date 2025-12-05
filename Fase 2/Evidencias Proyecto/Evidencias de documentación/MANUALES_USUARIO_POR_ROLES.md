# Manuales de Usuario por Roles - Plataforma de Gestión de Flota (PGF)

Este documento contiene manuales específicos para cada rol del sistema. Cada rol tiene permisos y funcionalidades diferentes según sus responsabilidades.

## Índice de Manuales

1. [Administrador (ADMIN)](#1-administrador-admin)
2. [Guardia (GUARDIA)](#2-guardia-guardia)
3. [Mecánico (MECANICO)](#3-mecánico-mecanico)
4. [Supervisor Zonal (SUPERVISOR)](#4-supervisor-zonal-supervisor)
5. [Jefe de Taller (JEFE_TALLER)](#5-jefe-de-taller-jefe_taller)
6. [Coordinador de Zona (COORDINADOR_ZONA)](#6-coordinador-de-zona-coordinador_zona)
7. [Ejecutivo (EJECUTIVO)](#7-ejecutivo-ejecutivo)
8. [Sponsor (SPONSOR)](#8-sponsor-sponsor)
9. [Chofer (CHOFER)](#9-chofer-chofer)
10. [Administrativo de Taller (ADMINISTRATIVO_TALLER)](#10-administrativo-de-taller-administrativo_taller)
11. [Bodega / Encargado de Repuestos (BODEGA)](#11-bodega--encargado-de-repuestos-bodega)

---

## 1. Administrador (ADMIN)

### Descripción del Rol

El Administrador tiene acceso completo al sistema y puede realizar todas las operaciones. Es responsable de la configuración general, gestión de usuarios y supervisión de todas las operaciones.

### Permisos y Accesos

- ✅ Acceso completo a todos los módulos
- ✅ Gestión de usuarios (crear, editar, eliminar)
- ✅ Configuración del sistema
- ✅ Todos los reportes
- ✅ Auditoría completa
- ✅ Gestión de roles y permisos

### Funcionalidades Principales

#### Gestión de Usuarios

1. **Crear Usuario**:
   - Ir a **"Usuarios"** → **"Nuevo Usuario"**
   - Completar: nombre, email, RUT, rol, contraseña
   - Asignar rol según responsabilidades
   - Guardar

2. **Editar Usuario**:
   - Buscar usuario en la lista
   - Hacer clic en **"Editar"**
   - Modificar información necesaria
   - Guardar cambios

3. **Desactivar Usuario**:
   - Abrir detalle del usuario
   - Cambiar estado a **"Inactivo"**
   - El usuario no podrá iniciar sesión

4. **Cambiar Contraseña de Usuario**:
   - Abrir detalle del usuario
   - Ir a **"Cambiar Contraseña"**
   - Ingresar nueva contraseña
   - Confirmar

#### Supervisión General

- **Dashboard Ejecutivo**: Ver KPIs generales del sistema
- **Auditoría**: Revisar todas las acciones del sistema
- **Reportes**: Generar cualquier tipo de reporte
- **Configuración**: Ajustar parámetros del sistema

### Tareas Comunes

1. **Crear nuevos usuarios** cuando se incorpora personal
2. **Asignar roles** según responsabilidades
3. **Revisar auditoría** para detectar problemas
4. **Generar reportes ejecutivos** para la gerencia
5. **Resolver problemas de acceso** de usuarios

### Recomendaciones

- Revisar regularmente la auditoría del sistema
- Mantener usuarios inactivos desactivados
- No compartir credenciales de administrador
- Realizar backups regulares de la información

---

## 2. Guardia (GUARDIA)

### Descripción del Rol

El Guardia es responsable del control de ingreso y salida de vehículos al taller. Es el primer punto de contacto cuando un vehículo ingresa para mantenimiento.

### Permisos y Accesos

- ✅ Registrar ingreso de vehículos
- ✅ Registrar salida de vehículos
- ✅ Ver listado de vehículos
- ✅ Ver ingresos del día
- ✅ Generar tickets de ingreso
- ❌ No puede crear/editar OTs directamente
- ❌ No tiene acceso a reportes

### Funcionalidades Principales

#### Registrar Ingreso de Vehículo

1. **Acceso Rápido**:
   - Ir a **"Vehículos"** → **"Ingreso"**
   - O usar el acceso directo desde el dashboard

2. **Buscar Vehículo**:
   - Ingresar patente del vehículo
   - O escanear código QR
   - O buscar por VIN
   - El sistema mostrará el vehículo si existe

3. **Completar Datos de Ingreso**:
   - **Kilometraje actual**: Ingresar kilometraje del vehículo
   - **Observaciones**: Notas sobre el estado del vehículo
   - **Evidencias**: Subir fotos del vehículo (opcional)
   - **RUT Conductor**: Si aplica

4. **Confirmar Ingreso**:
   - Revisar información
   - Hacer clic en **"Registrar Ingreso"**
   - El sistema creará automáticamente una OT en estado **ABIERTA**

5. **Generar Ticket**:
   - Después del ingreso, hacer clic en **"Generar Ticket"**
   - Se descargará un PDF con la información del ingreso
   - Entregar copia al conductor

#### Registrar Salida de Vehículo

1. **Ver Vehículos Pendientes de Salida**:
   - Ir a **"Vehículos"** → **"Pendientes de Salida"**
   - Ver lista de vehículos que ingresaron pero no han salido

2. **Seleccionar Vehículo**:
   - Buscar el vehículo por patente
   - O seleccionar de la lista

3. **Completar Datos de Salida**:
   - **Kilometraje de salida**: Ingresar nuevo kilometraje
   - **Observaciones de salida**: Notas sobre el trabajo realizado
   - **Verificar OT cerrada**: Asegurarse que la OT esté cerrada

4. **Confirmar Salida**:
   - Revisar información
   - Hacer clic en **"Registrar Salida"**
   - El vehículo quedará disponible

#### Ver Ingresos del Día

- Ir a **"Vehículos"** → **"Ingresos de Hoy"**
- Ver todos los ingresos registrados hoy
- Filtrar por estado, vehículo, etc.
- Generar tickets de cualquier ingreso

### Flujo de Trabajo Típico

1. **Mañana**: Revisar vehículos programados para el día
2. **Durante el día**: Registrar ingresos conforme llegan vehículos
3. **Generar tickets**: Entregar comprobante a cada conductor
4. **Tarde**: Registrar salidas de vehículos que terminaron
5. **Fin del día**: Verificar que todos los ingresos tengan salida o estén pendientes

### Validaciones Importantes

- No se puede registrar ingreso si el vehículo ya tiene una OT activa
- El kilometraje de salida debe ser mayor o igual al de ingreso
- Se debe verificar que la OT esté cerrada antes de registrar salida

### Recomendaciones

- Registrar ingresos inmediatamente al llegar el vehículo
- Tomar fotos del estado del vehículo al ingreso
- Verificar que los datos estén correctos antes de confirmar
- Mantener los tickets organizados para referencia

---

## 3. Mecánico (MECANICO)

### Descripción del Rol

El Mecánico ejecuta las órdenes de trabajo asignadas. Es responsable de realizar el trabajo de mantenimiento o reparación, documentar el proceso y subir evidencias.

### Permisos y Accesos

- ✅ Ver OTs asignadas
- ✅ Ejecutar OTs (cambiar a EN_EJECUCION)
- ✅ Agregar items de trabajo (repuestos y servicios)
- ✅ Subir evidencias fotográficas
- ✅ Agregar comentarios
- ✅ Pausar/reanudar trabajo
- ✅ Ver vehículos asignados
- ❌ No puede crear OTs
- ❌ No puede cerrar OTs (requiere QA)
- ❌ No tiene acceso a reportes

### Funcionalidades Principales

#### Ver Mis OTs Asignadas

1. **Dashboard**:
   - Ver OTs asignadas en el dashboard
   - Ver estado de cada OT
   - Acceso rápido a OTs pendientes

2. **Listado de OTs**:
   - Ir a **"Órdenes de Trabajo"**
   - Filtrar por "Asignadas a mí"
   - Ver estado, vehículo, prioridad

#### Iniciar Trabajo en una OT

1. **Seleccionar OT**:
   - Abrir el detalle de la OT asignada
   - Verificar que esté en estado **EN_DIAGNOSTICO** o **EN_EJECUCION**

2. **Iniciar Ejecución**:
   - Si está en **EN_DIAGNOSTICO**, esperar que el Jefe de Taller la mueva a **EN_EJECUCION**
   - Si ya está en **EN_EJECUCION**, puede comenzar a trabajar

3. **Revisar Diagnóstico**:
   - Leer el diagnóstico realizado por el Jefe de Taller
   - Revisar items de trabajo sugeridos
   - Verificar presupuesto si aplica

#### Agregar Items de Trabajo

1. **Acceder a Items**:
   - En el detalle de la OT, ir a pestaña **"Items"**
   - Ver items existentes

2. **Agregar Nuevo Item**:
   - Hacer clic en **"Agregar Item"**
   - Seleccionar tipo: **REPUESTO** o **SERVICIO**
   - Completar:
     - Descripción
     - Cantidad
     - Costo unitario
   - Guardar

3. **Solicitar Repuesto**:
   - Si agrega un item de tipo **REPUESTO**, se crea automáticamente una solicitud
   - La solicitud será revisada por Bodega
   - Puede ver el estado de la solicitud

#### Subir Evidencias

1. **Acceder a Evidencias**:
   - En el detalle de la OT, ir a pestaña **"Evidencias"**
   - Ver evidencias existentes

2. **Subir Nueva Evidencia**:
   - Hacer clic en **"Subir Evidencia"**
   - Seleccionar archivo (hasta 3GB)
   - Agregar descripción
   - Seleccionar tipo (FOTO, PDF, DOCUMENTO, etc.)
   - Hacer clic en **"Subir"**

3. **Tipos de Evidencias**:
   - **Fotos del trabajo**: Antes, durante, después
   - **Documentos**: Facturas, garantías, etc.
   - **Otros**: Cualquier documento relevante

#### Agregar Comentarios

1. **Acceder a Comentarios**:
   - En el detalle de la OT, ir a pestaña **"Comentarios"** o **"Timeline"**

2. **Escribir Comentario**:
   - Escribir el comentario
   - Puede mencionar usuarios con @usuario
   - Hacer clic en **"Enviar"**

3. **Responder Comentarios**:
   - Hacer clic en **"Responder"** en un comentario existente
   - Escribir respuesta
   - Enviar

#### Pausar/Reanudar Trabajo

1. **Pausar Manualmente**:
   - Si necesita pausar el trabajo
   - Hacer clic en **"Pausar"**
   - Seleccionar tipo de pausa:
     - **ESPERA_REPUESTO**: Esperando repuesto
     - **APROBACION_PENDIENTE**: Esperando aprobación
     - **COLACION**: Pausa para colación (aunque es automática)
     - **OTRO**: Otra razón
   - Agregar motivo
   - Confirmar

2. **Reanudar**:
   - Cuando esté listo para continuar
   - Hacer clic en **"Reanudar"**
   - El trabajo continúa

**Nota**: El sistema pausa automáticamente de 12:30 a 13:15 para colación.

#### Finalizar Trabajo

1. **Completar Items**:
   - Asegurarse de que todos los items estén completados
   - Verificar que los repuestos solicitados fueron entregados

2. **Subir Evidencias Finales**:
   - Subir fotos del trabajo completado
   - Documentar cualquier observación

3. **Enviar a QA**:
   - El Jefe de Taller o Supervisor moverá la OT a **EN_QA**
   - Esperar resultado del control de calidad

4. **Si hay Retrabajo**:
   - Si QA encuentra problemas, la OT volverá a **EN_EJECUCION**
   - Corregir los problemas indicados
   - Volver a enviar a QA

### Flujo de Trabajo Típico

1. **Inicio del día**: Revisar OTs asignadas
2. **Seleccionar OT**: Elegir OT según prioridad
3. **Revisar diagnóstico**: Leer diagnóstico del Jefe de Taller
4. **Solicitar repuestos**: Si necesita repuestos, agregarlos como items
5. **Iniciar trabajo**: Comenzar el trabajo de mantenimiento/reparación
6. **Documentar**: Subir fotos durante el proceso
7. **Completar trabajo**: Finalizar todos los items
8. **Subir evidencias finales**: Documentar trabajo completado
9. **Esperar QA**: Esperar control de calidad

### Recomendaciones

- Revisar el diagnóstico antes de comenzar
- Documentar bien el proceso con fotos
- Comunicar problemas o dudas mediante comentarios
- Solicitar repuestos con anticipación
- Mantener las evidencias organizadas

---

## 4. Supervisor Zonal (SUPERVISOR)

### Descripción del Rol

El Supervisor Zonal supervisa las operaciones de su zona. Aprueba asignaciones, asigna mecánicos, gestiona emergencias y supervisa el cumplimiento de OTs.

### Permisos y Accesos

- ✅ Ver todas las OTs de su zona
- ✅ Aprobar asignaciones de mecánicos
- ✅ Asignar mecánicos a OTs
- ✅ Ver y gestionar vehículos de su zona
- ✅ Gestionar emergencias
- ✅ Ver reportes de su zona
- ✅ Ver dashboard zonal
- ❌ No puede crear OTs directamente
- ❌ No puede realizar diagnósticos
- ❌ No puede cerrar OTs

### Funcionalidades Principales

#### Dashboard Zonal

- **OTs por Estado**: Ver distribución de OTs
- **Vehículos en Taller**: Ver vehículos de su zona en taller
- **Emergencias Activas**: Ver emergencias pendientes
- **Métricas de Productividad**: KPIs de su zona

#### Gestionar OTs

1. **Ver OTs de Mi Zona**:
   - Ir a **"Órdenes de Trabajo"**
   - Filtrar por zona
   - Ver todas las OTs de vehículos de su zona

2. **Aprobar Asignación**:
   - Cuando el Jefe de Taller asigna un mecánico
   - Revisar la asignación
   - Aprobar o rechazar
   - Si rechaza, indicar motivo

3. **Asignar Mecánico**:
   - Seleccionar OT
   - Ir a **"Asignar Mecánico"**
   - Seleccionar mecánico disponible
   - Confirmar asignación

4. **Supervisar Progreso**:
   - Revisar timeline de OTs
   - Ver comentarios y evidencias
   - Intervenir si hay problemas

#### Gestionar Emergencias

1. **Ver Emergencias**:
   - Ir a **"Emergencias"**
   - Ver emergencias de su zona

2. **Asignar Mecánico a Emergencia**:
   - Seleccionar emergencia aprobada
   - Asignar mecánico disponible
   - Actualizar estado a **ASIGNADA**

3. **Seguimiento**:
   - Monitorear progreso de emergencias
   - Actualizar estados según corresponda

#### Gestionar Vehículos

- Ver vehículos de su zona
- Revisar historial de mantenimientos
- Asignar vehículos backup cuando sea necesario
- Gestionar bloqueos de vehículos

#### Reportes Zonales

- Generar reportes filtrados por su zona
- Ver métricas de cumplimiento
- Analizar tiempos de reparación

### Flujo de Trabajo Típico

1. **Inicio del día**: Revisar dashboard zonal
2. **Revisar OTs pendientes**: Ver OTs que requieren atención
3. **Aprobar asignaciones**: Revisar y aprobar asignaciones de mecánicos
4. **Gestionar emergencias**: Atender emergencias urgentes
5. **Supervisar progreso**: Revisar OTs en ejecución
6. **Fin del día**: Revisar reportes y métricas

### Recomendaciones

- Revisar asignaciones diariamente
- Priorizar emergencias
- Mantener comunicación con mecánicos
- Revisar reportes regularmente para identificar tendencias

---

## 5. Jefe de Taller (JEFE_TALLER)

### Descripción del Rol

El Jefe de Taller realiza diagnósticos, asigna mecánicos, aprueba emergencias y realiza control de calidad (QA). Es responsable técnico del taller.

### Permisos y Accesos

- ✅ Ver todas las OTs del taller
- ✅ Realizar diagnósticos
- ✅ Asignar mecánicos
- ✅ Aprobar/rechazar emergencias
- ✅ Realizar control de calidad (QA)
- ✅ Ver vehículos
- ✅ Ver reportes del taller
- ❌ No puede crear OTs directamente
- ❌ No puede cerrar OTs (requiere QA exitoso)

### Funcionalidades Principales

#### Realizar Diagnóstico

1. **Ver OTs en Diagnóstico**:
   - Ir a **"Órdenes de Trabajo"**
   - Filtrar por estado **EN_DIAGNOSTICO**
   - Ver OTs pendientes de diagnóstico

2. **Abrir OT**:
   - Seleccionar OT
   - Ver información del vehículo
   - Revisar motivo de ingreso
   - Ver evidencias de ingreso si las hay

3. **Realizar Diagnóstico**:
   - Ir a **"Diagnóstico"** en el detalle de la OT
   - Escribir diagnóstico detallado
   - Agregar items de trabajo sugeridos (repuestos y servicios)
   - Estimar tiempos
   - Guardar diagnóstico

4. **Mover a Ejecución**:
   - Después del diagnóstico, mover OT a **EN_EJECUCION**
   - Asignar mecánico
   - La asignación será revisada por Supervisor

#### Asignar Mecánico

1. **Seleccionar Mecánico**:
   - Ver mecánicos disponibles
   - Considerar carga de trabajo actual
   - Asignar según especialidad si aplica

2. **Confirmar Asignación**:
   - La asignación requiere aprobación del Supervisor
   - El Supervisor puede aprobar o rechazar

#### Control de Calidad (QA)

1. **Ver OTs en QA**:
   - Filtrar por estado **EN_QA**
   - Ver OTs que completaron el trabajo

2. **Revisar Trabajo**:
   - Abrir detalle de la OT
   - Revisar:
     - Items completados
     - Evidencias subidas
     - Comentarios del mecánico
     - Tiempos de ejecución

3. **Realizar Checklist QA**:
   - Ir a pestaña **"Checklist"**
   - Completar checklist de calidad
   - Marcar items como **OK** o **NO_OK**
   - Agregar observaciones

4. **Aprobar o Enviar a Retrabajo**:
   - Si todo está correcto: **Aprobar** → OT se cierra
   - Si hay problemas: **Enviar a Retrabajo** → OT vuelve a **EN_EJECUCION**

#### Aprobar Emergencias

1. **Ver Emergencias Solicitadas**:
   - Ir a **"Emergencias"**
   - Filtrar por estado **SOLICITADA**
   - Ver emergencias pendientes de aprobación

2. **Revisar Emergencia**:
   - Leer descripción
   - Verificar prioridad
   - Revisar ubicación y vehículo

3. **Aprobar o Rechazar**:
   - **Aprobar**: Emergencia pasa a estado **APROBADA**
   - **Rechazar**: Indicar motivo, emergencia se cierra

### Flujo de Trabajo Típico

1. **Inicio del día**: Revisar OTs en diagnóstico
2. **Realizar diagnósticos**: Diagnosticar vehículos que ingresaron
3. **Asignar mecánicos**: Asignar trabajo según disponibilidad
4. **Supervisar ejecución**: Revisar progreso de OTs
5. **Control de calidad**: Revisar OTs completadas
6. **Gestionar emergencias**: Aprobar/rechazar según urgencia

### Recomendaciones

- Realizar diagnósticos detallados
- Asignar mecánicos según especialidad
- Ser riguroso en el control de calidad
- Priorizar emergencias críticas

---

## 6. Coordinador de Zona (COORDINADOR_ZONA)

### Descripción del Rol

El Coordinador de Zona programa mantenimientos preventivos, gestiona la agenda y coordina los ingresos de vehículos al taller.

### Permisos y Accesos

- ✅ Programar mantenimientos
- ✅ Gestionar agenda
- ✅ Ver y gestionar cupos diarios
- ✅ Ver vehículos de su zona
- ✅ Gestionar emergencias
- ✅ Ver OTs de su zona
- ❌ No puede crear OTs directamente
- ❌ No puede ejecutar OTs

### Funcionalidades Principales

#### Programar Mantenimiento

1. **Crear Programación**:
   - Ir a **"Programación"** → **"Nueva Programación"**
   - Seleccionar vehículo
   - Seleccionar fecha y hora
   - Indicar tipo de mantenimiento (PREVENTIVO, CORRECTIVO, EMERGENCIA)
   - Agregar motivo
   - Seleccionar zona
   - Guardar

2. **Verificar Cupos**:
   - El sistema verifica disponibilidad de cupos
   - Si no hay cupos, sugerir otra fecha

3. **Confirmar Programación**:
   - Contactar con el conductor/supervisor
   - Confirmar asistencia
   - Cambiar estado a **CONFIRMADA**

#### Gestionar Agenda

1. **Ver Agenda**:
   - Ver programaciones por fecha
   - Filtrar por zona, vehículo, estado
   - Ver cupos ocupados y disponibles

2. **Reprogramar**:
   - Si el vehículo no puede asistir
   - Seleccionar programación
   - Cambiar fecha
   - Actualizar estado a **REPROGRAMADA**

3. **Cancelar**:
   - Si el mantenimiento ya no es necesario
   - Cambiar estado a **CANCELADA**

#### Gestionar Cupos Diarios

1. **Ver Cupos**:
   - Ir a **"Programación"** → **"Cupos"**
   - Ver cupos por día
   - Ver cupos ocupados y disponibles

2. **Ajustar Cupos**:
   - Modificar cupos totales si es necesario
   - Considerar capacidad del taller

#### Seguimiento de Programaciones

- Ver qué vehículos asistieron
- Ver qué vehículos no asistieron
- Analizar cumplimiento de programaciones

### Flujo de Trabajo Típico

1. **Planificación semanal**: Programar mantenimientos de la semana
2. **Confirmaciones**: Confirmar asistencia de vehículos
3. **Ajustes**: Reprogramar según necesidades
4. **Seguimiento**: Verificar cumplimiento
5. **Análisis**: Revisar métricas de programación

### Recomendaciones

- Programar con anticipación
- Confirmar asistencia antes del día
- Mantener comunicación con conductores
- Optimizar uso de cupos disponibles

---

## 7. Ejecutivo (EJECUTIVO)

### Descripción del Rol

El Ejecutivo tiene acceso a dashboards y reportes para análisis estratégico y toma de decisiones. Acceso de solo lectura a la mayoría de funcionalidades.

### Permisos y Accesos

- ✅ Dashboard ejecutivo completo
- ✅ Todos los reportes
- ✅ Ver OTs (solo lectura)
- ✅ Ver vehículos (solo lectura)
- ❌ No puede crear/editar OTs
- ❌ No puede crear/editar vehículos
- ❌ No puede gestionar usuarios

### Funcionalidades Principales

#### Dashboard Ejecutivo

1. **KPIs en Tiempo Real**:
   - OTs por estado
   - Productividad (7 días)
   - Vehículos en taller
   - Métricas de eficiencia
   - Tiempos promedio de reparación

2. **Gráficos**:
   - Evolución de OTs
   - Distribución por zona
   - Análisis de tendencias

#### Reportes Ejecutivos

1. **Generar Reportes**:
   - Ir a **"Reportes"**
   - Seleccionar tipo de reporte
   - Configurar filtros (fechas, zona, etc.)
   - Generar PDF

2. **Tipos de Reportes Disponibles**:
   - Estado de Flota (General)
   - Órdenes de Trabajo
   - Uso/Comportamiento Operativo
   - Mantenimientos Recurrentes
   - Por Site/Zona/Supervisor
   - Cumplimiento y Política
   - Inventario/Características

#### Análisis de Datos

- Ver métricas históricas
- Comparar períodos
- Identificar tendencias
- Analizar eficiencia

### Flujo de Trabajo Típico

1. **Inicio del día**: Revisar dashboard ejecutivo
2. **Análisis**: Revisar KPIs y métricas
3. **Reportes**: Generar reportes según necesidad
4. **Toma de decisiones**: Usar información para decisiones estratégicas

### Recomendaciones

- Revisar dashboard regularmente
- Generar reportes periódicos
- Analizar tendencias a largo plazo
- Compartir insights con el equipo

---

## 8. Sponsor (SPONSOR)

### Descripción del Rol

El Sponsor aprueba o rechaza presupuestos que exceden un umbral determinado. Acceso principalmente de solo lectura.

### Permisos y Accesos

- ✅ Ver OTs con presupuestos
- ✅ Aprobar/rechazar presupuestos
- ✅ Dashboard ejecutivo (solo lectura)
- ✅ Ver reportes
- ❌ No puede crear/editar OTs
- ❌ No puede crear/editar vehículos

### Funcionalidades Principales

#### Revisar Presupuestos

1. **Ver OTs con Presupuestos Pendientes**:
   - Ir a **"Órdenes de Trabajo"**
   - Filtrar por "Presupuesto pendiente"
   - Ver OTs que requieren aprobación

2. **Revisar Presupuesto**:
   - Abrir detalle de la OT
   - Ir a pestaña **"Presupuesto"**
   - Ver:
     - Total del presupuesto
     - Detalles (items, cantidades, precios)
     - Motivo de la OT
     - Diagnóstico

3. **Aprobar o Rechazar**:
   - **Aprobar**: Presupuesto aprobado, OT puede continuar
   - **Rechazar**: Indicar motivo, OT queda en espera

#### Dashboard

- Ver métricas generales
- Ver OTs pendientes de aprobación
- Ver presupuestos aprobados/rechazados

### Flujo de Trabajo Típico

1. **Revisar pendientes**: Ver presupuestos pendientes de aprobación
2. **Analizar**: Revisar detalles del presupuesto
3. **Decidir**: Aprobar o rechazar según criterios
4. **Comunicar**: Si rechaza, indicar motivo claro

### Recomendaciones

- Revisar presupuestos regularmente
- Ser claro en los motivos de rechazo
- Considerar urgencia de la OT
- Mantener comunicación con el equipo

---

## 9. Chofer (CHOFER)

### Descripción del Rol

El Chofer tiene acceso de solo lectura para ver el estado de su vehículo asignado y las OTs relacionadas. Rol principalmente pasivo.

### Permisos y Accesos

- ✅ Ver su vehículo asignado
- ✅ Ver OTs de su vehículo
- ✅ Ver notificaciones
- ✅ Descargar comprobantes de ingreso/salida
- ❌ No puede crear/editar nada
- ❌ No puede gestionar OTs

### Funcionalidades Principales

#### Ver Mi Vehículo

1. **Dashboard Chofer**:
   - Ver estado actual de su vehículo
   - Ver información básica (patente, marca, modelo)
   - Ver estado operativo

2. **Detalle del Vehículo**:
   - Ver información completa
   - Ver historial de mantenimientos
   - Ver próximas revisiones

#### Ver OTs de Mi Vehículo

1. **Listado de OTs**:
   - Ver todas las OTs de su vehículo
   - Ver estado de cada OT
   - Ver fechas de ingreso/salida

2. **Detalle de OT**:
   - Ver información de la OT
   - Ver comentarios (si tiene acceso)
   - Ver estado actual

#### Notificaciones

- Recibir notificaciones cuando:
  - Su vehículo ingresa al taller
  - Se crea una OT para su vehículo
  - La OT cambia de estado
  - Su vehículo sale del taller

#### Comprobantes

- Descargar ticket de ingreso
- Descargar comprobante de salida
- Ver historial de ingresos/salidas

### Flujo de Trabajo Típico

1. **Revisar estado**: Ver estado de su vehículo
2. **Revisar OTs**: Ver si hay OTs activas
3. **Notificaciones**: Revisar notificaciones importantes
4. **Comprobantes**: Descargar comprobantes cuando sea necesario

### Recomendaciones

- Revisar estado del vehículo regularmente
- Estar atento a notificaciones
- Guardar comprobantes importantes
- Comunicar problemas al supervisor

---

## 10. Administrativo de Taller (ADMINISTRATIVO_TALLER)

### Descripción del Rol

El Administrativo de Taller gestiona aspectos administrativos de las OTs, como presupuestos, facturación y documentación.

### Permisos y Accesos

- ✅ Ver y gestionar OTs
- ✅ Gestionar presupuestos
- ✅ Ver y gestionar evidencias
- ✅ Ver reportes administrativos
- ✅ Ver vehículos
- ❌ No puede ejecutar OTs
- ❌ No puede realizar diagnósticos

### Funcionalidades Principales

#### Gestionar Presupuestos

1. **Crear Presupuestos**:
   - Abrir detalle de OT
   - Ir a **"Presupuesto"**
   - Crear presupuesto basado en items de trabajo
   - Agregar detalles
   - Calcular total

2. **Enviar a Aprobación**:
   - Si el presupuesto excede el umbral
   - Enviar a aprobación del Sponsor
   - Seguir estado de aprobación

#### Gestionar Documentación

1. **Organizar Evidencias**:
   - Ver evidencias de OTs
   - Validar que estén completas
   - Organizar por OT

2. **Gestionar Facturas**:
   - Subir facturas como evidencias
   - Asociar facturas a items de trabajo
   - Mantener registro

#### Reportes Administrativos

- Generar reportes de costos
- Reportes de presupuestos
- Análisis de gastos por período

### Flujo de Trabajo Típico

1. **Revisar OTs**: Ver OTs que requieren atención administrativa
2. **Crear presupuestos**: Generar presupuestos cuando sea necesario
3. **Gestionar documentación**: Organizar evidencias y facturas
4. **Reportes**: Generar reportes administrativos

### Recomendaciones

- Mantener presupuestos actualizados
- Organizar documentación sistemáticamente
- Validar que las evidencias estén completas
- Generar reportes periódicos

---

## 11. Bodega / Encargado de Repuestos (BODEGA)

### Descripción del Rol

El Encargado de Bodega gestiona el inventario de repuestos, stock, movimientos y solicitudes de repuestos desde las OTs.

### Permisos y Accesos

- ✅ Gestionar catálogo de repuestos
- ✅ Gestionar stock
- ✅ Gestionar movimientos
- ✅ Aprobar/rechazar solicitudes de repuestos
- ✅ Entregar repuestos
- ✅ Ver OTs (para contexto)
- ✅ Ver reportes de inventario
- ❌ No puede crear/editar OTs
- ❌ No puede ejecutar OTs

### Funcionalidades Principales

#### Gestionar Catálogo de Repuestos

1. **Ver Repuestos**:
   - Ir a **"Inventario"** → **"Repuestos"**
   - Ver catálogo completo

2. **Crear Repuesto**:
   - Hacer clic en **"Nuevo Repuesto"**
   - Completar:
     - Código (único)
     - Nombre
     - Descripción
     - Marca
     - Categoría
     - Precio de referencia
     - Unidad de medida
   - Guardar

3. **Editar Repuesto**:
   - Buscar repuesto
   - Editar información
   - Guardar cambios

#### Gestionar Stock

1. **Ver Stock Actual**:
   - Ir a **"Inventario"** → **"Stock"**
   - Ver stock de todos los repuestos
   - Ver cantidad actual y mínima

2. **Registrar Entrada**:
   - Seleccionar repuesto
   - Ir a **"Entrada"**
   - Ingresar cantidad
   - Agregar motivo
   - Confirmar

3. **Ajustar Stock**:
   - Si hay discrepancias
   - Ir a **"Ajustar"**
   - Ingresar cantidad correcta
   - Indicar motivo del ajuste
   - Confirmar

4. **Ver Repuestos que Necesitan Reorden**:
   - Ir a **"Necesitan Reorden"**
   - Ver repuestos bajo stock mínimo
   - Generar orden de compra

#### Gestionar Solicitudes de Repuestos

1. **Ver Solicitudes Pendientes**:
   - Ir a **"Inventario"** → **"Solicitudes"**
   - Filtrar por estado **PENDIENTE**
   - Ver solicitudes desde OTs

2. **Revisar Solicitud**:
   - Ver:
     - OT origen
     - Repuesto solicitado
     - Cantidad solicitada
     - Stock disponible
     - Mecánico solicitante

3. **Aprobar o Rechazar**:
   - **Aprobar**: Si hay stock disponible
   - **Rechazar**: Si no hay stock o no aplica
   - Indicar motivo si rechaza

4. **Entregar Repuesto**:
   - Después de aprobar
   - Ir a **"Entregar"**
   - Registrar cantidad entregada
   - Confirmar entrega
   - El stock se actualiza automáticamente

#### Gestionar Movimientos

1. **Ver Movimientos**:
   - Ir a **"Inventario"** → **"Movimientos"**
   - Ver historial de entradas y salidas
   - Filtrar por fecha, repuesto, tipo

2. **Tipos de Movimientos**:
   - **ENTRADA**: Ingreso de repuestos
   - **SALIDA**: Salida por uso en OT
   - **AJUSTE**: Ajuste manual
   - **DEVOLUCION**: Devolución de repuesto

### Flujo de Trabajo Típico

1. **Inicio del día**: Revisar solicitudes pendientes
2. **Revisar stock**: Verificar stock disponible
3. **Aprobar solicitudes**: Aprobar solicitudes con stock
4. **Entregar repuestos**: Entregar repuestos aprobados
5. **Registrar entradas**: Registrar nuevos repuestos recibidos
6. **Revisar reorden**: Verificar repuestos que necesitan compra

### Recomendaciones

- Mantener stock actualizado
- Revisar solicitudes regularmente
- Aprobar solicitudes con prontitud
- Mantener comunicación con mecánicos
- Generar órdenes de compra cuando sea necesario

---

## Notas Generales

### Seguridad

- Cada usuario debe mantener su contraseña segura
- No compartir credenciales
- Cerrar sesión al terminar

### Soporte

Para problemas o consultas, contactar al administrador del sistema.

---

**Última actualización**: [Fecha]
**Versión del Manual**: 1.0

