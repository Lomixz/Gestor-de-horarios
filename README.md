# Sistema de Gestión Académica

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Último commit](https://img.shields.io/github/last-commit/xXPakoGamer10Xx/sistema_login)](https://github.com/xXPakoGamer10Xx/sistema_login/commits/main)
[![Issues](https://img.shields.io/github/issues/xXPakoGamer10Xx/sistema_login)](https://github.com/xXPakoGamer10Xx/sistema_login/issues)
[![Stars](https://img.shields.io/github/stars/xXPakoGamer10Xx/sistema_login?style=social)](https://github.com/xXPakoGamer10Xx/sistema_login/stargazers)
[![Forks](https://img.shields.io/github/forks/xXPakoGamer10Xx/sistema_login?style=social)](https://github.com/xXPakoGamer10Xx/sistema_login/network/members)

Aplicación web desarrollada con Flask para administrar carreras, materias, grupos, profesores y horarios académicos. Incluye generación automática de horarios, control de disponibilidad docente, importación/exportación de datos, respaldo de base de datos y autenticación por roles.

## Tabla de contenidos

- [Características](#características)
- [Stack tecnológico](#stack-tecnológico)
- [Requisitos](#requisitos)
- [Inicio rápido con Docker](#inicio-rápido-con-docker-recomendado)
- [Instalación local](#instalación-local)
- [Configuración de entorno](#configuración-de-entorno)
- [Usuario inicial](#usuario-inicial)
- [Comandos operativos](#comandos-operativos)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Seguridad](#seguridad)
- [Despliegue en producción](#despliegue-en-producción-linux)
- [Licencia](#licencia)

## Características

### Funcionalidad principal
- **Generación automática de horarios** con OR-Tools (asincrónica con Celery para grandes volumenes).
- **Gestión de disponibilidad** de profesores por día y bloque horario.
- **Importación masiva** de datos académicos (profesores, materias, carreras y asignaciones).
- **Exportación de reportes** en PDF/Excel con formato personalizado.
- **Sistema de backups** con soporte de cifrado AES-256-GCM.
- **Control de acceso por roles** con flujos diferenciados para administración y personal docente.
- **Interfaz web responsive** con Bootstrap 5 y validación en cliente/servidor.

### Características técnicas (Phase 2)
- **Modularización**: Código base refactorizado en blueprints y helpers para mejorar mantenibilidad.
- **Validación de formularios**: WTForms con validadores de teléfono, longitud, tamaño de archivo, etc.
- **Estado asincrónico**: Tracker de progreso en Redis para generaciones concurrentes.
- **Escalabilidad**: PostgreSQL + Celery workers permiten cargas masivas sin bloqueos.
- **Health check**: Endpoint `/health` verifica estado de BD, Redis y workers.

### Roles de usuario

| Rol | Alcance principal |
| --- | --- |
| Administrador | Gestión completa del sistema: usuarios, catálogos, horarios, configuración y backups |
| Jefe de carrera | Gestión académica de su carrera, asignaciones y reportes |
| Profesor tiempo completo | Consulta de carga asignada y administración de disponibilidad |
| Profesor por asignatura | Consulta de horarios/materias y administración de disponibilidad |

## Stack tecnológico

| Capa | Tecnología |
| --- | --- |
| Backend | Flask 2.3, Python 3.12 |
| Base de datos | PostgreSQL 16 + SQLAlchemy 2.x |
| Cache / Estado | Redis 7 |
| Task queue | Celery + Redis broker |
| Formularios y auth | Flask-WTF, WTForms, Flask-Login |
| Seguridad | Flask-Limiter, cryptography |
| Generación de horarios | Google OR-Tools (asincrónico con Celery) |
| Exportación | ReportLab, xhtml2pdf, OpenPyXL |
| Despliegue | Gunicorn (4 workers), Docker, Docker Compose |

## Requisitos

### Para ejecución con Docker

- Docker 24+ (o compatible con Compose v2)
- Docker Compose

### Para ejecución local

- Python 3.12 (recomendado)
- `pip`

## Inicio rápido con Docker (recomendado)

**Opción 1: Arranque automatizado (recomendado)**

```bash
git clone https://github.com/xXPakoGamer10Xx/sistema_login.git
cd sistema_login
chmod +x start.sh
./start.sh
```

El script `start.sh` levanta automáticamente PostgreSQL, Redis, Celery worker y la aplicación. Aplicación disponible en: `http://localhost:5001`

**Opción 2: Arranque manual**

```bash
docker compose up --build -d
docker compose exec web flask db upgrade
docker compose exec web python init_config.py
```

Notas de arranque del contenedor:

- Si no existe `.env`, se genera automáticamente con una `SECRET_KEY` segura.
- Se crean carpetas operativas (`instance`, `logs`, `backups`, `static/uploads`, `horarios`).
- Las migraciones de BD se ejecutan automáticamente si no han sido aplicadas.
- Health check endpoint: `GET /health` verifica BD, Redis y Celery worker.

## Instalación local

```bash
git clone https://github.com/xXPakoGamer10Xx/sistema_login.git
cd sistema_login

python3 -m venv venv
source venv/bin/activate      # En Windows: venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env

python init_config.py
python migrate_remove_password_temporal.py
python app.py
```

Aplicación disponible en: `http://localhost:5001`

## Configuración de entorno

Variables soportadas en `.env`:

| Variable | Descripción | Valor por defecto |
| --- | --- | --- |
| `SECRET_KEY` | Clave de sesión y CSRF | Se genera automáticamente si no está definida |
| `DATABASE_URL` | URL de conexión PostgreSQL | `postgresql://gestor_user:gestor_secret_2024@db:5432/sistema_academico` |
| `FLASK_DEBUG` | Modo debug (`0`/`1`) | `0` |
| `BACKUP_ENCRYPTION_KEY` | Clave hex de 32 bytes para cifrar backups | Vacía (sin cifrado) |
| `POSTGRES_PASSWORD` | Contraseña del usuario PostgreSQL | `gestor_secret_2024` |
| `REDIS_URL` | URL de conexión Redis | `redis://redis:6379/0` |
| `CELERY_BROKER_URL` | URL del broker Celery | `redis://redis:6379/0` |

Generar claves:

```bash
# SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# BACKUP_ENCRYPTION_KEY (AES-256)
python backup_manager.py genkey
```

## Usuario inicial

En la primera ejecución se crea un usuario administrador por defecto:

| Campo | Valor |
| --- | --- |
| Usuario | `admin` |
| Contraseña | `admin123` |
| Rol | Administrador |

Recomendación: cambiar la contraseña inmediatamente después del primer acceso.

## Comandos operativos

### Con Docker Compose

```bash
# Ver estado de los servicios
docker compose ps

# Ver logs en tiempo real
docker compose logs -f                    # Todos los servicios
docker compose logs -f web                # Solo la app
docker compose logs -f celery_worker      # Solo Celery worker

# Ejecutar migraciones de BD
docker compose exec web flask db upgrade
docker compose exec web flask db revision --autogenerate -m "Descripción"

# Backups
docker compose exec web python backup_manager.py manual
docker compose exec web python backup_manager.py status
docker compose exec web python backup_manager.py decrypt backups/archivo.enc

# Detener servicios
docker compose down
docker compose down -v                    # Incluye volúmenes (borra datos de BD y Redis)
```

### Inspeccionar Celery

```bash
# Ver workers activos
docker compose exec celery_worker celery -A celery_app inspect active

# Ver cola de tareas
docker compose exec celery_worker celery -A celery_app inspect reserved

# Monitorar en tiempo real
docker compose exec celery_worker celery -A celery_app events
```

## Estructura del proyecto

```text
sistema_login/
├── app.py                                 # Punto de entrada (10k líneas, enrutamiento principal)
├── models.py                              # Modelos SQLAlchemy
├── forms.py                               # Formularios WTForms con validadores
├── utils.py                               # Utilidades compartidas
├── backup_manager.py                      # Gestión de backups con cifrado
├── generador_horarios_mejorado.py         # OR-Tools solver para horarios
├── celery_app.py                          # Configuración de Celery
├── progress.py                            # Tracker de progreso en Redis
├── init_config.py                         # Inicialización del sistema
├── requirements.txt
├── Dockerfile                             # Imagen con Gunicorn (4 workers)
├── docker-compose.yml                     # PostgreSQL, Redis, Celery worker
├── entrypoint.sh                          # Script de arranque del contenedor
├── start.sh                               # Script automatizado de arranque completo
├── .env.example
├── seguridad.md
├── app_pkg/                               # Paquete modular (Phase 2 refactoring)
│   ├── helpers/                           # Funciones extraídas de app.py
│   │   ├── generation_helpers.py          # Lógica de generación de horarios
│   │   ├── export_helpers.py              # PDF/Excel exports
│   │   ├── professor_helpers.py           # Disponibilidad y carga horaria
│   │   ├── schedule_helpers.py            # Procesamiento de horarios
│   │   └── __init__.py                    # Re-exports para backwards compatibility
│   └── blueprints/                        # Flask blueprints (modularización en progreso)
│       ├── api.py                         # Health check + API JSON endpoints
│       ├── auth.py                        # Autenticación (login, registro, logout)
│       └── admin/                         # Blueprints de administración (futura expansión)
├── instance/
├── templates/
├── static/
├── logs/
├── backups/
└── horarios/
```

**Nota sobre refactoring**: La Phase 2 está en progreso. Actualmente, helpers y blueprints coexisten. El objetivo es migrar todas las rutas a blueprints incrementalmente para mejorar mantenibilidad.

## Validación de formularios

Todos los formularios incluyen validadores WTForms robustos:

| Campo | Validaciones |
| --- | --- |
| **Usuario** | Máx 80 caracteres, único en BD |
| **Email** | Formato válido, máx 120 caracteres, único en BD |
| **Teléfono** | Exactamente 10 dígitos, solo números |
| **Nombre/Apellido** | Máx 100 caracteres |
| **Materia/Carrera** | Máx 200/150 caracteres |
| **Códigos** | Máx 20 caracteres, convertidos a mayúsculas |
| **Números** | Rangos válidos (ej: grupo 1-99, cuatrimestre 0-10) |
| **Horas** | Validación: hora_fin > hora_inicio |
| **Archivos** | Máx 5-10 MB según tipo; tipos permitidos: PDF, XLS, XLSX, CSV |

Validación ocurre tanto en cliente (HTML5 attributes) como en servidor (WTForms validators).

## Seguridad

El proyecto incluye controles de seguridad a nivel de aplicación y despliegue, entre ellos:

- Protección CSRF en formularios.
- Rate limiting en endpoints sensibles (por ejemplo login/registro).
- Security headers HTTP.
- Cookies de sesión seguras (`HttpOnly`, `SameSite=Lax`) y expiración de sesión.
- Validación de contraseñas y controles de autenticación.
- Validación de uploads (tipo/tamaño).
- Logging de auditoría.
- Contenedor Docker ejecutado como usuario no privilegiado.

Detalle técnico y checklist ampliado: `seguridad.md`.

## Despliegue en producción (Linux)

### Docker Compose

```bash
cp .env.example .env
# Editar .env con valores de producción:
# - SECRET_KEY: generar con python -c "import secrets; print(secrets.token_hex(32))"
# - POSTGRES_PASSWORD: cambiar a contraseña fuerte
# - BACKUP_ENCRYPTION_KEY: opcional, para cifrar backups

docker compose up --build -d
docker compose exec web flask db upgrade
docker compose exec web python init_config.py
```

### Verificación post-despliegue

```bash
# Verificar estado de servicios
docker compose ps

# Verificar health check
curl -s http://localhost:5001/health | python -m json.tool

# Ver logs de cualquier servicio
docker compose logs -f web
docker compose logs -f celery_worker
```

### Reverse proxy (Nginx)

```nginx
upstream app {
    server 127.0.0.1:5001;
}

server {
    listen 80;
    server_name tu-dominio.com;

    # Health check (usado por load balancers)
    location /health {
        proxy_pass http://app;
        access_log off;
    }

    location /static {
        alias /opt/sistema_login/static;
        expires 30d;
        access_log off;
    }

    location / {
        proxy_pass http://app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }

    client_max_body_size 10M;
}
```

**Notas de producción**:
- Usar generador de horarios masivos es asincrónico (Celery); esperar hasta 30s en timeout del proxy.
- Health check endpoint (`/health`) debe ser accesible para load balancers.

### HTTPS con Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com
```

## Licencia

Este proyecto se distribuye bajo la licencia MIT.
