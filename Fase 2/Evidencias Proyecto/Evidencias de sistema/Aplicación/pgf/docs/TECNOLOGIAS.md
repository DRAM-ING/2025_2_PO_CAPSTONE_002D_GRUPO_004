# 🛠️ Stack Tecnológico - Plataforma de Gestión de Flota (PGF)

Este documento detalla todas las tecnologías, frameworks, librerías y herramientas utilizadas en el proyecto PGF.

---

## 📋 Índice

- [Backend](#backend)
- [Frontend](#frontend)
- [Base de Datos](#base-de-datos)
- [Almacenamiento](#almacenamiento)
- [Colas y Tareas Asíncronas](#colas-y-tareas-asíncronas)
- [Comunicación en Tiempo Real](#comunicación-en-tiempo-real)
- [Autenticación y Seguridad](#autenticación-y-seguridad)
- [Testing](#testing)
- [DevOps y Contenedores](#devops-y-contenedores)
- [Herramientas de Desarrollo](#herramientas-de-desarrollo)
- [Visualización y Reportes](#visualización-y-reportes)
- [Servicios Externos](#servicios-externos)

---

## 🔧 Backend

### Framework Principal
- **Django 5.2.7** - Framework web de alto nivel para Python
- **Django REST Framework 3.16.1** - Toolkit para construir APIs RESTful
- **Python 3.13** - Lenguaje de programación

### Servidores ASGI/WSGI
- **Daphne 4.1.0** - Servidor ASGI para Django Channels (WebSockets)
- **Gunicorn 23.0.0** - Servidor WSGI HTTP para producción
- **Uvicorn 0.37.0** - Servidor ASGI de alto rendimiento

### Documentación de API
- **drf-spectacular 0.28.0** - Generación automática de documentación OpenAPI/Swagger

### Utilidades Django
- **django-filter 25.2** - Filtrado avanzado para QuerySets
- **django-cors-headers 4.9.0** - Manejo de CORS (Cross-Origin Resource Sharing)
- **django-debug-toolbar 6.0.0** - Panel de depuración para desarrollo
- **django-storages 1.14.6** - Integración con servicios de almacenamiento (S3)
- **django-redis 5.4.0** - Backend de caché usando Redis

### Gestión de Dependencias
- **Poetry** - Gestor de dependencias y entornos virtuales para Python

---

## 🎨 Frontend

### Framework Principal
- **Next.js 15.5.5** - Framework React con App Router
- **React 19.1.0** - Biblioteca de JavaScript para interfaces de usuario
- **React DOM 19.1.0** - Renderizado de React en el navegador
- **Turbopack** - Bundler de Next.js (modo experimental)

### Lenguaje
- **TypeScript 5.x** - Superset tipado de JavaScript

### Estilos
- **Tailwind CSS 4.x** - Framework CSS utility-first
- **@tailwindcss/postcss 4.x** - Plugin PostCSS para Tailwind

### Gestión de Estado
- **Zustand 5.0.8** - Librería ligera de gestión de estado para React

### Peticiones HTTP y Caché
- **Axios 1.12.2** - Cliente HTTP basado en promesas
- **SWR 2.3.6** - Librería de React Hooks para fetching de datos con caché

### Iconos
- **@heroicons/react 2.2.0** - Iconos SVG optimizados para React

### Visualización de Datos
- **Recharts 3.4.1** - Librería de gráficos para React

### Utilidades
- **js-cookie 3.0.5** - Utilidad para manejar cookies en JavaScript

---

## 🗄️ Base de Datos

### Motor de Base de Datos
- **PostgreSQL 16** - Sistema de gestión de bases de datos relacional

### Drivers y ORM
- **psycopg2-binary 2.9.11** - Adaptador PostgreSQL para Python
- **Django ORM** - Mapeo objeto-relacional incluido en Django

### Utilidades
- **dj-database-url 3.0.1** - Parseo de URLs de base de datos desde variables de entorno

---

## 📦 Almacenamiento

### Servicios de Almacenamiento
- **AWS S3** (producción) - Almacenamiento de objetos en la nube
- **LocalStack** (desarrollo) - Emulador local de servicios AWS (S3)

### SDKs y Librerías
- **boto3 1.40.52** - SDK de AWS para Python
- **django-storages 1.14.6** - Integración Django con S3

---

## ⚡ Colas y Tareas Asíncronas

### Sistema de Colas
- **Celery 5.5.3** - Sistema distribuido de tareas asíncronas
- **Redis 7** - Broker y backend de resultados para Celery
- **django-redis 5.4.0** - Integración Django con Redis

### Utilidades
- **redis 6.4.0** - Cliente Python para Redis

---

## 🔄 Comunicación en Tiempo Real

### WebSockets
- **Django Channels 4.1.0** - Extensión de Django para WebSockets y protocolos asíncronos
- **channels-redis 4.2.0** - Backend Redis para Django Channels
- **Daphne 4.1.0** - Servidor ASGI para Channels

---

## 🔐 Autenticación y Seguridad

### Autenticación
- **djangorestframework-simplejwt 5.5.1** - Autenticación JWT para Django REST Framework

### Seguridad
- **OWASP ZAP** - Herramienta de escaneo de seguridad (en Docker)

---

## 🧪 Testing

### Backend
- **pytest 8.4.2** - Framework de testing para Python
- **pytest-django 4.11.1** - Plugin de pytest para Django
- **pytest-cov 6.0.0** - Plugin de cobertura de código para pytest
- **pytest-html 4.1.1** - Generación de reportes HTML para pytest
- **factory-boy 3.3.3** - Creación de fixtures de prueba
- **faker 33.0.0** - Generación de datos falsos para pruebas

### Frontend
- **Vitest 1.6.1** - Framework de testing rápido para Vite
- **@vitest/coverage-v8 1.6.1** - Plugin de cobertura para Vitest
- **@vitest/ui 1.6.1** - Interfaz de usuario para Vitest
- **@testing-library/react 16.3.0** - Utilidades de testing para React
- **@testing-library/jest-dom 6.9.1** - Matchers personalizados para DOM
- **@testing-library/user-event 14.6.1** - Simulación de eventos de usuario
- **@testing-library/dom 10.4.1** - Utilidades de testing para DOM
- **jsdom 23.2.0** - Implementación de DOM para Node.js (testing)

---

## 🐳 DevOps y Contenedores

### Contenedores
- **Docker** - Plataforma de contenedores
- **Docker Compose** - Orquestación de contenedores multi-contenedor

### Imágenes Base
- **python:3.13-slim** - Imagen base de Python para backend
- **node:20-alpine** - Imagen base de Node.js para frontend (probable)
- **postgres:16** - Imagen oficial de PostgreSQL
- **redis:7** - Imagen oficial de Redis
- **localstack/localstack:latest** - Emulador de servicios AWS
- **ghcr.io/zaproxy/zaproxy:stable** - OWASP ZAP para escaneos de seguridad

---

## 🛠️ Herramientas de Desarrollo

### Gestión de Variables de Entorno
- **python-dotenv 1.1.1** - Carga de variables de entorno desde archivos .env

### Build Tools
- **@vitejs/plugin-react 4.7.0** - Plugin de Vite para React
- **Poetry Core** - Sistema de build para Poetry

### TypeScript
- **@types/node 20** - Tipos de TypeScript para Node.js
- **@types/react 19** - Tipos de TypeScript para React
- **@types/react-dom 19** - Tipos de TypeScript para React DOM

---

## 📊 Visualización y Reportes

### Generación de PDFs
- **ReportLab 4.4.4** - Generación de documentos PDF en Python

### Gráficos y Visualización
- **Matplotlib 3.9.0** - Librería de visualización de datos en Python
- **Recharts 3.4.1** - Gráficos interactivos en React

---

## ☁️ Servicios Externos

### Túneles y Networking
- **Cloudflare Tunnels** - Túneles seguros para exponer servicios locales

### Almacenamiento en la Nube
- **AWS S3** - Almacenamiento de objetos (producción)

---

## 📝 Resumen por Categoría

### Lenguajes
- Python 3.13
- TypeScript 5.x
- JavaScript (ES2017+)

### Frameworks Principales
- Django 5.2.7
- Next.js 15.5.5
- React 19.1.0

### Bases de Datos
- PostgreSQL 16

### Caché y Colas
- Redis 7
- Celery 5.5.3

### Almacenamiento
- AWS S3 (producción)
- LocalStack (desarrollo)

### Testing
- pytest (backend)
- Vitest (frontend)

### Contenedores
- Docker
- Docker Compose

### Comunicación en Tiempo Real
- Django Channels
- WebSockets

### Autenticación
- JWT (JSON Web Tokens)

---

## 🔄 Versiones Específicas

### Backend Core
- Python: `>=3.13,<4`
- Django: `>=5.2.7,<6.0.0`
- Django REST Framework: `>=3.16.1,<4.0.0`

### Frontend Core
- Next.js: `15.5.5`
- React: `19.1.0`
- TypeScript: `^5`

### Base de Datos
- PostgreSQL: `16`

### Contenedores
- Redis: `7`
- LocalStack: `latest`

---

## 📚 Documentación Relacionada

- [README Principal](../README.md) - Información general del proyecto
- [Guía de Pruebas](./PRUEBAS_DOCKER.md) - Cómo ejecutar tests
- [Cobertura de Código](./README-COVERAGE.md) - Reportes de cobertura
- [Docker en Producción](./DOCKER_PRODUCCION.md) - Despliegue con Docker
- [Túneles Cloudflare](./TUNELES_CLOUDFLARE.md) - Configuración de túneles

---

**Última actualización**: Enero 2025  
**Versión del Proyecto**: 2.1.0

