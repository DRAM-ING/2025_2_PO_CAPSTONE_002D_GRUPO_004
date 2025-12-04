# 📊 Modelo de Datos - Plataforma de Gestión de Flota PepsiCo

## 📋 Descripción General

Este documento describe el modelo de datos completo de la Plataforma de Gestión de Flota (PGF) de PepsiCo. El sistema está diseñado para gestionar toda la operación de mantenimiento y reparación de vehículos, incluyendo órdenes de trabajo, inventario, programación, emergencias y notificaciones.

## 🏗️ Arquitectura de la Base de Datos

- **Motor**: PostgreSQL 16
- **ORM**: Django ORM
- **Identificadores**: UUID v4 para la mayoría de entidades (evita exposición de información secuencial)
- **Timezone**: America/Santiago (UTC-3)
- **Encoding**: UTF-8
- **Características**: 
  - Índices optimizados para consultas frecuentes
  - Constraints de integridad referencial
  - Validaciones a nivel de base de datos
  - Soporte para JSONB para campos flexibles

## 📐 Diagramas

- **Diagrama MER**: Ver [MER_DIAGRAMA.md](./MER_DIAGRAMA.md) y [MER_DIAGRAMA.dbml](./MER_DIAGRAMA.dbml)
- **Esquema SQL**: Ver [ESQUEMA_SQL_COMPLETO.sql](./ESQUEMA_SQL_COMPLETO.sql)

## Módulos y Entidades Principales

### 1. Módulo de Usuarios y Autenticación

#### User (users_user)
Usuario principal del sistema. Extiende AbstractUser de Django.

**Campos principales:**
- `id`: BIGSERIAL (PK)
- `username`: VARCHAR(150) UNIQUE
- `email`: VARCHAR(254) UNIQUE NOT NULL
- `password`: VARCHAR(128) NOT NULL
- `rol`: VARCHAR(20) - Roles: GUARDIA, MECANICO, SUPERVISOR, COORDINADOR_ZONA, RECEPCIONISTA, JEFE_TALLER, EJECUTIVO, SPONSOR, ADMIN, CHOFER
- `rut`: VARCHAR(12) UNIQUE - RUT chileno sin puntos ni guión
- `is_permanent`: BOOLEAN - Usuario que no se puede eliminar

**Relaciones:**
- OneToOne → Profile
- OneToMany → PasswordResetToken
- OneToMany → OrdenTrabajo (como supervisor, jefe_taller, mecanico, responsable)
- OneToMany → Vehiculo (como supervisor)
- OneToMany → Notification

#### Profile (users_profile)
Perfil extendido del usuario con preferencias.

**Campos principales:**
- `user_id`: FK → User (OneToOne)
- `phone_number`: VARCHAR(32)
- `notificaciones_email`: BOOLEAN
- `notificaciones_sonido`: BOOLEAN
- `notificaciones_push`: BOOLEAN

#### PasswordResetToken (users_passwordresettoken)
Tokens para recuperación de contraseña.

**Campos principales:**
- `id`: UUID (PK)
- `user_id`: FK → User
- `token`: VARCHAR(64) UNIQUE
- `expires_at`: TIMESTAMP
- `used`: BOOLEAN

---

### 2. Módulo de Vehículos

#### Vehiculo (vehicles_vehiculo)
Vehículo de la flota. Entidad central del sistema.

**Campos principales:**
- `id`: UUID (PK)
- `patente`: VARCHAR(32) UNIQUE NOT NULL
- `tipo`: VARCHAR(20) - ELECTRICO, DIESEL, UTILITARIO, REPARTO, VENTAS, RESPALDO
- `categoria`: VARCHAR(20) - REPARTO, VENTAS, RESPALDO
- `marca`, `modelo`: VARCHAR(64)
- `anio`: INTEGER (1900-2100)
- `vin`: VARCHAR(64) - Vehicle Identification Number
- `estado`: VARCHAR(32) - ACTIVO, EN_ESPERA, EN_MANTENIMIENTO, BAJA
- `zona`, `sucursal`, `site`: VARCHAR(100)
- `supervisor_id`: FK → User
- `estado_operativo`: VARCHAR(30) - OPERATIVO, EN_TALLER, BLOQUEADO, etc.
- `cumplimiento`: VARCHAR(20) - EN_POLITICA, FUERA_POLITICA
- `tct`: BOOLEAN - Bloqueo Temporal
- `kilometraje_actual`: INTEGER
- `km_mensual_promedio`: INTEGER
- `ultima_revision`, `proxima_revision`: DATE

**Relaciones:**
- OneToMany → OrdenTrabajo
- OneToMany → IngresoVehiculo
- OneToMany → HistorialVehiculo
- OneToMany → BackupVehiculo (como principal o backup)
- OneToMany → Chofer
- OneToMany → Agenda
- OneToMany → EmergenciaRuta

#### IngresoVehiculo (vehicles_ingresovehiculo)
Registro de ingreso de vehículo al taller.

**Campos principales:**
- `id`: UUID (PK)
- `vehiculo_id`: FK → Vehiculo
- `guardia_id`: FK → User
- `fecha_ingreso`: TIMESTAMP
- `fecha_salida`: TIMESTAMP
- `kilometraje`, `kilometraje_salida`: INTEGER
- `salio`: BOOLEAN

**Relaciones:**
- OneToMany → EvidenciaIngreso

#### EvidenciaIngreso (vehicles_evidenciaingreso)
Evidencias fotográficas del ingreso.

**Campos principales:**
- `id`: UUID (PK)
- `ingreso_id`: FK → IngresoVehiculo
- `url`: VARCHAR(200) - URL en S3
- `tipo`: VARCHAR(20) - FOTO_INGRESO, FOTO_DANOS, FOTO_DOCUMENTOS, OTRO

#### HistorialVehiculo (vehicles_historialvehiculo)
Historial completo de eventos del vehículo.

**Campos principales:**
- `id`: UUID (PK)
- `vehiculo_id`: FK → Vehiculo
- `ot_id`: FK → OrdenTrabajo (opcional)
- `tipo_evento`: VARCHAR(30) - OT_CREADA, OT_CERRADA, INGRESO_TALLER, etc.
- `fecha_ingreso`, `fecha_salida`: TIMESTAMP
- `tiempo_permanencia`: NUMERIC(10,2) - días
- `supervisor_id`: FK → User
- `backup_utilizado_id`: FK → BackupVehiculo

#### BackupVehiculo (vehicles_backupvehiculo)
Asignación de vehículo backup cuando el principal está en taller.

**Campos principales:**
- `id`: UUID (PK)
- `vehiculo_principal_id`: FK → Vehiculo
- `vehiculo_backup_id`: FK → Vehiculo
- `ot_id`: FK → OrdenTrabajo
- `fecha_inicio`, `fecha_devolucion`: TIMESTAMP
- `duracion_dias`: NUMERIC(10,2)
- `estado`: VARCHAR(20) - ACTIVO, DEVUELTO, CANCELADO
- `supervisor_id`: FK → User

---

### 3. Módulo de Choferes

#### Chofer (drivers_chofer)
Chofer asignado a vehículos.

**Campos principales:**
- `id`: UUID (PK)
- `nombre_completo`: VARCHAR(255)
- `rut`: VARCHAR(12) UNIQUE
- `telefono`, `email`: VARCHAR
- `zona`, `sucursal`: VARCHAR(100)
- `vehiculo_asignado_id`: FK → Vehiculo
- `km_mensual_promedio`: INTEGER
- `activo`: BOOLEAN

**Relaciones:**
- OneToMany → HistorialAsignacionVehiculo
- OneToMany → OrdenTrabajo

#### HistorialAsignacionVehiculo (drivers_historialasignacionvehiculo)
Historial de asignaciones de vehículos a choferes.

**Campos principales:**
- `id`: UUID (PK)
- `chofer_id`: FK → Chofer
- `vehiculo_id`: FK → Vehiculo
- `fecha_asignacion`, `fecha_fin`: TIMESTAMP
- `activa`: BOOLEAN

---

### 4. Módulo de Órdenes de Trabajo

#### OrdenTrabajo (workorders_ordentrabajo)
Orden de trabajo. Entidad central del flujo de mantenimiento.

**Estados del flujo:**
```
ABIERTA → EN_DIAGNOSTICO → EN_EJECUCION → EN_PAUSA → EN_EJECUCION 
→ EN_QA → CERRADA
                    ↓
                RETRABAJO → EN_EJECUCION
```

**Campos principales:**
- `id`: UUID (PK)
- `vehiculo_id`: FK → Vehiculo
- `supervisor_id`: FK → User
- `jefe_taller_id`: FK → User
- `mecanico_id`: FK → User
- `responsable_id`: FK → User
- `chofer_id`: FK → Chofer
- `estado`: VARCHAR(20) - ABIERTA, EN_DIAGNOSTICO, EN_EJECUCION, EN_PAUSA, EN_QA, RETRABAJO, CERRADA, ANULADA
- `tipo`: VARCHAR(50) - MANTENCION, REPARACION, EMERGENCIA, DIAGNOSTICO, OTRO
- `prioridad`: VARCHAR(20) - CRITICA, ALTA, MEDIA, BAJA
- `motivo`, `diagnostico`: TEXT
- `zona`, `site`: VARCHAR(100)
- `backup_id`: FK → BackupVehiculo
- `tiempo_espera`, `tiempo_ejecucion`, `tiempo_total_reparacion`: NUMERIC(10,2)
- `sla_vencido`: BOOLEAN
- `fecha_limite_sla`: TIMESTAMP
- `apertura`, `fecha_diagnostico`, `fecha_aprobacion_supervisor`, `fecha_asignacion_mecanico`, `fecha_inicio_ejecucion`, `cierre`: TIMESTAMP

**Relaciones:**
- OneToMany → ItemOT
- OneToOne → Presupuesto
- OneToMany → Pausa
- OneToMany → Checklist
- OneToMany → Evidencia
- OneToMany → ComentarioOT
- OneToMany → SolicitudRepuesto
- OneToMany → MovimientoStock
- OneToOne → Agenda (ot_asociada)
- OneToOne → EmergenciaRuta (ot_asociada)

#### ItemOT (workorders_itemot)
Items de trabajo (repuestos y servicios) de una OT.

**Campos principales:**
- `id`: UUID (PK)
- `ot_id`: FK → OrdenTrabajo
- `tipo`: VARCHAR(20) - REPUESTO, SERVICIO
- `descripcion`: TEXT
- `cantidad`: INTEGER (> 0)
- `costo_unitario`: NUMERIC(12,2) (>= 0)

#### Presupuesto (workorders_presupuesto)
Presupuesto asociado a una OT.

**Campos principales:**
- `id`: UUID (PK)
- `ot_id`: FK → OrdenTrabajo (OneToOne)
- `total`: NUMERIC(14,2)
- `requiere_aprobacion`: BOOLEAN
- `umbral`: NUMERIC(14,2)

**Relaciones:**
- OneToMany → DetallePresup
- OneToOne → Aprobacion

#### DetallePresup (workorders_detallepresup)
Detalles del presupuesto.

**Campos principales:**
- `id`: UUID (PK)
- `presupuesto_id`: FK → Presupuesto
- `concepto`: VARCHAR(255)
- `cantidad`: INTEGER
- `precio`: NUMERIC(12,2)

#### Aprobacion (workorders_aprobacion)
Aprobación de presupuesto por Sponsor.

**Campos principales:**
- `id`: UUID (PK)
- `presupuesto_id`: FK → Presupuesto (OneToOne)
- `sponsor_id`: FK → User
- `estado`: VARCHAR(20) - PENDIENTE, APROBADO, RECHAZADO
- `comentario`: TEXT

#### Pausa (workorders_pausa)
Pausas durante la ejecución de una OT.

**Campos principales:**
- `id`: UUID (PK)
- `ot_id`: FK → OrdenTrabajo
- `usuario_id`: FK → User
- `tipo`: VARCHAR(30) - ESPERA_REPUESTO, APROBACION_PENDIENTE, COLACION, OTRO, ADMINISTRATIVA
- `motivo`: VARCHAR(255)
- `es_automatica`: BOOLEAN - True para pausas automáticas (colación)
- `inicio`, `fin`: TIMESTAMP

#### Checklist (workorders_checklist)
Checklists de calidad para OT.

**Campos principales:**
- `id`: UUID (PK)
- `ot_id`: FK → OrdenTrabajo
- `verificador_id`: FK → User
- `resultado`: VARCHAR(10) - OK, NO_OK
- `observaciones`: TEXT

#### Evidencia (workorders_evidencia)
Evidencias fotográficas/documentales de una OT.

**Campos principales:**
- `id`: UUID (PK)
- `ot_id`: FK → OrdenTrabajo
- `url`: VARCHAR(200) - URL en S3
- `tipo`: VARCHAR(15) - FOTO, PDF, HOJA_CALCULO, DOCUMENTO, COMPRIMIDO, OTRO
- `descripcion`: TEXT
- `subido_por_id`: FK → User
- `invalidado`: BOOLEAN
- `invalidado_por_id`: FK → User
- `invalidado_en`: TIMESTAMP
- `motivo_invalidacion`: TEXT

**Relaciones:**
- OneToMany → VersionEvidencia
- OneToMany → Notification

#### VersionEvidencia (workorders_versionevidencia)
Historial de versiones de evidencias invalidadas.

**Campos principales:**
- `id`: UUID (PK)
- `evidencia_original_id`: FK → Evidencia
- `url_anterior`: VARCHAR(200)
- `invalidado_por_id`: FK → User
- `motivo`: TEXT

#### ComentarioOT (workorders_comentarioot)
Comentarios internos en una OT.

**Campos principales:**
- `id`: UUID (PK)
- `ot_id`: FK → OrdenTrabajo
- `usuario_id`: FK → User
- `comentario_padre_id`: FK → ComentarioOT (self-reference para respuestas)
- `contenido`: TEXT
- `menciones`: JSONB - Lista de IDs de usuarios mencionados
- `editado`: BOOLEAN
- `creado_en`, `editado_en`: TIMESTAMP

#### BloqueoVehiculo (workorders_bloqueovehiculo)
Bloqueos o restricciones de vehículos.

**Campos principales:**
- `id`: UUID (PK)
- `vehiculo_id`: FK → Vehiculo
- `creado_por_id`: FK → User
- `tipo`: VARCHAR(50) - PENDIENTE_PAGO, DOCUMENTACION_INCOMPLETA, SANCION, etc.
- `estado`: VARCHAR(20) - ACTIVO, RESUELTO, CANCELADO
- `motivo`: TEXT
- `resuelto_por_id`: FK → User
- `resuelto_en`: TIMESTAMP

#### Auditoria (workorders_auditoria)
Registro de auditoría de todas las acciones del sistema.

**Campos principales:**
- `id`: BIGSERIAL (PK)
- `usuario_id`: FK → User (opcional, puede ser sistema)
- `accion`: VARCHAR(64) - Tipo de acción (ej: "LOGIN_EXITOSO", "CERRAR_OT")
- `objeto_tipo`: VARCHAR(64) - Tipo del objeto afectado (ej: "OrdenTrabajo")
- `objeto_id`: VARCHAR(64) - ID del objeto afectado
- `payload`: JSONB - Datos adicionales
- `ts`: TIMESTAMP

---

### 5. Módulo de Inventario

#### Repuesto (inventory_repuesto)
Catálogo de repuestos disponibles.

**Campos principales:**
- `id`: UUID (PK)
- `codigo`: VARCHAR(64) UNIQUE
- `nombre`: VARCHAR(255)
- `descripcion`: TEXT
- `marca`: VARCHAR(128)
- `categoria`: VARCHAR(128) - ej: "Frenos", "Motor", "Transmisión"
- `precio_referencia`: NUMERIC(12,2)
- `unidad_medida`: VARCHAR(32) - UNIDAD, LITRO, KILO, etc.
- `activo`: BOOLEAN

**Relaciones:**
- OneToOne → Stock
- OneToMany → MovimientoStock
- OneToMany → SolicitudRepuesto
- OneToMany → HistorialRepuestoVehiculo

#### Stock (inventory_stock)
Stock actual de repuestos en bodega.

**Campos principales:**
- `id`: BIGSERIAL (PK)
- `repuesto_id`: FK → Repuesto (OneToOne)
- `cantidad_actual`: INTEGER
- `cantidad_minima`: INTEGER - Nivel de reorden
- `ubicacion`: VARCHAR(128) - Ubicación física en bodega

#### MovimientoStock (inventory_movimientostock)
Registro de movimientos de stock (entradas y salidas).

**Campos principales:**
- `id`: UUID (PK)
- `repuesto_id`: FK → Repuesto
- `tipo`: VARCHAR(20) - ENTRADA, SALIDA, AJUSTE, DEVOLUCION
- `cantidad`, `cantidad_anterior`, `cantidad_nueva`: INTEGER
- `motivo`: TEXT
- `usuario_id`: FK → User
- `fecha`: TIMESTAMP
- `ot_id`: FK → OrdenTrabajo (opcional)
- `item_ot_id`: FK → ItemOT (opcional)
- `vehiculo_id`: FK → Vehiculo (opcional)

#### SolicitudRepuesto (inventory_solicitudrepuesto)
Solicitudes de repuestos desde OT.

**Campos principales:**
- `id`: UUID (PK)
- `ot_id`: FK → OrdenTrabajo
- `item_ot_id`: FK → ItemOT
- `repuesto_id`: FK → Repuesto
- `cantidad_solicitada`, `cantidad_entregada`: INTEGER
- `estado`: VARCHAR(20) - PENDIENTE, APROBADA, RECHAZADA, ENTREGADA, CANCELADA
- `solicitante_id`: FK → User
- `aprobador_id`: FK → User
- `entregador_id`: FK → User
- `fecha_solicitud`, `fecha_aprobacion`, `fecha_entrega`: TIMESTAMP

#### HistorialRepuestoVehiculo (inventory_historialrepuestovehiculo)
Histórico de repuestos utilizados por vehículo.

**Campos principales:**
- `id`: UUID (PK)
- `vehiculo_id`: FK → Vehiculo
- `repuesto_id`: FK → Repuesto
- `cantidad`: INTEGER
- `fecha_uso`: TIMESTAMP
- `ot_id`: FK → OrdenTrabajo
- `item_ot_id`: FK → ItemOT
- `costo_unitario`: NUMERIC(12,2)

---

### 6. Módulo de Programación

#### Agenda (scheduling_agenda)
Agenda de programación de mantenimientos.

**Campos principales:**
- `id`: UUID (PK)
- `vehiculo_id`: FK → Vehiculo
- `coordinador_id`: FK → User
- `fecha_programada`: TIMESTAMP
- `motivo`: TEXT
- `tipo_mantenimiento`: VARCHAR(50) - PREVENTIVO, CORRECTIVO, EMERGENCIA
- `zona`: VARCHAR(100)
- `estado`: VARCHAR(20) - PROGRAMADA, CONFIRMADA, EN_PROCESO, COMPLETADA, CANCELADA, REPROGRAMADA
- `ot_asociada_id`: FK → OrdenTrabajo (OneToOne, se crea cuando el vehículo ingresa)

**Constraints:**
- UNIQUE (vehiculo_id, fecha_programada) WHERE estado IN ('PROGRAMADA', 'CONFIRMADA', 'EN_PROCESO')

#### CupoDiario (scheduling_cupodiario)
Cupos disponibles por día para programación.

**Campos principales:**
- `id`: UUID (PK)
- `fecha`: DATE UNIQUE
- `cupos_totales`: INTEGER DEFAULT 10
- `cupos_ocupados`: INTEGER DEFAULT 0
- `zona`: VARCHAR(100)

---

### 7. Módulo de Emergencias

#### EmergenciaRuta (emergencies_emergenciaruta)
Emergencias en ruta que requieren atención especial.

**Estados:**
```
SOLICITADA → APROBADA → ASIGNADA → EN_CAMINO → EN_REPARACION 
→ RESUELTA → CERRADA
```

**Campos principales:**
- `id`: UUID (PK)
- `vehiculo_id`: FK → Vehiculo
- `solicitante_id`: FK → User
- `aprobador_id`: FK → User
- `supervisor_asignado_id`: FK → User
- `mecanico_asignado_id`: FK → User
- `descripcion`: TEXT
- `ubicacion`: VARCHAR(255)
- `zona`: VARCHAR(100)
- `prioridad`: VARCHAR(20) - CRITICA, ALTA, MEDIA
- `estado`: VARCHAR(20) - SOLICITADA, APROBADA, ASIGNADA, EN_CAMINO, EN_REPARACION, RESUELTA, CERRADA, RECHAZADA
- `fecha_solicitud`, `fecha_aprobacion`, `fecha_asignacion`, `fecha_resolucion`, `fecha_cierre`: TIMESTAMP
- `ot_asociada_id`: FK → OrdenTrabajo (OneToOne, se crea cuando se asigna mecánico)

---

### 8. Módulo de Notificaciones

#### Notification (notifications_notification)
Notificaciones del sistema para usuarios.

**Campos principales:**
- `id`: UUID (PK)
- `usuario_id`: FK → User
- `tipo`: VARCHAR(20) - EVIDENCIA_SUBIDA, OT_CREADA, OT_CERRADA, OT_ASIGNADA, OT_EN_PAUSA, OT_EN_QA, OT_RETRABAJO, OT_APROBADA, OT_RECHAZADA, GENERAL
- `titulo`: VARCHAR(200)
- `mensaje`: TEXT
- `estado`: VARCHAR(15) - NO_LEIDA, LEIDA, ARCHIVADA
- `ot_id`: FK → OrdenTrabajo (opcional)
- `evidencia_id`: FK → Evidencia (opcional)
- `creada_en`, `leida_en`: TIMESTAMP
- `metadata`: JSONB - Datos adicionales

---

## Relaciones Principales

### Flujo de Orden de Trabajo
```
Vehiculo → IngresoVehiculo → OrdenTrabajo → ItemOT
                              ↓
                         Presupuesto → DetallePresup
                              ↓
                         Aprobacion (si requiere)
                              ↓
                         Pausa (durante ejecución)
                              ↓
                         Checklist (QA)
                              ↓
                         Evidencia
                              ↓
                         Cierre
```

### Flujo de Emergencia
```
EmergenciaRuta → OrdenTrabajo (se crea automáticamente)
```

### Flujo de Programación
```
Agenda → OrdenTrabajo (se crea cuando el vehículo ingresa)
```

### Flujo de Inventario
```
SolicitudRepuesto → MovimientoStock → Stock
```

## Índices Principales

Los índices están optimizados para las consultas más frecuentes:

- **Búsquedas por estado**: `idx_ordentrabajo_estado`, `idx_vehiculo_estado`
- **Búsquedas por fecha**: `idx_ordentrabajo_apertura`, `idx_ingresovehiculo_fecha_ingreso`
- **Búsquedas por usuario**: `idx_notification_usuario_estado`
- **Búsquedas por vehículo**: `idx_ordentrabajo_vehiculo`, `idx_historialvehiculo_vehiculo`
- **Búsquedas por código**: `idx_repuesto_codigo`, `idx_chofer_rut`

## Constraints y Validaciones

- **CheckConstraints**: Validación de año de vehículo (1900-2100), cantidad > 0 en ItemOT, costo >= 0
- **UniqueConstraints**: Patente única, RUT único, código de repuesto único
- **Foreign Keys**: Integridad referencial con ON DELETE CASCADE/PROTECT/SET NULL según corresponda

## 🔐 Consideraciones de Diseño

1. **UUIDs**: Se usan UUIDs para evitar exposición de información secuencial y mejorar la seguridad
2. **Timestamps**: Todos incluyen timezone (TIMESTAMP WITH TIME ZONE) para manejo correcto de fechas
3. **Soft Deletes**: Algunas entidades usan campos `activo` o `estado` en lugar de eliminación física para mantener historial
4. **Auditoría**: Tabla genérica de auditoría para registrar todas las acciones del sistema
5. **Evidencias**: Almacenamiento en S3 (LocalStack en desarrollo), referenciado por URL
6. **JSONB**: Uso de JSONB para campos flexibles (metadata, payload, menciones) permitiendo consultas eficientes
7. **Índices**: Optimizados para consultas frecuentes (búsquedas por estado, fecha, usuario, vehículo)
8. **Constraints**: Validaciones a nivel de base de datos para garantizar integridad

## 📈 Estadísticas del Modelo

- **Total de Tablas**: ~30 tablas principales
- **Módulos**: 8 módulos principales
- **Relaciones**: ~50 relaciones ForeignKey y OneToOne
- **Índices**: ~20 índices optimizados
- **Constraints**: Validaciones en múltiples niveles

## 🔗 Referencias

- [Diagrama MER](./MER_DIAGRAMA.md)
- [Esquema SQL Completo](./ESQUEMA_SQL_COMPLETO.sql)
- [Manual de Usuario General](./MANUAL_USUARIO_GENERAL.md)
- [Manuales por Rol](./MANUALES_USUARIO_POR_ROLES.md)

---

**Última actualización**: Enero 2025

