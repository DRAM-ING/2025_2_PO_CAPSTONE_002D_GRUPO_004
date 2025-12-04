# Colección Postman - PGF API

## 📥 Importar Colección

1. Abre Postman
2. Click en "Import"
3. Selecciona el archivo `PGF_API_Collection.json`
4. La colección se importará con todas las carpetas y requests

## 🔧 Configurar Variables de Entorno

1. En Postman, click en "Environments" (lado izquierdo)
2. Crea un nuevo environment llamado "PGF Local"
3. Agrega las siguientes variables:

| Variable | Valor Inicial | Descripción |
|----------|---------------|-------------|
| `base_url` | `http://localhost:8000/api/v1` | URL base de la API. **Importante**: Si usas Docker, usa `http://localhost:8000/api/v1`. Si el backend está en otro puerto, ajusta el puerto. |
| `frontend_url` | `http://localhost:3000` | URL del frontend |
| `access_token` | (vacío) | Se llena automáticamente al hacer login |
| `refresh_token` | (vacío) | Se llena automáticamente al hacer login |
| `user_id` | (vacío) | Se llena automáticamente al hacer login |
| `ot_id` | (vacío) | Se llena al crear una OT |
| `vehicle_id` | (vacío) | Se llena al crear un vehículo (UUID) |
| `chofer_id` | (vacío) | Se llena al crear un chofer (UUID) |

4. Selecciona este environment antes de ejecutar las requests

## 🚀 Flujos de Prueba

### Flujo 1: Autenticación Completa

1. **Login**
   - Ejecuta "1. Autenticación > Login"
   - Verifica que `access_token` y `refresh_token` se guardaron
   - Verifica que `user_id` se guardó

2. **Obtener Usuario Actual**
   - Ejecuta "1. Autenticación > Obtener Usuario Actual (Me)"
   - Verifica que retorna los datos del usuario logueado

3. **Refresh Token**
   - Espera 1 hora (o modifica expiración)
   - Ejecuta "1. Autenticación > Refresh Token"
   - Verifica que se obtiene un nuevo token

### Flujo 2: Gestión de Usuarios (Requiere ADMIN)

1. **Listar Usuarios**
   - Ejecuta "2. Usuarios > Listar Usuarios"
   - Verifica que retorna lista paginada
   - Verifica que usuario "admin" NO aparece si no eres admin

2. **Crear Usuario**
   - Ejecuta "2. Usuarios > Crear Usuario"
   - Modifica los datos en el body según necesites
   - Verifica que se crea correctamente

3. **Obtener Usuario**
   - Ejecuta "2. Usuarios > Obtener Usuario por ID"
   - Usa el ID del usuario creado
   - Verifica que retorna los datos correctos

### Flujo 3: Gestión de Vehículos - Ingreso y Salida

1. **Registrar Ingreso de Vehículo**
   - Ejecuta "3. Vehículos > Registrar Ingreso"
   - Body: `{"patente": "ABC123", "observaciones": "Ingreso para mantención"}`
   - Verifica que se crea `IngresoVehiculo` y `OrdenTrabajo` automáticamente
   - Guarda `ingreso_id` y `ot_id` de la respuesta

2. **Generar Ticket de Ingreso PDF**
   - Ejecuta "3. Vehículos > Generar Ticket PDF"
   - Usa el `ingreso_id` guardado
   - Verifica que descarga un PDF válido con información del ingreso

3. **Listar Ingresos del Día**
   - Ejecuta "3. Vehículos > Ingresos del Día"
   - Verifica que retorna lista de ingresos del día actual
   - Verifica que incluye información del vehículo y OT generada

4. **Registrar Salida de Vehículo**
   - Ejecuta "3. Vehículos > Registrar Salida"
   - Body: `{"ingreso_id": "...", "observaciones_salida": "Vehículo listo", "kilometraje_salida": 50000}`
   - Verifica que cambia estado del vehículo a ACTIVO
   - Verifica que `salio` se marca como `true`

### Flujo 4: Crear Orden de Trabajo Completa

1. **Listar Vehículos**
   - Ejecuta "3. Vehículos > Listar Vehículos"
   - Copia un `vehicle_id` de la respuesta
   - Actualiza la variable `vehicle_id` en el environment

2. **Crear OT**
   - Ejecuta "4. Órdenes de Trabajo > Crear OT"
   - Verifica que `ot_id` se guarda automáticamente
   - Verifica que la OT se crea con estado "ABIERTA"

3. **Obtener OT**
   - Ejecuta "4. Órdenes de Trabajo > Obtener OT por ID"
   - Verifica que retorna todos los datos de la OT

4. **Timeline de OT**
   - Ejecuta "4. Órdenes de Trabajo > Timeline de OT"
   - Usa el `ot_id` guardado
   - Verifica que retorna timeline consolidado con cambios, comentarios, evidencias

5. **Comentarios en OT**
   - Ejecuta "4. Órdenes de Trabajo > Crear Comentario"
   - Body: `{"contenido": "Comentario con @usuario mencionado", "menciones": ["@usuario"]}`
   - Verifica que se crea comentario y notifica a usuarios mencionados

### Flujo 5: Subir Evidencia

1. **Obtener Presigned URL**
   - Ejecuta "5. Evidencias > Obtener Presigned URL"
   - Verifica que retorna `upload.url` y `file_url`
   - Las variables se guardan automáticamente

2. **Subir Archivo a S3** (Manual)
   - Usa la `presigned_url` obtenida
   - En Postman, crea un nuevo request tipo POST
   - Body: form-data
   - Agrega los campos de `upload.fields` de la respuesta
   - Agrega el archivo en el campo "file"
   - Ejecuta el request

3. **Crear Evidencia**
   - Ejecuta "5. Evidencias > Crear Evidencia"
   - Verifica que se crea correctamente
   - Guarda `evidencia_id`

4. **Invalidar Evidencia**
   - Ejecuta "5. Evidencias > Invalidar Evidencia"
   - Usa el `evidencia_id` guardado
   - Body: `{"motivo_invalidacion": "Foto borrosa, requiere retomar"}`
   - Verifica que se marca como invalidada y se crea nueva versión

5. **Listar Evidencias**
   - Ejecuta "5. Evidencias > Listar Evidencias"
   - Verifica que aparece la evidencia creada
   - Verifica que muestra versiones si fue invalidada

### Flujo 6: Gestión de Choferes
1. **Listar Choferes**
   - Ejecuta "6. Choferes > Listar Choferes"
   - Verifica que retorna lista paginada de choferes
   - Verifica filtros por zona, activo, etc.

2. **Crear Chofer**
   - Ejecuta "6. Choferes > Crear Chofer"
   - Body: `{"nombre_completo": "Juan Pérez", "rut": "123456789", "zona": "Zona Centro", ...}`
   - Verifica que se crea correctamente y se guarda `chofer_id`
   - Verifica que se crea un usuario asociado con rol CHOFER

3. **Obtener Chofer**
   - Ejecuta "6. Choferes > Obtener Chofer por ID"
   - Usa el `chofer_id` guardado
   - Verifica que retorna todos los datos del chofer

4. **Asignar Vehículo a Chofer**
   - Ejecuta "6. Choferes > Asignar Vehículo a Chofer"
   - Body: `{"vehiculo_id": "{{vehicle_id}}"}`
   - Verifica que se asigna correctamente
   - Verifica que se crea registro en historial

5. **Historial de Asignaciones**
   - Ejecuta "6. Choferes > Historial de Asignaciones"
   - Verifica que retorna historial completo del chofer

### Flujo 7: Generar Reportes

1. **Dashboard Ejecutivo**
   - Ejecuta "7. Reportes > Dashboard Ejecutivo"
   - Verifica que retorna KPIs y datos

2. **Generar PDF**
   - Ejecuta "7. Reportes > Generar PDF Diario"
   - Verifica que descarga un PDF válido
   - Cambia `tipo` a "semanal" o "mensual" para otros reportes

## 🧪 Pruebas de Seguridad

### Probar Acceso No Autorizado

1. Elimina o invalida `access_token`
2. Intenta acceder a cualquier endpoint protegido
3. Verifica que retorna 401 Unauthorized

### Probar Permisos por Roles

1. Login con usuario MECANICO
2. Intenta acceder a "Listar Usuarios"
3. Verifica que retorna 403 Forbidden

### Probar Validaciones

1. Intenta crear usuario sin campos obligatorios
2. Verifica que retorna 400 Bad Request con errores
3. Intenta crear OT con vehículo inexistente
4. Verifica que retorna error de validación

## 📊 Ejecutar con Newman (CLI)

```bash
# Instalar Newman
npm install -g newman

# Ejecutar colección completa
newman run postman/PGF_API_Collection.json \
  -e postman/PGF_Local_Environment.json \
  --reporters cli,html \
  --reporter-html-export test-results/postman-report.html

# Ejecutar solo una carpeta
newman run postman/PGF_API_Collection.json \
  -e postman/PGF_Local_Environment.json \
  --folder "1. Autenticación"
```

## 🔄 Integración CI/CD

```yaml
# GitHub Actions
- name: Run Postman Tests
  run: |
    newman run postman/PGF_API_Collection.json \
      -e postman/PGF_CI_Environment.json \
      --reporters junit \
      --reporter-junit-export test-results/postman-junit.xml
```

## 📝 Endpoints Disponibles

### Autenticación
- `POST /api/v1/auth/login/` - Login con username/password
- `POST /api/v1/auth/refresh/` - Refrescar token de acceso
- `GET /api/v1/auth/me/` - Obtener usuario actual

### Usuarios
- `GET /api/v1/users/` - Listar usuarios (requiere ADMIN/SUPERVISOR)
- `POST /api/v1/users/` - Crear usuario (público)
- `GET /api/v1/users/{id}/` - Obtener usuario por ID
- `PUT/PATCH /api/v1/users/{id}/` - Actualizar usuario
- `DELETE /api/v1/users/{id}/` - Eliminar usuario (no permite eliminar permanentes)

### Vehículos
- `GET /api/v1/vehicles/` - Listar vehículos
- `POST /api/v1/vehicles/` - Crear vehículo
- `POST /api/v1/vehicles/ingreso/` - Registrar ingreso de vehículo
- `POST /api/v1/vehicles/salida/` - Registrar salida de vehículo
- `GET /api/v1/vehicles/ingresos-hoy/` - Listar ingresos del día
- `GET /api/v1/vehicles/ingreso/{ingreso_id}/ticket/` - Generar ticket PDF

### Choferes (Drivers)
- `GET /api/v1/drivers/choferes/` - Listar choferes
- `POST /api/v1/drivers/choferes/` - Crear chofer
- `GET /api/v1/drivers/choferes/{id}/` - Obtener chofer por ID
- `PUT/PATCH /api/v1/drivers/choferes/{id}/` - Actualizar chofer
- `DELETE /api/v1/drivers/choferes/{id}/` - Eliminar chofer
- `POST /api/v1/drivers/choferes/{id}/asignar-vehiculo/` - Asignar vehículo a chofer
- `GET /api/v1/drivers/choferes/{id}/historial/` - Historial de asignaciones
- `GET /api/v1/drivers/historial/` - Listar todo el historial de asignaciones

### Órdenes de Trabajo
- `GET /api/v1/work/ordenes/` - Listar órdenes de trabajo
- `POST /api/v1/work/ordenes/` - Crear orden de trabajo
- `GET /api/v1/work/ordenes/{ot_id}/` - Obtener OT por ID
- `GET /api/v1/work/ordenes/{ot_id}/timeline/` - Timeline consolidado de OT
- `GET /api/v1/work/comentarios/?ot={ot_id}` - Listar comentarios de OT
- `POST /api/v1/work/comentarios/` - Crear comentario en OT

### Evidencias
- `POST /api/v1/work/evidencias/presigned/` - Obtener presigned URL para subir
- `GET /api/v1/work/evidencias/?ot={ot_id}` - Listar evidencias
- `POST /api/v1/work/evidencias/` - Crear evidencia
- `POST /api/v1/work/evidencias/{id}/invalidar/` - Invalidar evidencia

### Reportes
- `GET /api/v1/reports/dashboard-ejecutivo/` - Dashboard ejecutivo
- `GET /api/v1/reports/pdf/` - Generar PDF de reportes

## ⚙️ Configuración de URL Base

### Para Desarrollo Local (sin Docker)
```
base_url = http://localhost:8000/api/v1
```

### Para Docker
```
base_url = http://localhost:8000/api/v1
```
(Desde el host, el puerto 8000 está mapeado al contenedor)

### Para Producción
```
base_url = https://api.tudominio.com/api/v1
```

**Importante**: La variable `base_url` debe incluir `/api/v1` al final. Todos los endpoints se construyen como `{{base_url}}/endpoint/`.

## 📝 Notas

- Los tokens JWT expiran en 1 hora por defecto
- Algunos endpoints requieren roles específicos (ADMIN, SUPERVISOR, etc.)
- Las variables se actualizan automáticamente con scripts de test
- Para pruebas de carga, usa Postman Runner con múltiples iteraciones
- **Credenciales por defecto**: admin / admin123 (usuario permanente)
- Los usuarios permanentes no se pueden eliminar, solo editar y ver

