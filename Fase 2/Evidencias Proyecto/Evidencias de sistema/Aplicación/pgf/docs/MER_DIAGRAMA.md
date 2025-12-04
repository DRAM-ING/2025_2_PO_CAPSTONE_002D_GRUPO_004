# Modelo Entidad-Relación (MER) - Plataforma de Gestión de Flota Pepsico

Este documento contiene el diagrama MER completo de la base de datos en formato **DBML (Database Markup Language)** para visualización en dbdiagram.io.

## Visualización del Diagrama

El diagrama está en formato DBML. Puedes visualizarlo en:

- **[dbdiagram.io](https://dbdiagram.io)** - Herramienta principal recomendada
- VS Code con extensión DBML
- Cualquier herramienta que soporte DBML

## Cómo Visualizar el Diagrama

### Opción 1: dbdiagram.io (Recomendado)

1. Ve a [https://dbdiagram.io](https://dbdiagram.io)
2. Haz clic en **"New Project"** o **"Import"**
3. Abre el archivo `MER_DIAGRAMA.dbml` desde este repositorio
4. O copia y pega el contenido del archivo directamente
5. El diagrama se renderizará automáticamente con todas las relaciones

### Opción 2: Desde el Archivo

El código completo del diagrama está en: **`MER_DIAGRAMA.dbml`**

Puedes:
- Abrir el archivo directamente en dbdiagram.io
- Copiar su contenido y pegarlo en el editor online
- Usarlo con herramientas de línea de comandos que soporten DBML

## Estructura del Diagrama

El diagrama incluye **8 módulos principales**:

1. **Usuarios y Autenticación**
   - User, Profile, PasswordResetToken

2. **Vehículos**
   - Vehiculo, IngresoVehiculo, EvidenciaIngreso, HistorialVehiculo, BackupVehiculo

3. **Choferes**
   - Chofer, HistorialAsignacionVehiculo

4. **Órdenes de Trabajo**
   - OrdenTrabajo, ItemOT, Presupuesto, DetallePresup, Aprobacion
   - Pausa, Checklist, Evidencia, VersionEvidencia
   - ComentarioOT, BloqueoVehiculo, Auditoria

5. **Inventario**
   - Repuesto, Stock, MovimientoStock, SolicitudRepuesto, HistorialRepuestoVehiculo

6. **Programación**
   - Agenda, CupoDiario

7. **Emergencias**
   - EmergenciaRuta

8. **Notificaciones**
   - Notification

## Características del Diagrama

- **Relaciones explícitas**: Todas las Foreign Keys están definidas
- **Tipos de datos**: Especificados según el esquema PostgreSQL
- **Constraints**: Primary Keys, Unique Keys, Defaults
- **Notas**: Cada tabla incluye una descripción
- **OneToOne explícitas**: Relaciones especiales marcadas con `-` en lugar de `>`

## Leyenda de Relaciones en DBML

En el código DBML encontrarás:

- `ref: >` : Relación Uno a Muchos (OneToMany) - La tabla actual tiene muchos registros relacionados
- `ref: -` : Relación Uno a Uno (OneToOne) - La tabla actual tiene un solo registro relacionado
- `[pk]` : Primary Key
- `[unique]` : Unique Key
- `[not null]` : Campo obligatorio
- `[default: valor]` : Valor por defecto

## Ejemplo de Uso

```dbml
Table users_user {
  id bigserial [pk]
  email varchar(254) [unique, not null]
  rol varchar(20) [default: 'ADMIN']
  
  Note: 'Usuario principal del sistema.'
}

Table users_profile {
  id bigserial [pk]
  user_id bigint [unique, not null, ref: - users_user.id]
  
  Note: 'Perfil extendido del usuario.'
}
```

## Notas Importantes

- Todos los modelos principales usan **UUID** como identificador primario (excepto User que usa bigserial)
- El modelo `User` extiende `AbstractUser` de Django
- Las relaciones de auditoría usan campos genéricos (objeto_tipo, objeto_id) para flexibilidad
- Los timestamps incluyen timezone (`timestamptz`)
- Se mantiene integridad referencial con ON DELETE CASCADE/PROTECT/SET NULL según corresponda

## Exportar el Diagrama

Desde dbdiagram.io puedes:
- Exportar como imagen (PNG, SVG)
- Exportar como PDF
- Generar código SQL
- Compartir el diagrama con un enlace

## Archivos Relacionados

- `ESQUEMA_SQL_COMPLETO.sql` - Script SQL completo con todas las tablas
- `MODELO_DATOS.md` - Documentación detallada del modelo de datos
- `MER_DIAGRAMA.dbml` - Código fuente del diagrama (este archivo)

