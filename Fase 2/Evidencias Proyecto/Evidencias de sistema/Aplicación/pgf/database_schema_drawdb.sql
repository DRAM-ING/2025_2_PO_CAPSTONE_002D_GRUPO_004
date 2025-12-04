-- ============================================
-- PGF - Plataforma de Gestión de Flota
-- Schema SQL para drawdb.io
-- ============================================

-- ============================================
-- USUARIOS Y AUTENTICACIÓN
-- ============================================

CREATE TABLE users_user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    password VARCHAR(128) NOT NULL,
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    is_active BOOLEAN DEFAULT TRUE,
    is_staff BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    rol VARCHAR(20) DEFAULT 'ADMIN',
    rut VARCHAR(12) UNIQUE,
    is_permanent BOOLEAN DEFAULT FALSE
);

CREATE TABLE users_profile (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users_user(id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone_number VARCHAR(32),
    notificaciones_email BOOLEAN DEFAULT TRUE,
    notificaciones_sonido BOOLEAN DEFAULT TRUE,
    notificaciones_push BOOLEAN DEFAULT FALSE
);

CREATE TABLE users_passwordresettoken (
    id UUID PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users_user(id) ON DELETE CASCADE,
    token VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE
);

-- ============================================
-- VEHÍCULOS
-- ============================================

CREATE TABLE vehicles_marca (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(64) UNIQUE NOT NULL,
    activa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE vehicles_vehiculo (
    id UUID PRIMARY KEY,
    patente VARCHAR(32) UNIQUE NOT NULL,
    tipo VARCHAR(20),
    categoria VARCHAR(20),
    marca_id INTEGER REFERENCES vehicles_marca(id) ON DELETE PROTECT,
    modelo VARCHAR(64),
    anio INTEGER,
    vin VARCHAR(64),
    estado VARCHAR(32) DEFAULT 'ACTIVO',
    zona VARCHAR(100),
    sucursal VARCHAR(100),
    supervisor_id INTEGER REFERENCES users_user(id) ON DELETE SET NULL,
    estado_operativo VARCHAR(30) DEFAULT 'OPERATIVO',
    cumplimiento VARCHAR(20) DEFAULT 'EN_POLITICA',
    tct BOOLEAN DEFAULT FALSE,
    tct_fecha_inicio TIMESTAMP,
    tct_dias INTEGER DEFAULT 0,
    ceco VARCHAR(50),
    equipo_sap VARCHAR(50),
    ultima_revision DATE,
    proxima_revision DATE,
    kilometraje_actual INTEGER,
    km_mensual_promedio INTEGER,
    ultimo_movimiento TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (anio IS NULL OR (anio >= 1900 AND anio <= 2100))
);

CREATE TABLE vehicles_ingresovehiculo (
    id UUID PRIMARY KEY,
    vehiculo_id UUID NOT NULL REFERENCES vehicles_vehiculo(id) ON DELETE PROTECT,
    guardia_id INTEGER NOT NULL REFERENCES users_user(id) ON DELETE PROTECT,
    fecha_ingreso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_salida TIMESTAMP,
    guardia_salida_id INTEGER REFERENCES users_user(id) ON DELETE SET NULL,
    observaciones TEXT,
    observaciones_salida TEXT,
    kilometraje INTEGER,
    kilometraje_salida INTEGER,
    qr_code VARCHAR(255),
    salio BOOLEAN DEFAULT FALSE
);

CREATE TABLE vehicles_evidenciaingreso (
    id UUID PRIMARY KEY,
    ingreso_id UUID NOT NULL REFERENCES vehicles_ingresovehiculo(id) ON DELETE CASCADE,
    url VARCHAR(500) NOT NULL,
    tipo VARCHAR(20) DEFAULT 'FOTO_INGRESO',
    descripcion TEXT,
    subido_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE vehicles_historialvehiculo (
    id UUID PRIMARY KEY,
    vehiculo_id UUID NOT NULL REFERENCES vehicles_vehiculo(id) ON DELETE CASCADE,
    ot_id UUID REFERENCES workorders_ordentrabajo(id) ON DELETE SET NULL,
    tipo_evento VARCHAR(30) DEFAULT 'OTRO',
    fecha_ingreso TIMESTAMP,
    fecha_salida TIMESTAMP,
    tiempo_permanencia DECIMAL(10,2),
    descripcion TEXT,
    falla VARCHAR(200),
    supervisor_id INTEGER REFERENCES users_user(id) ON DELETE SET NULL,
    estado_antes VARCHAR(30),
    estado_despues VARCHAR(30),
    backup_utilizado_id UUID REFERENCES vehicles_backupvehiculo(id) ON DELETE SET NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE vehicles_backupvehiculo (
    id UUID PRIMARY KEY,
    vehiculo_principal_id UUID NOT NULL REFERENCES vehicles_vehiculo(id) ON DELETE PROTECT,
    vehiculo_backup_id UUID NOT NULL REFERENCES vehicles_vehiculo(id) ON DELETE PROTECT,
    ot_id UUID REFERENCES workorders_ordentrabajo(id) ON DELETE SET NULL,
    fecha_inicio TIMESTAMP NOT NULL,
    fecha_devolucion TIMESTAMP,
    duracion_dias DECIMAL(10,2),
    motivo TEXT NOT NULL,
    supervisor_id INTEGER REFERENCES users_user(id) ON DELETE SET NULL,
    estado VARCHAR(20) DEFAULT 'ACTIVO',
    observaciones TEXT,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- ÓRDENES DE TRABAJO
-- ============================================

CREATE TABLE workorders_ordentrabajo (
    id UUID PRIMARY KEY,
    vehiculo_id UUID NOT NULL REFERENCES vehicles_vehiculo(id) ON DELETE PROTECT,
    supervisor_id INTEGER REFERENCES users_user(id) ON DELETE SET NULL,
    jefe_taller_id INTEGER REFERENCES users_user(id) ON DELETE SET NULL,
    mecanico_id INTEGER REFERENCES users_user(id) ON DELETE SET NULL,
    responsable_id INTEGER REFERENCES users_user(id) ON DELETE SET NULL,
    chofer_id UUID REFERENCES drivers_chofer(id) ON DELETE SET NULL,
    estado VARCHAR(20) DEFAULT 'ABIERTA',
    tipo VARCHAR(50) DEFAULT 'MANTENCION',
    prioridad VARCHAR(20) DEFAULT 'MEDIA',
    motivo TEXT,
    diagnostico TEXT,
    zona VARCHAR(100),
    apertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cierre TIMESTAMP,
    tiempo_total_horas DECIMAL(10,2),
    tiempo_ejecucion_horas DECIMAL(10,2),
    tiempo_pausa_horas DECIMAL(10,2),
    costo_total DECIMAL(12,2),
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE workorders_itemot (
    id UUID PRIMARY KEY,
    ot_id UUID NOT NULL REFERENCES workorders_ordentrabajo(id) ON DELETE CASCADE,
    tipo VARCHAR(20) DEFAULT 'REPUESTO',
    descripcion TEXT NOT NULL,
    cantidad DECIMAL(10,2) DEFAULT 1.0,
    precio_unitario DECIMAL(12,2),
    subtotal DECIMAL(12,2),
    repuesto_id UUID REFERENCES inventory_repuesto(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE workorders_presupuesto (
    id UUID PRIMARY KEY,
    ot_id UUID UNIQUE NOT NULL REFERENCES workorders_ordentrabajo(id) ON DELETE CASCADE,
    total DECIMAL(12,2) NOT NULL,
    estado VARCHAR(20) DEFAULT 'BORRADOR',
    creado_por_id INTEGER REFERENCES users_user(id) ON DELETE SET NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_aprobacion TIMESTAMP,
    observaciones TEXT
);

CREATE TABLE workorders_detallepresup (
    id UUID PRIMARY KEY,
    presupuesto_id UUID NOT NULL REFERENCES workorders_presupuesto(id) ON DELETE CASCADE,
    item_ot_id UUID REFERENCES workorders_itemot(id) ON DELETE SET NULL,
    descripcion TEXT NOT NULL,
    cantidad DECIMAL(10,2) NOT NULL,
    precio_unitario DECIMAL(12,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL
);

CREATE TABLE workorders_aprobacion (
    id UUID PRIMARY KEY,
    presupuesto_id UUID NOT NULL REFERENCES workorders_presupuesto(id) ON DELETE CASCADE,
    sponsor_id INTEGER NOT NULL REFERENCES users_user(id) ON DELETE PROTECT,
    estado VARCHAR(20) DEFAULT 'PENDIENTE',
    fecha_aprobacion TIMESTAMP,
    comentarios TEXT
);

CREATE TABLE workorders_pausa (
    id UUID PRIMARY KEY,
    ot_id UUID NOT NULL REFERENCES workorders_ordentrabajo(id) ON DELETE CASCADE,
    usuario_id INTEGER NOT NULL REFERENCES users_user(id) ON DELETE PROTECT,
    motivo VARCHAR(50) DEFAULT 'MANUAL',
    inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fin TIMESTAMP,
    duracion_minutos INTEGER
);

CREATE TABLE workorders_checklist (
    id UUID PRIMARY KEY,
    ot_id UUID NOT NULL REFERENCES workorders_ordentrabajo(id) ON DELETE CASCADE,
    item VARCHAR(200) NOT NULL,
    completado BOOLEAN DEFAULT FALSE,
    observaciones TEXT,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE workorders_evidencia (
    id UUID PRIMARY KEY,
    ot_id UUID NOT NULL REFERENCES workorders_ordentrabajo(id) ON DELETE CASCADE,
    url VARCHAR(500) NOT NULL,
    tipo VARCHAR(20) DEFAULT 'FOTO',
    descripcion TEXT,
    subido_por_id INTEGER REFERENCES users_user(id) ON DELETE SET NULL,
    subido_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valida BOOLEAN DEFAULT TRUE
);

CREATE TABLE workorders_auditoria (
    id UUID PRIMARY KEY,
    usuario_id INTEGER REFERENCES users_user(id) ON DELETE SET NULL,
    accion VARCHAR(100) NOT NULL,
    objeto_tipo VARCHAR(100),
    objeto_id VARCHAR(100),
    payload JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- CHOFERES
-- ============================================

CREATE TABLE drivers_chofer (
    id UUID PRIMARY KEY,
    nombre_completo VARCHAR(255) NOT NULL,
    rut VARCHAR(12) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    email VARCHAR(254),
    zona VARCHAR(100),
    sucursal VARCHAR(100),
    vehiculo_asignado_id UUID REFERENCES vehicles_vehiculo(id) ON DELETE SET NULL,
    km_mensual_promedio INTEGER,
    activo BOOLEAN DEFAULT TRUE,
    fecha_ingreso DATE,
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE drivers_historialasignacionvehiculo (
    id UUID PRIMARY KEY,
    chofer_id UUID NOT NULL REFERENCES drivers_chofer(id) ON DELETE CASCADE,
    vehiculo_id UUID NOT NULL REFERENCES vehicles_vehiculo(id) ON DELETE PROTECT,
    fecha_asignacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMP,
    motivo_fin TEXT,
    activa BOOLEAN DEFAULT TRUE
);

-- ============================================
-- INVENTARIO
-- ============================================

CREATE TABLE inventory_repuesto (
    id UUID PRIMARY KEY,
    codigo VARCHAR(64) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    marca VARCHAR(128),
    categoria VARCHAR(128),
    precio_referencia DECIMAL(12,2),
    unidad_medida VARCHAR(32) DEFAULT 'UNIDAD',
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE inventory_stock (
    id SERIAL PRIMARY KEY,
    repuesto_id UUID UNIQUE NOT NULL REFERENCES inventory_repuesto(id) ON DELETE CASCADE,
    cantidad_actual INTEGER DEFAULT 0,
    cantidad_minima INTEGER DEFAULT 0,
    ubicacion VARCHAR(128),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE inventory_movimientostock (
    id UUID PRIMARY KEY,
    repuesto_id UUID NOT NULL REFERENCES inventory_repuesto(id) ON DELETE PROTECT,
    tipo VARCHAR(20) NOT NULL,
    cantidad INTEGER NOT NULL,
    cantidad_anterior INTEGER NOT NULL,
    cantidad_nueva INTEGER NOT NULL,
    motivo TEXT,
    usuario_id INTEGER NOT NULL REFERENCES users_user(id) ON DELETE PROTECT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ot_id UUID REFERENCES workorders_ordentrabajo(id) ON DELETE SET NULL,
    item_ot_id UUID REFERENCES workorders_itemot(id) ON DELETE SET NULL,
    vehiculo_id UUID REFERENCES vehicles_vehiculo(id) ON DELETE SET NULL
);

CREATE TABLE inventory_solicitudrepuesto (
    id UUID PRIMARY KEY,
    ot_id UUID NOT NULL REFERENCES workorders_ordentrabajo(id) ON DELETE CASCADE,
    item_ot_id UUID REFERENCES workorders_itemot(id) ON DELETE CASCADE,
    repuesto_id UUID NOT NULL REFERENCES inventory_repuesto(id) ON DELETE PROTECT,
    cantidad_solicitada INTEGER NOT NULL,
    cantidad_entregada INTEGER DEFAULT 0,
    estado VARCHAR(20) DEFAULT 'PENDIENTE',
    motivo TEXT,
    solicitante_id INTEGER REFERENCES users_user(id) ON DELETE PROTECT,
    aprobador_id INTEGER REFERENCES users_user(id) ON DELETE SET NULL,
    entregador_id INTEGER REFERENCES users_user(id) ON DELETE SET NULL,
    fecha_solicitud TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_aprobacion TIMESTAMP,
    fecha_entrega TIMESTAMP
);

CREATE TABLE inventory_historialrepuestovehiculo (
    id UUID PRIMARY KEY,
    vehiculo_id UUID NOT NULL REFERENCES vehicles_vehiculo(id) ON DELETE CASCADE,
    repuesto_id UUID NOT NULL REFERENCES inventory_repuesto(id) ON DELETE PROTECT,
    cantidad INTEGER NOT NULL,
    fecha_uso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ot_id UUID REFERENCES workorders_ordentrabajo(id) ON DELETE SET NULL,
    item_ot_id UUID REFERENCES workorders_itemot(id) ON DELETE SET NULL,
    costo_unitario DECIMAL(12,2)
);

-- ============================================
-- PROGRAMACIÓN (SCHEDULING)
-- ============================================

CREATE TABLE scheduling_agenda (
    id UUID PRIMARY KEY,
    vehiculo_id UUID NOT NULL REFERENCES vehicles_vehiculo(id) ON DELETE PROTECT,
    coordinador_id INTEGER NOT NULL REFERENCES users_user(id) ON DELETE PROTECT,
    fecha_programada TIMESTAMP NOT NULL,
    motivo TEXT NOT NULL,
    tipo_mantenimiento VARCHAR(50) DEFAULT 'PREVENTIVO',
    zona VARCHAR(100),
    estado VARCHAR(20) DEFAULT 'PROGRAMADA',
    observaciones TEXT,
    ot_asociada_id UUID UNIQUE REFERENCES workorders_ordentrabajo(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE scheduling_cupodiario (
    id UUID PRIMARY KEY,
    fecha DATE UNIQUE NOT NULL,
    cupos_totales INTEGER DEFAULT 10,
    cupos_ocupados INTEGER DEFAULT 0,
    zona VARCHAR(100)
);

-- ============================================
-- EMERGENCIAS
-- ============================================

CREATE TABLE emergencies_emergenciaruta (
    id UUID PRIMARY KEY,
    vehiculo_id UUID NOT NULL REFERENCES vehicles_vehiculo(id) ON DELETE PROTECT,
    solicitante_id INTEGER NOT NULL REFERENCES users_user(id) ON DELETE PROTECT,
    aprobador_id INTEGER REFERENCES users_user(id) ON DELETE SET NULL,
    supervisor_asignado_id INTEGER REFERENCES users_user(id) ON DELETE SET NULL,
    mecanico_asignado_id INTEGER REFERENCES users_user(id) ON DELETE SET NULL,
    descripcion TEXT NOT NULL,
    ubicacion VARCHAR(255) NOT NULL,
    zona VARCHAR(100),
    prioridad VARCHAR(20) DEFAULT 'ALTA',
    estado VARCHAR(20) DEFAULT 'SOLICITADA',
    fecha_solicitud TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_aprobacion TIMESTAMP,
    fecha_asignacion TIMESTAMP,
    fecha_resolucion TIMESTAMP,
    fecha_cierre TIMESTAMP,
    ot_asociada_id UUID UNIQUE REFERENCES workorders_ordentrabajo(id) ON DELETE SET NULL,
    observaciones TEXT
);

-- ============================================
-- NOTIFICACIONES
-- ============================================

CREATE TABLE notifications_notification (
    id UUID PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES users_user(id) ON DELETE CASCADE,
    tipo VARCHAR(20) DEFAULT 'GENERAL',
    titulo VARCHAR(200) NOT NULL,
    mensaje TEXT NOT NULL,
    estado VARCHAR(15) DEFAULT 'NO_LEIDA',
    ot_id UUID REFERENCES workorders_ordentrabajo(id) ON DELETE SET NULL,
    evidencia_id UUID REFERENCES workorders_evidencia(id) ON DELETE SET NULL,
    creada_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    leida_en TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- ============================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- ============================================

CREATE INDEX idx_user_email ON users_user(email);
CREATE INDEX idx_user_rut ON users_user(rut);
CREATE INDEX idx_user_rol ON users_user(rol);
CREATE INDEX idx_vehiculo_patente ON vehicles_vehiculo(patente);
CREATE INDEX idx_vehiculo_estado ON vehicles_vehiculo(estado);
CREATE INDEX idx_vehiculo_marca ON vehicles_vehiculo(marca_id);
CREATE INDEX idx_ot_vehiculo ON workorders_ordentrabajo(vehiculo_id);
CREATE INDEX idx_ot_estado ON workorders_ordentrabajo(estado);
CREATE INDEX idx_ot_mecanico ON workorders_ordentrabajo(mecanico_id);
CREATE INDEX idx_ot_supervisor ON workorders_ordentrabajo(supervisor_id);
CREATE INDEX idx_chofer_rut ON drivers_chofer(rut);
CREATE INDEX idx_repuesto_codigo ON inventory_repuesto(codigo);
CREATE INDEX idx_notification_usuario ON notifications_notification(usuario_id, estado);

