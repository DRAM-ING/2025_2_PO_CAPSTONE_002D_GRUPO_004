# Diagrama de Arquitectura Completo - Flujo de Trabajo OT

## Diagrama de Arquitectura con Flujo de Trabajo OT

```mermaid
graph TB
    subgraph PRESENTACION["🎨 CAPA DE PRESENTACIÓN"]
        WEB[Web App<br/>Browser]
        MOBILE[Mobile Browser]
        TABLET[Tablet Guardia]
    end
    
    subgraph FRONTEND["💻 Frontend Next.js 15"]
        SSR[Server Side Rendering<br/>App Router]
        STORE[Zustand Store<br/>Estado Global]
        SSR --> STORE
    end
    
    subgraph GATEWAY["🌐 API Gateway"]
        NGINX[Nginx Reverse Proxy<br/>Load Balancer & SSL]
    end
    
    subgraph NEGOCIO["⚙️ CAPA DE NEGOCIO - Backend Django 5"]
        DRF[Django REST Framework<br/>API Endpoints]
        CELERY[Celery Workers<br/>Tareas Asíncronas]
        CHANNELS[Django Channels<br/>WebSockets]
        UPLOAD[Upload/Download<br/>File Handler]
    end
    
    subgraph EXTERNOS["🔌 Servicios Externos"]
        EMAIL[Email Service]
        MONITOR[Prometheus/Grafana<br/>Monitoring]
    end
    
    subgraph DATOS["💾 CAPA DE DATOS"]
        PG[(PostgreSQL 15<br/>Master/Slave)]
        REDIS[Redis 7<br/>Cache & Broker]
        S3[AWS S3 / LocalStack<br/>Media Storage]
    end
    
    %% Conexiones Capa de Presentación
    WEB -->|HTTPS/WSS| SSR
    MOBILE -->|HTTPS/WSS| SSR
    TABLET -->|HTTPS/WSS| SSR
    
    %% Frontend a Gateway
    SSR -->|HTTPS| NGINX
    
    %% Gateway a Backend
    NGINX -->|Proxy Pass| DRF
    NGINX -->|Upgrade WS| CHANNELS
    
    %% Backend - Django REST Framework
    DRF -->|Query/Transacción| PG
    DRF -->|Trigger Task| CELERY
    DRF -->|Cache/Session| REDIS
    DRF -->|Send Mail| EMAIL
    DRF -->|Upload/Download| UPLOAD
    
    %% Backend - Celery Workers
    CELERY -->|Store Result| PG
    CELERY -->|Broker| REDIS
    CELERY -->|Upload Files| S3
    
    %% Backend - Django Channels
    CHANNELS -->|Sub/Pub| REDIS
    CHANNELS -->|Broker| REDIS
    
    %% Backend - Upload/Download
    UPLOAD -->|PUT/GET| S3
    
    %% Estilos
    style PRESENTACION fill:#e1f5ff
    style FRONTEND fill:#e3f2fd
    style GATEWAY fill:#f3e5f5
    style NEGOCIO fill:#fff4e1
    style EXTERNOS fill:#fce4ec
    style DATOS fill:#e8f5e9
```

## Diagrama de Flujo de Trabajo OT (3 Capas)

```mermaid
graph TB
    subgraph PRESENTACION["🎨 CAPA DE PRESENTACIÓN"]
        USUARIO_GUARDIA[👤 Guardia<br/>Crea OT]
        USUARIO_SUPER[👤 Supervisor<br/>Asigna Mecánico]
        USUARIO_MEC[👤 Mecánico<br/>Trabaja en OT]
        USUARIO_JEFE[👤 Jefe Taller<br/>Cierra OT]
    end
    
    subgraph FRONTEND["💻 Frontend Next.js"]
        FORM_CREATE[Formulario Crear OT<br/>/workorders/create]
        FORM_ASIGNAR[Formulario Asignar<br/>/workorders/id]
        FORM_TRABAJO[Formulario Trabajo<br/>/workorders/id]
        FORM_CIERRE[Formulario Cerrar<br/>/workorders/id/cerrar]
    end
    
    subgraph GATEWAY["🌐 API Gateway"]
        PROXY[Proxy Routes<br/>/api/proxy/work/]
    end
    
    subgraph NEGOCIO["⚙️ CAPA DE NEGOCIO"]
        API_CREATE[API: POST /work/ordenes/<br/>Crea OT ABIERTA/EN_PAUSA]
        API_ASIGNAR[API: POST /aprobar-asignacion/<br/>Transición a EN_EJECUCION]
        API_ITEMS[API: POST /items/<br/>Agrega Items]
        API_EVIDENCIAS[API: POST /evidencias/<br/>Sube Archivos]
        API_QA[API: POST /en-qa/<br/>Envía a QA]
        API_CERRAR[API: POST /cerrar/<br/>Cierra OT]
        
        CELERY_COLACION[Celery Beat<br/>Colación 12:30-13:15]
        CELERY_PDF[Celery Worker<br/>Genera PDF]
    end
    
    subgraph DATOS["💾 CAPA DE DATOS"]
        PG_OT[(PostgreSQL<br/>OrdenTrabajo)]
        PG_ITEMS[(PostgreSQL<br/>ItemOT)]
        PG_EVID[(PostgreSQL<br/>Evidencia)]
        PG_PAUSA[(PostgreSQL<br/>Pausa)]
        
        REDIS_TASK[Redis<br/>Broker Tareas]
        REDIS_CACHE[Redis<br/>Cache]
        
        S3_FILES[S3/LocalStack<br/>Archivos & PDFs]
    end
    
    %% Flujo 1: Creación de OT
    USUARIO_GUARDIA -->|1. Crea OT| FORM_CREATE
    FORM_CREATE -->|POST| PROXY
    PROXY -->|POST /work/ordenes/| API_CREATE
    API_CREATE -->|INSERT| PG_OT
    PG_OT -->|Response| API_CREATE
    API_CREATE -->|Response| FORM_CREATE
    FORM_CREATE -->|Muestra OT| USUARIO_GUARDIA
    
    %% Flujo 2: Asignación de Mecánico
    USUARIO_SUPER -->|2. Asigna Mecánico| FORM_ASIGNAR
    FORM_ASIGNAR -->|POST| PROXY
    PROXY -->|POST /aprobar-asignacion/| API_ASIGNAR
    API_ASIGNAR -->|UPDATE estado: EN_EJECUCION| PG_OT
    PG_OT -->|Response| API_ASIGNAR
    API_ASIGNAR -->|Notifica| CHANNELS_WS
    CHANNELS_WS -->|WebSocket| FORM_ASIGNAR
    
    %% Flujo 3: Trabajo en OT
    USUARIO_MEC -->|3. Agrega Items| FORM_TRABAJO
    FORM_TRABAJO -->|POST /items/| PROXY
    PROXY -->|POST| API_ITEMS
    API_ITEMS -->|INSERT| PG_ITEMS
    
    USUARIO_MEC -->|4. Sube Evidencias| FORM_TRABAJO
    FORM_TRABAJO -->|POST /evidencias/| PROXY
    PROXY -->|POST| API_EVIDENCIAS
    API_EVIDENCIAS -->|PUT archivo| S3_FILES
    API_EVIDENCIAS -->|INSERT| PG_EVID
    
    %% Flujo 4: Colación Automática
    CELERY_COLACION -->|12:30 Programa| REDIS_TASK
    REDIS_TASK -->|Consume| CELERY_COLACION
    CELERY_COLACION -->|INSERT Pausa| PG_PAUSA
    CELERY_COLACION -->|UPDATE EN_PAUSA| PG_OT
    
    CELERY_COLACION -->|13:15 Finaliza| REDIS_TASK
    REDIS_TASK -->|Consume| CELERY_COLACION
    CELERY_COLACION -->|UPDATE Pausa| PG_PAUSA
    CELERY_COLACION -->|UPDATE EN_EJECUCION| PG_OT
    
    %% Flujo 5: Envío a QA
    USUARIO_MEC -->|5. Envía a QA| FORM_TRABAJO
    FORM_TRABAJO -->|POST /en-qa/| PROXY
    PROXY -->|POST| API_QA
    API_QA -->|UPDATE EN_QA| PG_OT
    
    %% Flujo 6: Cierre de OT
    USUARIO_JEFE -->|6. Cierra OT| FORM_CIERRE
    FORM_CIERRE -->|POST /cerrar/| PROXY
    PROXY -->|POST| API_CERRAR
    API_CERRAR -->|UPDATE CERRADA| PG_OT
    API_CERRAR -->|Tarea PDF| REDIS_TASK
    REDIS_TASK -->|Consume| CELERY_PDF
    CELERY_PDF -->|SELECT datos| PG_OT
    CELERY_PDF -->|Genera PDF| CELERY_PDF
    CELERY_PDF -->|PUT PDF| S3_FILES
    CELERY_PDF -->|INSERT Evidencia| PG_EVID
    
    %% WebSocket para notificaciones
    CHANNELS_WS[Django Channels<br/>WebSocket]
    CHANNELS_WS -->|Sub/Pub| REDIS_CACHE
    CHANNELS_WS -->|Notifica cambios| FORM_ASIGNAR
    CHANNELS_WS -->|Notifica cambios| FORM_TRABAJO
    
    %% Estilos
    style PRESENTACION fill:#e1f5ff
    style FRONTEND fill:#e3f2fd
    style GATEWAY fill:#f3e5f5
    style NEGOCIO fill:#fff4e1
    style DATOS fill:#e8f5e9
```

## Diagrama Detallado de Flujo OT (Paso a Paso)

```mermaid
sequenceDiagram
    participant G as Guardia
    participant F as Frontend
    participant P as Proxy
    participant API as API Django
    participant PG as PostgreSQL
    participant CB as Celery Beat
    participant R as Redis
    participant W as Worker
    participant S3 as LocalStack
    participant S as Supervisor
    participant M as Mecanico
    participant J as Jefe Taller
    
    Note over G,PG: 1. CREACIÓN DE OT
    G->>F: Crea OT (formulario)
    F->>P: POST /api/proxy/work/ordenes/
    P->>API: POST /work/ordenes/
    API->>PG: INSERT OrdenTrabajo (ABIERTA/EN_PAUSA)
    PG-->>API: OT creada
    API-->>F: Response {id, estado}
    F-->>G: Muestra OT creada
    
    Note over S,PG: 2. ASIGNACIÓN DE MECÁNICO
    S->>F: Asigna mecánico
    F->>P: POST /api/proxy/work/ordenes/{id}/aprobar-asignacion/
    P->>API: POST /aprobar-asignacion/
    API->>PG: UPDATE mecanico_id, estado: EN_EJECUCION
    PG-->>API: Actualizado
    API-->>F: Estado: EN_EJECUCION
    F-->>S: Muestra estado actualizado
    
    Note over M,PG: 3. TRABAJO EN OT
    M->>F: Agrega items
    F->>P: POST /api/proxy/work/items/
    P->>API: POST /items/
    API->>PG: INSERT ItemOT
    PG-->>API: Item creado
    
    M->>F: Sube evidencias
    F->>P: POST /api/proxy/work/evidencias/presigned/
    P->>API: POST /evidencias/presigned/
    API->>S3: PUT archivo
    S3-->>API: Archivo subido
    API->>PG: INSERT Evidencia
    PG-->>API: Evidencia creada
    API-->>F: URL pública
    F-->>M: Muestra evidencia
    
    Note over CB,PG: 4. COLACIÓN AUTOMÁTICA
    CB->>R: Programa tarea 12:30
    R->>W: Consume tarea
    W->>PG: INSERT Pausa (tipo: COLACION)
    W->>PG: UPDATE estado: EN_PAUSA
    PG-->>W: Actualizado
    
    CB->>R: Programa tarea 13:15
    R->>W: Consume tarea
    W->>PG: UPDATE Pausa (fin)
    W->>PG: UPDATE estado: EN_EJECUCION
    PG-->>W: Actualizado
    
    Note over M,PG: 5. ENVÍO A QA
    M->>F: Envía a QA
    F->>P: POST /api/proxy/work/ordenes/{id}/en-qa/
    P->>API: POST /en-qa/
    API->>PG: UPDATE estado: EN_QA
    PG-->>API: Actualizado
    API-->>F: Estado: EN_QA
    F-->>M: Muestra estado
    
    Note over J,S3: 6. CIERRE DE OT
    J->>F: Cierra OT
    F->>P: POST /api/proxy/work/ordenes/{id}/cerrar/
    P->>API: POST /cerrar/
    API->>PG: UPDATE estado: CERRADA, cierre
    API->>R: Tarea: generar_pdf_cierre
    R->>W: Consume tarea
    W->>PG: SELECT OT (datos completos)
    PG-->>W: Datos de OT
    W->>W: Genera PDF (ReportLab)
    W->>S3: PUT PDF
    S3-->>W: PDF subido
    W->>PG: INSERT Evidencia (PDF)
    PG-->>W: Evidencia creada
    W->>R: Resultado (URL PDF)
    API-->>F: OT cerrada + URL PDF
    F-->>J: Muestra PDF
```

## Diagrama de Estados con Roles

```mermaid
stateDiagram-v2
    [*] --> ABIERTA
    
    ABIERTA --> EN_PAUSA: Sin mecanico
    ABIERTA --> EN_DIAGNOSTICO: JEFE_TALLER
    ABIERTA --> EN_EJECUCION: SUPERVISOR asigna
    
    EN_DIAGNOSTICO --> EN_EJECUCION: JEFE_TALLER finaliza
    EN_DIAGNOSTICO --> ABIERTA: Error
    
    EN_PAUSA --> EN_EJECUCION: SUPERVISOR asigna
    EN_PAUSA --> EN_EJECUCION: MECANICO reanuda
    EN_PAUSA --> EN_EJECUCION: Celery Beat finaliza colacion
    
    EN_EJECUCION --> EN_PAUSA: MECANICO pausa
    EN_EJECUCION --> EN_PAUSA: Celery Beat colacion
    EN_EJECUCION --> EN_QA: MECANICO envia
    
    EN_QA --> CERRADA: JEFE_TALLER aprueba
    EN_QA --> EN_EJECUCION: SUPERVISOR rechaza menor
    EN_QA --> RETRABAJO: SUPERVISOR rechaza mayor
    
    RETRABAJO --> EN_EJECUCION: MECANICO corrige
    RETRABAJO --> EN_QA: MECANICO correccion
    
    CERRADA --> [*]
```

## Componentes por Capa

### 🎨 Capa de Presentación
- **Web App**: Navegador web estándar
- **Mobile Browser**: Navegadores móviles
- **Tablet Guardia**: Tablets para guardias en terreno

### 💻 Frontend
- **Next.js 15**: Framework React con SSR
- **App Router**: Sistema de rutas de Next.js
- **Zustand Store**: Gestión de estado global

### 🌐 API Gateway
- **Nginx**: Reverse proxy, load balancer y SSL termination

### ⚙️ Capa de Negocio
- **Django REST Framework**: API REST principal
- **Celery Workers**: Tareas asíncronas (PDFs, colación)
- **Celery Beat**: Programador de tareas periódicas
- **Django Channels**: WebSockets para notificaciones en tiempo real
- **Upload/Download Handler**: Gestión de archivos

### 💾 Capa de Datos
- **PostgreSQL 15**: Base de datos principal (Master/Slave)
- **Redis 7**: Cache y broker de mensajes
- **AWS S3 / LocalStack**: Almacenamiento de archivos

### 🔌 Servicios Externos
- **Email Service**: Envío de correos
- **Prometheus/Grafana**: Monitoreo y métricas

