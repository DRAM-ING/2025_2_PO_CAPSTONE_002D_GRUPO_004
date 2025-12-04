# Diagramas Mermaid - Solo Código

Copia solo el código dentro de los bloques ```mermaid para usar en Mermaid Live Editor o cualquier herramienta compatible.

---

## Diagrama 1: Completo (3 Capas)

```mermaid
graph TB
    subgraph PRESENTACION["CAPA DE PRESENTACION"]
        USUARIO[Usuario GUARDIA/SUPERVISOR/JEFE_TALLER/MECANICO]
        FRONTEND[Frontend Next.js /workorders/create /workorders/id]
        CLOUDFLARE[Cloudflare Tunnel HTTPS Publico]
    end
    
    subgraph NEGOCIO["CAPA DE NEGOCIO"]
        API[API Django OrdenTrabajoViewSet ItemOTViewSet EvidenciaViewSet]
        WORKER[Worker Celery Tareas Asincronas]
        BEAT[Celery Beat Tareas Programadas]
        REDIS_BROKER[Redis Broker & Cache]
    end
    
    subgraph DATOS["CAPA DE DATOS"]
        POSTGRES[(PostgreSQL OrdenTrabajo ItemOT Evidencia Pausa Checklist)]
        LOCALSTACK[LocalStack S3 Archivos & PDFs]
        REDIS_CACHE[Redis Cache & Results]
    end
    
    USUARIO -->|1. Interaccion| FRONTEND
    FRONTEND <-->|HTTP/WebSocket| CLOUDFLARE
    CLOUDFLARE <-->|Proxy| API
    API <-->|Lee/Escribe| POSTGRES
    API -->|Sube archivos| LOCALSTACK
    API <-->|Cache| REDIS_CACHE
    API -->|Envia tareas| REDIS_BROKER
    BEAT -->|Programa tareas| REDIS_BROKER
    REDIS_BROKER -->|Consume| WORKER
    WORKER <-->|Lee/Escribe| POSTGRES
    WORKER -->|Sube PDFs| LOCALSTACK
    WORKER <-->|Resultados| REDIS_CACHE
    
    style PRESENTACION fill:#e1f5ff
    style NEGOCIO fill:#fff4e1
    style DATOS fill:#e8f5e9
```

---

## Diagrama 2: Estados

```mermaid
stateDiagram-v2
    [*] --> ABIERTA
    
    ABIERTA --> EN_DIAGNOSTICO
    ABIERTA --> EN_PAUSA
    ABIERTA --> EN_EJECUCION
    
    EN_DIAGNOSTICO --> EN_EJECUCION
    EN_DIAGNOSTICO --> ABIERTA
    
    EN_PAUSA --> EN_EJECUCION
    
    EN_EJECUCION --> EN_PAUSA
    EN_EJECUCION --> EN_QA
    
    EN_QA --> CERRADA
    EN_QA --> EN_EJECUCION
    EN_QA --> RETRABAJO
    
    RETRABAJO --> EN_EJECUCION
    RETRABAJO --> EN_QA
    
    CERRADA --> [*]
```

---

## Diagrama 3: Secuencia

```mermaid
sequenceDiagram
    participant U as Usuario
    participant F as Frontend
    participant API as API Django
    participant PG as PostgreSQL
    participant W as Worker Celery
    participant LS as LocalStack
    participant CB as Celery Beat
    participant R as Redis
    
    Note over U,R: 1. CREACION DE OT
    U->>F: Crea OT formulario
    F->>API: POST /work/ordenes/
    API->>PG: INSERT OrdenTrabajo ABIERTA
    PG-->>API: OT creada
    API-->>F: Response
    F-->>U: Muestra OT
    
    Note over U,R: 2. ASIGNACION DE MECANICO
    U->>F: Asigna mecanico
    F->>API: POST /aprobar-asignacion/
    API->>PG: UPDATE EN_EJECUCION
    PG-->>API: Actualizado
    API-->>F: Estado actualizado
    F-->>U: Muestra estado
    
    Note over U,R: 3. TRABAJO EN OT
    U->>F: Agrega items / Sube evidencias
    F->>API: POST /items/ o /evidencias/
    API->>PG: INSERT ItemOT/Evidencia
    API->>LS: PUT archivo
    LS-->>API: Archivo subido
    API-->>F: Item/Evidencia creada
    F-->>U: Actualiza UI
    
    Note over U,R: 4. COLACION AUTOMATICA
    CB->>R: Programa tarea 12:30
    R->>W: Consume tarea
    W->>PG: INSERT Pausa UPDATE EN_PAUSA
    PG-->>W: Actualizado
    
    Note over U,R: 5. ENVIO A QA
    U->>F: Envia a QA
    F->>API: POST /en-qa/
    API->>PG: UPDATE EN_QA
    PG-->>API: Actualizado
    API-->>F: Estado EN_QA
    F-->>U: Muestra estado
    
    Note over U,R: 6. CIERRE DE OT
    U->>F: Cierra OT
    F->>API: POST /cerrar/
    API->>PG: UPDATE CERRADA
    API->>R: Tarea generar_pdf_cierre
    R->>W: Consume tarea
    W->>PG: SELECT OT datos completos
    PG-->>W: Datos de OT
    W->>W: Genera PDF ReportLab
    W->>LS: PUT PDF
    LS-->>W: PDF subido
    W->>PG: INSERT Evidencia PDF
    W->>R: Resultado URL PDF
    API-->>F: OT cerrada + URL PDF
    F-->>U: Muestra PDF
```

---

## Diagrama 4: Componentes por Capa

```mermaid
graph LR
    subgraph PRES["PRESENTACION"]
        A[Frontend Next.js]
        B[Cloudflare Tunnel]
    end
    
    subgraph NEG["NEGOCIO"]
        C[API Django]
        D[Worker Celery]
        E[Celery Beat]
    end
    
    subgraph DAT["DATOS"]
        F[(PostgreSQL)]
        G[LocalStack]
        H[Redis]
    end
    
    A <--> B
    B <--> C
    C <--> F
    C <--> G
    C <--> H
    D <--> F
    D <--> G
    D <--> H
    E --> H
    H --> D
    
    style PRES fill:#e1f5ff
    style NEG fill:#fff4e1
    style DAT fill:#e8f5e9
```

---

## Diagrama 5: Flujo Creación OT

```mermaid
flowchart LR
    A[Usuario] -->|Datos| B[Frontend]
    B -->|POST| C[API Django]
    C -->|Valida| C
    C -->|INSERT| D[(PostgreSQL)]
    D -->|Response| C
    C -->|Response| B
    B -->|Muestra| A
    
    style A fill:#ffebee
    style B fill:#e1f5ff
    style C fill:#fff4e1
    style D fill:#e8f5e9
```

---

## Diagrama 6: Flujo Subida Evidencia

```mermaid
flowchart LR
    A[Usuario] -->|Archivo| B[Frontend]
    B -->|FormData| C[API Django]
    C -->|Valida| C
    C -->|PUT| D[LocalStack]
    C -->|INSERT| E[(PostgreSQL)]
    D -->|URL| C
    E -->|Response| C
    C -->|URL publica| B
    B -->|Muestra| A
    
    style A fill:#ffebee
    style B fill:#e1f5ff
    style C fill:#fff4e1
    style D fill:#fff3e0
    style E fill:#e8f5e9
```

---

## Diagrama 7: Flujo Generación PDF

```mermaid
flowchart LR
    A[Usuario] -->|Cierra OT| B[Frontend]
    B -->|POST /cerrar/| C[API Django]
    C -->|UPDATE| D[(PostgreSQL)]
    C -->|Tarea| E[Redis]
    E -->|Consume| F[Worker Celery]
    F -->|SELECT| D
    D -->|Datos| F
    F -->|Genera| F
    F -->|PUT PDF| G[LocalStack]
    F -->|INSERT| D
    F -->|Resultado| E
    C -->|URL PDF| B
    B -->|Muestra PDF| A
    
    style A fill:#ffebee
    style B fill:#e1f5ff
    style C fill:#fff4e1
    style D fill:#e8f5e9
    style E fill:#f3e5f5
    style F fill:#e0f2f1
    style G fill:#fff3e0
```

---

## Diagrama 8: Arquitectura Completa

```mermaid
graph TB
    subgraph PRESENTACION["CAPA DE PRESENTACION"]
        USUARIO[Usuario]
        FRONTEND[Frontend Next.js]
        CLOUDFLARE[Cloudflare Tunnel]
    end
    
    subgraph NEGOCIO["CAPA DE NEGOCIO"]
        API[API Django]
        WORKER[Worker Celery]
        BEAT[Celery Beat]
    end
    
    subgraph DATOS["CAPA DE DATOS"]
        POSTGRES[(PostgreSQL)]
        LOCALSTACK[LocalStack S3]
        REDIS[Redis]
    end
    
    USUARIO --> FRONTEND
    FRONTEND <--> CLOUDFLARE
    CLOUDFLARE <--> API
    API <--> POSTGRES
    API --> LOCALSTACK
    API <--> REDIS
    BEAT --> REDIS
    REDIS --> WORKER
    WORKER <--> POSTGRES
    WORKER --> LOCALSTACK
    WORKER <--> REDIS
    
    style PRESENTACION fill:#e1f5ff
    style NEGOCIO fill:#fff4e1
    style DATOS fill:#e8f5e9
```

---

## Diagrama 9: Arquitectura Sistema Completo

```mermaid
graph TB
    subgraph PRESENTACION["CAPA DE PRESENTACION"]
        WEB[Web App Browser]
        MOBILE[Mobile Browser]
        TABLET[Tablet Guardia]
    end
    
    subgraph FRONTEND["Frontend Next.js 15"]
        SSR[Server Side Rendering App Router]
        STORE[Zustand Store Estado Global]
        SSR --> STORE
    end
    
    subgraph GATEWAY["API Gateway"]
        NGINX[Nginx Reverse Proxy Load Balancer & SSL]
    end
    
    subgraph NEGOCIO["CAPA DE NEGOCIO - Backend Django 5"]
        DRF[Django REST Framework API Endpoints]
        CELERY[Celery Workers Tareas Asincronas]
        CHANNELS[Django Channels WebSockets]
        UPLOAD[Upload/Download File Handler]
    end
    
    subgraph EXTERNOS["Servicios Externos"]
        EMAIL[Email Service]
        MONITOR[Prometheus/Grafana Monitoring]
    end
    
    subgraph DATOS["CAPA DE DATOS"]
        PG[(PostgreSQL 15 Master/Slave)]
        REDIS[Redis 7 Cache & Broker]
        S3[AWS S3 / LocalStack Media Storage]
    end
    
    WEB -->|HTTPS/WSS| SSR
    MOBILE -->|HTTPS/WSS| SSR
    TABLET -->|HTTPS/WSS| SSR
    
    SSR -->|HTTPS| NGINX
    
    NGINX -->|Proxy Pass| DRF
    NGINX -->|Upgrade WS| CHANNELS
    
    DRF -->|Query/Transaccion| PG
    DRF -->|Trigger Task| CELERY
    DRF -->|Cache/Session| REDIS
    DRF -->|Send Mail| EMAIL
    DRF -->|Upload/Download| UPLOAD
    
    CELERY -->|Store Result| PG
    CELERY -->|Broker| REDIS
    CELERY -->|Upload Files| S3
    
    CHANNELS -->|Sub/Pub| REDIS
    CHANNELS -->|Broker| REDIS
    
    UPLOAD -->|PUT/GET| S3
    
    style PRESENTACION fill:#e1f5ff
    style FRONTEND fill:#e3f2fd
    style GATEWAY fill:#f3e5f5
    style NEGOCIO fill:#fff4e1
    style EXTERNOS fill:#fce4ec
    style DATOS fill:#e8f5e9
```

---

## Diagrama 10: Flujo Trabajo OT Completo

```mermaid
graph TB
    subgraph PRESENTACION["CAPA DE PRESENTACION"]
        GUARDIA[Guardia Crea OT]
        SUPERVISOR[Supervisor Asigna Mecanico]
        MECANICO[Mecanico Trabaja en OT]
        JEFE[Jefe Taller Cierra OT]
    end
    
    subgraph FRONTEND["Frontend Next.js"]
        FORM_CREATE[Formulario Crear OT]
        FORM_ASIGNAR[Formulario Asignar]
        FORM_TRABAJO[Formulario Trabajo]
        FORM_CIERRE[Formulario Cerrar]
    end
    
    subgraph GATEWAY["API Gateway"]
        PROXY[Proxy Routes /api/proxy/work/]
    end
    
    subgraph NEGOCIO["CAPA DE NEGOCIO"]
        API_CREATE[API POST /work/ordenes/ Crea OT]
        API_ASIGNAR[API POST /aprobar-asignacion/]
        API_ITEMS[API POST /items/ Agrega Items]
        API_EVIDENCIAS[API POST /evidencias/ Sube Archivos]
        API_QA[API POST /en-qa/ Envia a QA]
        API_CERRAR[API POST /cerrar/ Cierra OT]
        CELERY_COLACION[Celery Beat Colacion 12:30-13:15]
        CELERY_PDF[Celery Worker Genera PDF]
    end
    
    subgraph DATOS["CAPA DE DATOS"]
        PG_OT[(PostgreSQL OrdenTrabajo)]
        PG_ITEMS[(PostgreSQL ItemOT)]
        PG_EVID[(PostgreSQL Evidencia)]
        PG_PAUSA[(PostgreSQL Pausa)]
        REDIS_TASK[Redis Broker Tareas]
        REDIS_CACHE[Redis Cache]
        S3_FILES[S3/LocalStack Archivos & PDFs]
    end
    
    GUARDIA -->|1. Crea OT| FORM_CREATE
    FORM_CREATE -->|POST| PROXY
    PROXY -->|POST /work/ordenes/| API_CREATE
    API_CREATE -->|INSERT| PG_OT
    
    SUPERVISOR -->|2. Asigna| FORM_ASIGNAR
    FORM_ASIGNAR -->|POST| PROXY
    PROXY -->|POST /aprobar-asignacion/| API_ASIGNAR
    API_ASIGNAR -->|UPDATE EN_EJECUCION| PG_OT
    
    MECANICO -->|3. Agrega Items| FORM_TRABAJO
    FORM_TRABAJO -->|POST /items/| PROXY
    PROXY -->|POST| API_ITEMS
    API_ITEMS -->|INSERT| PG_ITEMS
    
    MECANICO -->|4. Sube Evidencias| FORM_TRABAJO
    FORM_TRABAJO -->|POST /evidencias/| PROXY
    PROXY -->|POST| API_EVIDENCIAS
    API_EVIDENCIAS -->|PUT archivo| S3_FILES
    API_EVIDENCIAS -->|INSERT| PG_EVID
    
    CELERY_COLACION -->|12:30 Programa| REDIS_TASK
    REDIS_TASK -->|Consume| CELERY_COLACION
    CELERY_COLACION -->|INSERT Pausa UPDATE EN_PAUSA| PG_PAUSA
    CELERY_COLACION -->|UPDATE| PG_OT
    
    MECANICO -->|5. Envia a QA| FORM_TRABAJO
    FORM_TRABAJO -->|POST /en-qa/| PROXY
    PROXY -->|POST| API_QA
    API_QA -->|UPDATE EN_QA| PG_OT
    
    JEFE -->|6. Cierra OT| FORM_CIERRE
    FORM_CIERRE -->|POST /cerrar/| PROXY
    PROXY -->|POST| API_CERRAR
    API_CERRAR -->|UPDATE CERRADA| PG_OT
    API_CERRAR -->|Tarea PDF| REDIS_TASK
    REDIS_TASK -->|Consume| CELERY_PDF
    CELERY_PDF -->|SELECT datos| PG_OT
    CELERY_PDF -->|PUT PDF| S3_FILES
    CELERY_PDF -->|INSERT Evidencia| PG_EVID
    
    style PRESENTACION fill:#e1f5ff
    style FRONTEND fill:#e3f2fd
    style GATEWAY fill:#f3e5f5
    style NEGOCIO fill:#fff4e1
    style DATOS fill:#e8f5e9
```

---

## Diagrama 11: Arquitectura Completa Mejorada (Con Capa de Negocio)

```mermaid
flowchart TB
    subgraph Clientes["CAPA DE PRESENTACION - Clientes"]
        Web[Web App]
        Mobile[Mobile Browser]
        Tablet[Tablet Guardia]
    end
    
    subgraph FrontendZone["Frontend Next.js 15"]
        NextJS[Server Side Rendering App Router]
        Zustand[Zustand Store]
    end
    
    subgraph DMZ["API Gateway"]
        Nginx[Nginx Reverse Proxy Load Balancer & SSL]
    end
    
    subgraph AppLayer["Backend Django 5"]
        API[Django REST Framework]
        Channels[Django Channels WebSockets]
        Celery[Celery Workers Tareas Asincronas]
    end
    
    subgraph BusinessLayer["CAPA DE NEGOCIO"]
        OTService[Servicio Ordenes Trabajo Transiciones de Estado]
        ItemService[Servicio Items OT Gestion de Repuestos]
        EvidenceService[Servicio Evidencias Gestion de Archivos]
        ColacionService[Servicio Colacion Pausas Automaticas]
        PDFService[Servicio PDF Generacion de Documentos]
    end
    
    subgraph DataLayer["CAPA DE DATOS"]
        Postgres[("PostgreSQL 15 Master/Slave")]
        Redis[("Redis 7 Cache & Broker")]
        S3[("AWS S3 / LocalStack Media Storage")]
    end
    
    subgraph External["Servicios Externos"]
        SMTP[Email Service]
        Monitor[Prometheus/Grafana]
    end
    
    Web -->|HTTPS/WSS| NextJS
    Mobile -->|HTTPS/WSS| NextJS
    Tablet -->|HTTPS/WSS| NextJS
    NextJS -->|HTTPS| Nginx
    Nginx -->|Proxy Pass| API
    Nginx -->|Upgrade WS| Channels
    
    API -->|Llama| OTService
    API -->|Llama| ItemService
    API -->|Llama| EvidenceService
    API -->|Trigger Task| Celery
    API -->|Cache/Session| Redis
    
    Channels -->|Sub/Pub| Redis
    
    Celery -->|Ejecuta| ColacionService
    Celery -->|Ejecuta| PDFService
    Celery -->|Broker| Redis
    Celery -->|Send Mail| SMTP
    
    OTService -->|Query/Transaccion| Postgres
    ItemService -->|Query/Transaccion| Postgres
    EvidenceService -->|Query/Transaccion| Postgres
    EvidenceService -->|Upload/Download| S3
    ColacionService -->|Query/Transaccion| Postgres
    PDFService -->|Query/Transaccion| Postgres
    PDFService -->|Upload/Download| S3
    PDFService -->|Store Result| Postgres
    
    Web:::client
    Mobile:::client
    Tablet:::client
    NextJS:::frontend
    Zustand:::frontend
    Nginx:::gateway
    API:::backend
    Channels:::backend
    Celery:::backend
    OTService:::business
    ItemService:::business
    EvidenceService:::business
    ColacionService:::business
    PDFService:::business
    Postgres:::data
    Redis:::data
    S3:::data
    SMTP:::ext
    Monitor:::ext
    
    classDef client fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef frontend fill:#e0f7fa,stroke:#006064,stroke-width:2px
    classDef gateway fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef backend fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef business fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef data fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef ext fill:#eceff1,stroke:#455a64,stroke-width:2px,stroke-dasharray: 5 5
```

