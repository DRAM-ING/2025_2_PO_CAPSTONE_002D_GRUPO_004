-- ============================================================================
-- ESQUEMA SQL COMPLETO - PLATAFORMA DE GESTIÓN DE FLOTA PEPSICO
-- ============================================================================
-- Este script contiene la estructura completa de la base de datos
-- con todas las tablas, relaciones, índices y constraints.
-- 
-- Base de datos: PostgreSQL
-- Generado desde modelos Django
-- ============================================================================

-- ============================================================================
-- TABLA: users_user (Modelo User extendido de AbstractUser)
-- ============================================================================
CREATE TABLE IF NOT EXISTS users_user (
    id BIGSERIAL PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    username VARCHAR(150) UNIQUE NOT NULL,
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    email VARCHAR(254) UNIQUE NOT NULL,
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    date_joined TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    rol VARCHAR(20) NOT NULL DEFAULT 'ADMIN',
    rut VARCHAR(12) UNIQUE,
    is_permanent BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_users_user_rol ON users_user(rol);
CREATE INDEX IF NOT EXISTS idx_users_user_email ON users_user(email);
CREATE INDEX IF NOT EXISTS idx_users_user_rut ON users_user(rut);

-- ============================================================================
-- TABLA: users_profile (Perfil extendido del usuario)
-- ============================================================================
CREATE TABLE IF NOT EXISTS users_profile (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL REFERENCES users_user(id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone_number VARCHAR(32),
    notificaciones_email BOOLEAN NOT NULL DEFAULT TRUE,
    notificaciones_sonido BOOLEAN NOT NULL DEFAULT TRUE,
    notificaciones_push BOOLEAN NOT NULL DEFAULT FALSE
);

-- ============================================================================
-- TABLA: users_passwordresettoken (Tokens de recuperación de contraseña)
-- ============================================================================
CREATE TABLE IF NOT EXISTS users_passwordresettoken (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL REFERENCES users_user(id) ON DELETE CASCADE,
    token VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_passwordresettoken_token_used ON users_passwordresettoken(token, used);
CREATE INDEX IF NOT EXISTS idx_passwordresettoken_expires_at ON users_passwordresettoken(expires_at);
CREATE INDEX IF NOT EXISTS idx_passwordresettoken_user_id ON users_passwordresettoken(user_id);

-- ============================================================================
-- TABLA: vehicles_vehiculo (Vehículos de la flota)
-- ============================================================================
CREATE TABLE IF NOT EXISTS vehicles_vehiculo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patente VARCHAR(32) UNIQUE NOT NULL,
    tipo VARCHAR(20),
    categoria VARCHAR(20),
    marca VARCHAR(64),
    modelo VARCHAR(64),
    anio INTEGER,
    vin VARCHAR(64),
    estado VARCHAR(32) NOT NULL DEFAULT 'ACTIVO',
    zona VARCHAR(100),
    sucursal VARCHAR(100),
    site VARCHAR(100),
    supervisor_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL,
    estado_operativo VARCHAR(30) NOT NULL DEFAULT 'OPERATIVO',
    cumplimiento VARCHAR(20) NOT NULL DEFAULT 'EN_POLITICA',
    tct BOOLEAN NOT NULL DEFAULT FALSE,
    tct_fecha_inicio TIMESTAMP WITH TIME ZONE,
    tct_dias INTEGER NOT NULL DEFAULT 0,
    ceco VARCHAR(50),
    equipo_sap VARCHAR(50),
    ultima_revision DATE,
    proxima_revision DATE,
    kilometraje_actual INTEGER,
    km_mensual_promedio INTEGER,
    ultimo_movimiento TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT vehiculo_anio_valid CHECK (anio IS NULL OR (anio >= 1900 AND anio <= 2100))
);

CREATE INDEX IF NOT EXISTS idx_vehiculo_patente ON vehicles_vehiculo(patente);
CREATE INDEX IF NOT EXISTS idx_vehiculo_estado ON vehicles_vehiculo(estado);
CREATE INDEX IF NOT EXISTS idx_vehiculo_marca_modelo ON vehicles_vehiculo(marca, modelo);
CREATE INDEX IF NOT EXISTS idx_vehiculo_supervisor ON vehicles_vehiculo(supervisor_id);

-- ============================================================================
-- TABLA: vehicles_ingresovehiculo (Registro de ingreso al taller)
-- ============================================================================
CREATE TABLE IF NOT EXISTS vehicles_ingresovehiculo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehiculo_id UUID NOT NULL REFERENCES vehicles_vehiculo(id) ON DELETE PROTECT,
    guardia_id BIGINT NOT NULL REFERENCES users_user(id) ON DELETE PROTECT,
    fecha_ingreso TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_salida TIMESTAMP WITH TIME ZONE,
    guardia_salida_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL,
    observaciones TEXT,
    observaciones_salida TEXT,
    kilometraje INTEGER,
    kilometraje_salida INTEGER,
    qr_code VARCHAR(255),
    salio BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_ingresovehiculo_fecha_ingreso ON vehicles_ingresovehiculo(fecha_ingreso);
CREATE INDEX IF NOT EXISTS idx_ingresovehiculo_vehiculo_fecha ON vehicles_ingresovehiculo(vehiculo_id, fecha_ingreso);

-- ============================================================================
-- TABLA: vehicles_evidenciaingreso (Evidencias fotográficas del ingreso)
-- ============================================================================
CREATE TABLE IF NOT EXISTS vehicles_evidenciaingreso (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ingreso_id UUID NOT NULL REFERENCES vehicles_ingresovehiculo(id) ON DELETE CASCADE,
    url VARCHAR(200) NOT NULL,
    tipo VARCHAR(20) NOT NULL DEFAULT 'FOTO_INGRESO',
    descripcion TEXT,
    subido_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evidenciaingreso_ingreso_tipo ON vehicles_evidenciaingreso(ingreso_id, tipo);

-- ============================================================================
-- TABLA: vehicles_historialvehiculo (Historial completo del vehículo)
-- ============================================================================
CREATE TABLE IF NOT EXISTS vehicles_historialvehiculo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehiculo_id UUID NOT NULL REFERENCES vehicles_vehiculo(id) ON DELETE CASCADE,
    ot_id UUID REFERENCES workorders_ordentrabajo(id) ON DELETE SET NULL,
    tipo_evento VARCHAR(30) NOT NULL DEFAULT 'OTRO',
    fecha_ingreso TIMESTAMP WITH TIME ZONE,
    fecha_salida TIMESTAMP WITH TIME ZONE,
    tiempo_permanencia NUMERIC(10, 2),
    descripcion TEXT,
    falla VARCHAR(200),
    supervisor_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL,
    site VARCHAR(100),
    estado_antes VARCHAR(30),
    estado_despues VARCHAR(30),
    backup_utilizado_id UUID REFERENCES vehicles_backupvehiculo(id) ON DELETE SET NULL,
    creado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_historialvehiculo_vehiculo_creado ON vehicles_historialvehiculo(vehiculo_id, creado_en);
CREATE INDEX IF NOT EXISTS idx_historialvehiculo_tipo_evento ON vehicles_historialvehiculo(tipo_evento, creado_en);

-- ============================================================================
-- TABLA: vehicles_backupvehiculo (Asignación de vehículos backup)
-- ============================================================================
CREATE TABLE IF NOT EXISTS vehicles_backupvehiculo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehiculo_principal_id UUID NOT NULL REFERENCES vehicles_vehiculo(id) ON DELETE PROTECT,
    vehiculo_backup_id UUID NOT NULL REFERENCES vehicles_vehiculo(id) ON DELETE PROTECT,
    ot_id UUID REFERENCES workorders_ordentrabajo(id) ON DELETE SET NULL,
    fecha_inicio TIMESTAMP WITH TIME ZONE NOT NULL,
    fecha_devolucion TIMESTAMP WITH TIME ZONE,
    duracion_dias NUMERIC(10, 2),
    motivo TEXT NOT NULL,
    site VARCHAR(100),
    supervisor_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
    observaciones TEXT,
    creado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_backupvehiculo_principal_estado ON vehicles_backupvehiculo(vehiculo_principal_id, estado);
CREATE INDEX IF NOT EXISTS idx_backupvehiculo_backup_estado ON vehicles_backupvehiculo(vehiculo_backup_id, estado);
CREATE INDEX IF NOT EXISTS idx_backupvehiculo_fecha_inicio ON vehicles_backupvehiculo(fecha_inicio);

-- ============================================================================
-- TABLA: drivers_chofer (Choferes de la flota)
-- ============================================================================
CREATE TABLE IF NOT EXISTS drivers_chofer (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre_completo VARCHAR(255) NOT NULL,
    rut VARCHAR(12) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    email VARCHAR(254),
    zona VARCHAR(100),
    sucursal VARCHAR(100),
    vehiculo_asignado_id UUID REFERENCES vehicles_vehiculo(id) ON DELETE SET NULL,
    km_mensual_promedio INTEGER,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_ingreso DATE,
    observaciones TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chofer_rut ON drivers_chofer(rut);
CREATE INDEX IF NOT EXISTS idx_chofer_zona_activo ON drivers_chofer(zona, activo);
CREATE INDEX IF NOT EXISTS idx_chofer_vehiculo_asignado ON drivers_chofer(vehiculo_asignado_id);

-- ============================================================================
-- TABLA: drivers_historialasignacionvehiculo (Historial de asignaciones)
-- ============================================================================
CREATE TABLE IF NOT EXISTS drivers_historialasignacionvehiculo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chofer_id UUID NOT NULL REFERENCES drivers_chofer(id) ON DELETE CASCADE,
    vehiculo_id UUID NOT NULL REFERENCES vehicles_vehiculo(id) ON DELETE PROTECT,
    fecha_asignacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMP WITH TIME ZONE,
    motivo_fin TEXT,
    activa BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_historialasignacion_chofer_activa ON drivers_historialasignacionvehiculo(chofer_id, activa);
CREATE INDEX IF NOT EXISTS idx_historialasignacion_vehiculo_activa ON drivers_historialasignacionvehiculo(vehiculo_id, activa);
CREATE INDEX IF NOT EXISTS idx_historialasignacion_fecha ON drivers_historialasignacionvehiculo(fecha_asignacion);

-- ============================================================================
-- TABLA: workorders_ordentrabajo (Órdenes de Trabajo)
-- ============================================================================
CREATE TABLE IF NOT EXISTS workorders_ordentrabajo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehiculo_id UUID NOT NULL REFERENCES vehicles_vehiculo(id) ON DELETE PROTECT,
    supervisor_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL,
    jefe_taller_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL,
    mecanico_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL,
    responsable_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL,
    chofer_id UUID REFERENCES drivers_chofer(id) ON DELETE SET NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'ABIERTA',
    tipo VARCHAR(50) NOT NULL DEFAULT 'MANTENCION',
    prioridad VARCHAR(20) NOT NULL DEFAULT 'MEDIA',
    motivo TEXT,
    diagnostico TEXT,
    zona VARCHAR(100),
    site VARCHAR(100),
    backup_id UUID REFERENCES vehicles_backupvehiculo(id) ON DELETE SET NULL,
    estado_operativo_antes VARCHAR(30),
    estado_operativo_despues VARCHAR(30),
    causa_ingreso TEXT,
    causa_salida TEXT,
    tiempo_espera NUMERIC(10, 2),
    tiempo_ejecucion NUMERIC(10, 2),
    tiempo_total_reparacion NUMERIC(10, 2),
    sla_vencido BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_limite_sla TIMESTAMP WITH TIME ZONE,
    apertura TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_diagnostico TIMESTAMP WITH TIME ZONE,
    fecha_aprobacion_supervisor TIMESTAMP WITH TIME ZONE,
    fecha_asignacion_mecanico TIMESTAMP WITH TIME ZONE,
    fecha_inicio_ejecucion TIMESTAMP WITH TIME ZONE,
    cierre TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_ordentrabajo_estado ON workorders_ordentrabajo(estado);
CREATE INDEX IF NOT EXISTS idx_ordentrabajo_apertura ON workorders_ordentrabajo(apertura);
CREATE INDEX IF NOT EXISTS idx_ordentrabajo_vehiculo ON workorders_ordentrabajo(vehiculo_id);
CREATE INDEX IF NOT EXISTS idx_ordentrabajo_mecanico ON workorders_ordentrabajo(mecanico_id);
CREATE INDEX IF NOT EXISTS idx_ordentrabajo_supervisor ON workorders_ordentrabajo(supervisor_id);

-- ============================================================================
-- TABLA: workorders_itemot (Items de trabajo de una OT)
-- ============================================================================
CREATE TABLE IF NOT EXISTS workorders_itemot (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ot_id UUID NOT NULL REFERENCES workorders_ordentrabajo(id) ON DELETE CASCADE,
    tipo VARCHAR(20) NOT NULL,
    descripcion TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    costo_unitario NUMERIC(12, 2) NOT NULL,
    CONSTRAINT itemot_cantidad_gt_0 CHECK (cantidad > 0),
    CONSTRAINT itemot_costo_gte_0 CHECK (costo_unitario >= 0)
);

CREATE INDEX IF NOT EXISTS idx_itemot_ot ON workorders_itemot(ot_id);
CREATE INDEX IF NOT EXISTS idx_itemot_tipo ON workorders_itemot(tipo);

-- ============================================================================
-- TABLA: workorders_presupuesto (Presupuestos de OT)
-- ============================================================================
CREATE TABLE IF NOT EXISTS workorders_presupuesto (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ot_id UUID UNIQUE NOT NULL REFERENCES workorders_ordentrabajo(id) ON DELETE CASCADE,
    total NUMERIC(14, 2) NOT NULL,
    requiere_aprobacion BOOLEAN NOT NULL DEFAULT FALSE,
    umbral NUMERIC(14, 2),
    creado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLA: workorders_detallepresup (Detalles del presupuesto)
-- ============================================================================
CREATE TABLE IF NOT EXISTS workorders_detallepresup (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    presupuesto_id UUID NOT NULL REFERENCES workorders_presupuesto(id) ON DELETE CASCADE,
    concepto VARCHAR(255) NOT NULL,
    cantidad INTEGER NOT NULL,
    precio NUMERIC(12, 2) NOT NULL
);

-- ============================================================================
-- TABLA: workorders_aprobacion (Aprobaciones de presupuesto)
-- ============================================================================
CREATE TABLE IF NOT EXISTS workorders_aprobacion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    presupuesto_id UUID UNIQUE NOT NULL REFERENCES workorders_presupuesto(id) ON DELETE CASCADE,
    sponsor_id BIGINT NOT NULL REFERENCES users_user(id) ON DELETE PROTECT,
    estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    comentario TEXT,
    fecha TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLA: workorders_pausa (Pausas durante ejecución de OT)
-- ============================================================================
CREATE TABLE IF NOT EXISTS workorders_pausa (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ot_id UUID NOT NULL REFERENCES workorders_ordentrabajo(id) ON DELETE CASCADE,
    usuario_id BIGINT NOT NULL REFERENCES users_user(id) ON DELETE PROTECT,
    tipo VARCHAR(30) NOT NULL DEFAULT 'OTRO',
    motivo VARCHAR(255) NOT NULL,
    es_automatica BOOLEAN NOT NULL DEFAULT FALSE,
    inicio TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fin TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_pausa_ot_inicio ON workorders_pausa(ot_id, inicio);
CREATE INDEX IF NOT EXISTS idx_pausa_tipo_inicio ON workorders_pausa(tipo, inicio);
CREATE INDEX IF NOT EXISTS idx_pausa_automatica ON workorders_pausa(es_automatica);

-- ============================================================================
-- TABLA: workorders_checklist (Checklists de calidad)
-- ============================================================================
CREATE TABLE IF NOT EXISTS workorders_checklist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ot_id UUID NOT NULL REFERENCES workorders_ordentrabajo(id) ON DELETE CASCADE,
    verificador_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL,
    resultado VARCHAR(10) NOT NULL,
    observaciones TEXT,
    fecha TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLA: workorders_evidencia (Evidencias fotográficas/documentales)
-- ============================================================================
CREATE TABLE IF NOT EXISTS workorders_evidencia (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ot_id UUID REFERENCES workorders_ordentrabajo(id) ON DELETE CASCADE,
    url VARCHAR(200) NOT NULL,
    tipo VARCHAR(15) NOT NULL DEFAULT 'FOTO',
    descripcion TEXT NOT NULL DEFAULT '',
    subido_por_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL,
    subido_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    invalidado BOOLEAN NOT NULL DEFAULT FALSE,
    invalidado_por_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL,
    invalidado_en TIMESTAMP WITH TIME ZONE,
    motivo_invalidacion TEXT
);

CREATE INDEX IF NOT EXISTS idx_evidencia_ot ON workorders_evidencia(ot_id);
CREATE INDEX IF NOT EXISTS idx_evidencia_tipo ON workorders_evidencia(tipo);

-- ============================================================================
-- TABLA: workorders_versionevidencia (Historial de versiones de evidencias)
-- ============================================================================
CREATE TABLE IF NOT EXISTS workorders_versionevidencia (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evidencia_original_id UUID NOT NULL REFERENCES workorders_evidencia(id) ON DELETE CASCADE,
    url_anterior VARCHAR(200) NOT NULL,
    invalidado_por_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL,
    motivo TEXT NOT NULL,
    invalidado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_versionevidencia_original_invalidado ON workorders_versionevidencia(evidencia_original_id, invalidado_en);

-- ============================================================================
-- TABLA: workorders_auditoria (Registro de auditoría)
-- ============================================================================
CREATE TABLE IF NOT EXISTS workorders_auditoria (
    id BIGSERIAL PRIMARY KEY,
    usuario_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL,
    accion VARCHAR(64) NOT NULL,
    objeto_tipo VARCHAR(64) NOT NULL,
    objeto_id VARCHAR(64) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    ts TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_auditoria_objeto ON workorders_auditoria(objeto_tipo, objeto_id);
CREATE INDEX IF NOT EXISTS idx_auditoria_accion ON workorders_auditoria(accion);
CREATE INDEX IF NOT EXISTS idx_auditoria_ts ON workorders_auditoria(ts);

-- ============================================================================
-- TABLA: workorders_comentarioot (Comentarios en OT)
-- ============================================================================
CREATE TABLE IF NOT EXISTS workorders_comentarioot (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ot_id UUID NOT NULL REFERENCES workorders_ordentrabajo(id) ON DELETE CASCADE,
    usuario_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL,
    comentario_padre_id UUID REFERENCES workorders_comentarioot(id) ON DELETE CASCADE,
    contenido TEXT NOT NULL,
    menciones JSONB NOT NULL DEFAULT '[]',
    editado BOOLEAN NOT NULL DEFAULT FALSE,
    creado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    editado_en TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_comentarioot_ot_creado ON workorders_comentarioot(ot_id, creado_en);
CREATE INDEX IF NOT EXISTS idx_comentarioot_usuario_creado ON workorders_comentarioot(usuario_id, creado_en);

-- ============================================================================
-- TABLA: workorders_bloqueovehiculo (Bloqueos de vehículos)
-- ============================================================================
CREATE TABLE IF NOT EXISTS workorders_bloqueovehiculo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehiculo_id UUID NOT NULL REFERENCES vehicles_vehiculo(id) ON DELETE CASCADE,
    creado_por_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL,
    tipo VARCHAR(50) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
    motivo TEXT NOT NULL,
    creado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resuelto_en TIMESTAMP WITH TIME ZONE,
    resuelto_por_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_bloqueovehiculo_vehiculo_estado ON workorders_bloqueovehiculo(vehiculo_id, estado);
CREATE INDEX IF NOT EXISTS idx_bloqueovehiculo_estado_creado ON workorders_bloqueovehiculo(estado, creado_en);

-- ============================================================================
-- TABLA: inventory_repuesto (Catálogo de repuestos)
-- ============================================================================
CREATE TABLE IF NOT EXISTS inventory_repuesto (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo VARCHAR(64) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    marca VARCHAR(128),
    categoria VARCHAR(128),
    precio_referencia NUMERIC(12, 2),
    unidad_medida VARCHAR(32) NOT NULL DEFAULT 'UNIDAD',
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_repuesto_codigo ON inventory_repuesto(codigo);
CREATE INDEX IF NOT EXISTS idx_repuesto_categoria_activo ON inventory_repuesto(categoria, activo);

-- ============================================================================
-- TABLA: inventory_stock (Stock de repuestos)
-- ============================================================================
CREATE TABLE IF NOT EXISTS inventory_stock (
    id BIGSERIAL PRIMARY KEY,
    repuesto_id UUID UNIQUE NOT NULL REFERENCES inventory_repuesto(id) ON DELETE CASCADE,
    cantidad_actual INTEGER NOT NULL DEFAULT 0,
    cantidad_minima INTEGER NOT NULL DEFAULT 0,
    ubicacion VARCHAR(128),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stock_cantidad_actual ON inventory_stock(cantidad_actual);

-- ============================================================================
-- TABLA: inventory_movimientostock (Movimientos de stock)
-- ============================================================================
CREATE TABLE IF NOT EXISTS inventory_movimientostock (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repuesto_id UUID NOT NULL REFERENCES inventory_repuesto(id) ON DELETE PROTECT,
    tipo VARCHAR(20) NOT NULL,
    cantidad INTEGER NOT NULL,
    cantidad_anterior INTEGER NOT NULL,
    cantidad_nueva INTEGER NOT NULL,
    motivo TEXT,
    usuario_id BIGINT NOT NULL REFERENCES users_user(id) ON DELETE PROTECT,
    fecha TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ot_id UUID REFERENCES workorders_ordentrabajo(id) ON DELETE SET NULL,
    item_ot_id UUID REFERENCES workorders_itemot(id) ON DELETE SET NULL,
    vehiculo_id UUID REFERENCES vehicles_vehiculo(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_movimientostock_fecha ON inventory_movimientostock(fecha);
CREATE INDEX IF NOT EXISTS idx_movimientostock_repuesto_fecha ON inventory_movimientostock(repuesto_id, fecha);
CREATE INDEX IF NOT EXISTS idx_movimientostock_tipo_fecha ON inventory_movimientostock(tipo, fecha);
CREATE INDEX IF NOT EXISTS idx_movimientostock_ot_vehiculo ON inventory_movimientostock(ot_id, vehiculo_id);

-- ============================================================================
-- TABLA: inventory_solicitudrepuesto (Solicitudes de repuestos)
-- ============================================================================
CREATE TABLE IF NOT EXISTS inventory_solicitudrepuesto (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ot_id UUID NOT NULL REFERENCES workorders_ordentrabajo(id) ON DELETE CASCADE,
    item_ot_id UUID REFERENCES workorders_itemot(id) ON DELETE CASCADE,
    repuesto_id UUID NOT NULL REFERENCES inventory_repuesto(id) ON DELETE PROTECT,
    cantidad_solicitada INTEGER NOT NULL,
    cantidad_entregada INTEGER NOT NULL DEFAULT 0,
    estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    motivo TEXT,
    solicitante_id BIGINT REFERENCES users_user(id) ON DELETE PROTECT,
    aprobador_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL,
    entregador_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL,
    fecha_solicitud TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_aprobacion TIMESTAMP WITH TIME ZONE,
    fecha_entrega TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_solicitudrepuesto_estado_fecha ON inventory_solicitudrepuesto(estado, fecha_solicitud);
CREATE INDEX IF NOT EXISTS idx_solicitudrepuesto_ot_estado ON inventory_solicitudrepuesto(ot_id, estado);
CREATE INDEX IF NOT EXISTS idx_solicitudrepuesto_repuesto_estado ON inventory_solicitudrepuesto(repuesto_id, estado);

-- ============================================================================
-- TABLA: inventory_historialrepuestovehiculo (Historial de repuestos por vehículo)
-- ============================================================================
CREATE TABLE IF NOT EXISTS inventory_historialrepuestovehiculo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehiculo_id UUID NOT NULL REFERENCES vehicles_vehiculo(id) ON DELETE CASCADE,
    repuesto_id UUID NOT NULL REFERENCES inventory_repuesto(id) ON DELETE PROTECT,
    cantidad INTEGER NOT NULL,
    fecha_uso TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ot_id UUID REFERENCES workorders_ordentrabajo(id) ON DELETE SET NULL,
    item_ot_id UUID REFERENCES workorders_itemot(id) ON DELETE SET NULL,
    costo_unitario NUMERIC(12, 2)
);

CREATE INDEX IF NOT EXISTS idx_historialrepuesto_vehiculo_fecha ON inventory_historialrepuestovehiculo(vehiculo_id, fecha_uso);
CREATE INDEX IF NOT EXISTS idx_historialrepuesto_repuesto_fecha ON inventory_historialrepuestovehiculo(repuesto_id, fecha_uso);
CREATE INDEX IF NOT EXISTS idx_historialrepuesto_ot ON inventory_historialrepuestovehiculo(ot_id);

-- ============================================================================
-- TABLA: scheduling_agenda (Agenda de programación)
-- ============================================================================
CREATE TABLE IF NOT EXISTS scheduling_agenda (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehiculo_id UUID NOT NULL REFERENCES vehicles_vehiculo(id) ON DELETE PROTECT,
    coordinador_id BIGINT NOT NULL REFERENCES users_user(id) ON DELETE PROTECT,
    fecha_programada TIMESTAMP WITH TIME ZONE NOT NULL,
    motivo TEXT NOT NULL,
    tipo_mantenimiento VARCHAR(50) NOT NULL DEFAULT 'PREVENTIVO',
    zona VARCHAR(100),
    estado VARCHAR(20) NOT NULL DEFAULT 'PROGRAMADA',
    observaciones TEXT,
    ot_asociada_id UUID UNIQUE REFERENCES workorders_ordentrabajo(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_vehiculo_fecha_activa UNIQUE (vehiculo_id, fecha_programada) 
        WHERE estado IN ('PROGRAMADA', 'CONFIRMADA', 'EN_PROCESO')
);

CREATE INDEX IF NOT EXISTS idx_agenda_fecha_programada ON scheduling_agenda(fecha_programada);
CREATE INDEX IF NOT EXISTS idx_agenda_estado_fecha ON scheduling_agenda(estado, fecha_programada);
CREATE INDEX IF NOT EXISTS idx_agenda_vehiculo_estado ON scheduling_agenda(vehiculo_id, estado);
CREATE INDEX IF NOT EXISTS idx_agenda_zona_fecha ON scheduling_agenda(zona, fecha_programada);

-- ============================================================================
-- TABLA: scheduling_cupodiario (Cupos diarios de programación)
-- ============================================================================
CREATE TABLE IF NOT EXISTS scheduling_cupodiario (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fecha DATE UNIQUE NOT NULL,
    cupos_totales INTEGER NOT NULL DEFAULT 10,
    cupos_ocupados INTEGER NOT NULL DEFAULT 0,
    zona VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_cupodiario_fecha_zona ON scheduling_cupodiario(fecha, zona);

-- ============================================================================
-- TABLA: emergencies_emergenciaruta (Emergencias en ruta)
-- ============================================================================
CREATE TABLE IF NOT EXISTS emergencies_emergenciaruta (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehiculo_id UUID NOT NULL REFERENCES vehicles_vehiculo(id) ON DELETE PROTECT,
    solicitante_id BIGINT NOT NULL REFERENCES users_user(id) ON DELETE PROTECT,
    aprobador_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL,
    supervisor_asignado_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL,
    mecanico_asignado_id BIGINT REFERENCES users_user(id) ON DELETE SET NULL,
    descripcion TEXT NOT NULL,
    ubicacion VARCHAR(255) NOT NULL,
    zona VARCHAR(100),
    prioridad VARCHAR(20) NOT NULL DEFAULT 'ALTA',
    estado VARCHAR(20) NOT NULL DEFAULT 'SOLICITADA',
    fecha_solicitud TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_aprobacion TIMESTAMP WITH TIME ZONE,
    fecha_asignacion TIMESTAMP WITH TIME ZONE,
    fecha_resolucion TIMESTAMP WITH TIME ZONE,
    fecha_cierre TIMESTAMP WITH TIME ZONE,
    ot_asociada_id UUID UNIQUE REFERENCES workorders_ordentrabajo(id) ON DELETE SET NULL,
    observaciones TEXT
);

CREATE INDEX IF NOT EXISTS idx_emergenciaruta_estado_fecha ON emergencies_emergenciaruta(estado, fecha_solicitud);
CREATE INDEX IF NOT EXISTS idx_emergenciaruta_vehiculo_estado ON emergencies_emergenciaruta(vehiculo_id, estado);
CREATE INDEX IF NOT EXISTS idx_emergenciaruta_zona_estado ON emergencies_emergenciaruta(zona, estado);
CREATE INDEX IF NOT EXISTS idx_emergenciaruta_mecanico_estado ON emergencies_emergenciaruta(mecanico_asignado_id, estado);

-- ============================================================================
-- TABLA: notifications_notification (Notificaciones del sistema)
-- ============================================================================
CREATE TABLE IF NOT EXISTS notifications_notification (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id BIGINT NOT NULL REFERENCES users_user(id) ON DELETE CASCADE,
    tipo VARCHAR(20) NOT NULL DEFAULT 'GENERAL',
    titulo VARCHAR(200) NOT NULL,
    mensaje TEXT NOT NULL,
    estado VARCHAR(15) NOT NULL DEFAULT 'NO_LEIDA',
    ot_id UUID REFERENCES workorders_ordentrabajo(id) ON DELETE SET NULL,
    evidencia_id UUID REFERENCES workorders_evidencia(id) ON DELETE SET NULL,
    creada_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    leida_en TIMESTAMP WITH TIME ZONE,
    metadata JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_notification_usuario_estado ON notifications_notification(usuario_id, estado);
CREATE INDEX IF NOT EXISTS idx_notification_creada_en ON notifications_notification(creada_en);

-- ============================================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- ============================================================================

COMMENT ON TABLE users_user IS 'Usuarios del sistema con roles y autenticación';
COMMENT ON TABLE users_profile IS 'Perfiles extendidos de usuarios';
COMMENT ON TABLE vehicles_vehiculo IS 'Vehículos de la flota';
COMMENT ON TABLE workorders_ordentrabajo IS 'Órdenes de trabajo de mantenimiento';
COMMENT ON TABLE inventory_repuesto IS 'Catálogo de repuestos disponibles';
COMMENT ON TABLE drivers_chofer IS 'Choferes asignados a vehículos';

-- ============================================================================
-- FIN DEL ESQUEMA
-- ============================================================================

