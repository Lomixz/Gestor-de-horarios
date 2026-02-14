# Sistema de Gestion Academica

Sistema web desarrollado con Flask para la gestion integral de horarios academicos, profesores, materias y carreras. Incluye generacion automatica de horarios, gestion de disponibilidad docente, importacion/exportacion de datos y control de acceso basado en roles.

## Caracteristicas Principales

- **Generacion automatica de horarios** con algoritmo de optimizacion (OR-Tools)
- **Gestion de disponibilidad** de profesores por dia y hora
- **Importacion masiva** de profesores, materias, carreras y asignaciones via Excel
- **Exportacion de horarios** en PDF y Excel
- **Sistema de backups** automaticos con encriptacion AES-256-GCM
- **4 roles de usuario** con permisos diferenciados
- **Interfaz responsiva** con Bootstrap 5 adaptada a cualquier dispositivo

### Roles de Usuario

| Rol | Permisos |
|-----|----------|
| **Administrador** | Gestion completa: usuarios, carreras, materias, grupos, horarios, configuracion del sistema, backups |
| **Jefe de Carrera** | Gestion de profesores y horarios de su carrera, generacion de horarios, reportes |
| **Profesor Tiempo Completo** | Ver horarios asignados, gestionar disponibilidad, ver materias |
| **Profesor por Asignatura** | Ver horarios y materias asignadas, gestionar disponibilidad |

## Instalacion

### Opcion 1: Docker (Recomendado)

Solo necesitas Docker instalado. Todo se configura automaticamente:

```bash
git clone https://github.com/xXPakoGamer10Xx/sistema_login.git
cd sistema_login
docker compose up --build
```

El sistema estara disponible en `http://localhost:5001`

> El entrypoint genera automaticamente el archivo `.env` con una `SECRET_KEY` segura si no existe, inicializa la base de datos y ejecuta las migraciones pendientes.

### Opcion 2: Instalacion Manual

#### Requisitos
- Python 3.10 o superior
- pip

#### Pasos

```bash
# Clonar el proyecto
git clone https://github.com/xXPakoGamer10Xx/sistema_login.git
cd sistema_login

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Crear archivo de configuracion
cp .env.example .env

# Inicializar base de datos
python init_config.py

# Ejecutar
python app.py
```

El sistema estara disponible en `http://localhost:5001`

## Usuario por Defecto

Al iniciar por primera vez se crea automaticamente:

| Campo | Valor |
|-------|-------|
| Usuario | `admin` |
| Contrasena | `admin123` |
| Rol | Administrador |

> Se recomienda cambiar la contrasena inmediatamente despues del primer inicio de sesion.

## Estructura del Proyecto

```
sistema_login/
├── app.py                          # Aplicacion principal Flask (rutas y logica)
├── models.py                       # Modelos de base de datos (SQLAlchemy)
├── forms.py                        # Formularios (WTForms)
├── utils.py                        # Funciones auxiliares
├── generador_horarios_mejorado.py  # Motor de generacion de horarios (OR-Tools)
├── backup_manager.py               # Gestor de backups con encriptacion AES-256-GCM
├── init_config.py                  # Inicializacion del sistema y BD
├── migrate_remove_password_temporal.py  # Migracion de seguridad
├── requirements.txt                # Dependencias de Python
├── Dockerfile                      # Configuracion del contenedor
├── docker-compose.yml              # Orquestacion Docker
├── entrypoint.sh                   # Script de inicio automatico
├── .env.example                    # Plantilla de variables de entorno
├── .gitignore                      # Archivos excluidos de git
├── seguridad.md                    # Documentacion de seguridad
├── instance/
│   ├── poblar.py                   # Script para poblar datos de ejemplo
│   └── limpiar_base_datos.py       # Script para limpiar la BD
├── templates/
│   ├── base.html                   # Plantilla base
│   ├── login.html                  # Inicio de sesion
│   ├── register.html               # Registro de usuarios
│   ├── dashboard.html              # Panel principal
│   ├── admin/                      # 44 templates del administrador
│   ├── jefe/                       # 15 templates del jefe de carrera
│   ├── profesor/                   # 4 templates del profesor
│   ├── errors/                     # Paginas de error (404, 500)
│   └── exports/                    # Plantillas de exportacion PDF
├── static/
│   ├── css/style.css               # Estilos personalizados
│   ├── images/                     # Imagenes del sistema
│   └── uploads/                    # Archivos subidos (perfiles, firmas)
├── logs/                           # Logs de aplicacion y auditoria
└── backups/                        # Backups de la base de datos
```

## Configuracion

Las variables de entorno se configuran en el archivo `.env`:

| Variable | Descripcion | Requerida |
|----------|-------------|-----------|
| `SECRET_KEY` | Clave secreta para sesiones y CSRF | Se auto-genera si no se define |
| `DATABASE_URL` | URI de la base de datos | No (default: SQLite) |
| `FLASK_DEBUG` | Modo debug: 0 o 1 | No (default: 0) |
| `BACKUP_ENCRYPTION_KEY` | Clave AES-256 para encriptar backups | No |

Generar una clave secreta manualmente:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Generar clave de encriptacion para backups:
```bash
python backup_manager.py genkey
```

## Seguridad

El sistema implementa 21 medidas de seguridad documentadas en `seguridad.md`:

- **SECRET_KEY** dinamica via variable de entorno
- **Proteccion CSRF** en formularios y llamadas AJAX (secureFetch)
- **Rate Limiting** en login (10 intentos/min) y registro (5/min)
- **Security Headers**: X-Frame-Options, X-Content-Type-Options, HSTS, Referrer-Policy
- **Cookies seguras**: HttpOnly, SameSite=Lax, timeout de 60 minutos
- **Validacion de passwords**: minimo 8 caracteres, mayuscula, numero y caracter especial
- **Proteccion contra Open Redirect** en login
- **Proteccion contra Path Traversal** en descarga de backups
- **Prevencion de XSS** con escape de datos en servidor
- **Validacion de uploads**: tipo MIME y limite de 5MB
- **Audit logging**: registro de logins, logouts y cambios de contrasena
- **Backups encriptados** con AES-256-GCM
- **Docker no-root**: contenedor ejecuta como usuario sin privilegios (`appuser`)

## Despliegue en Produccion (Linux)

### Con Docker

```bash
# Crear archivo de configuracion
cp .env.example .env
# Editar .env con valores de produccion (SECRET_KEY, etc.)

# Levantar el servicio
docker compose up --build -d
```

### Con Nginx como Proxy Inverso

```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    location /static {
        alias /opt/sistema_login/static;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 10M;
}
```

### HTTPS con Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com
```

## Comandos Utiles

```bash
# Backup manual de la base de datos
python backup_manager.py manual

# Ver estado de backups
python backup_manager.py status

# Poblar base de datos con datos de ejemplo
python instance/poblar.py

# Limpiar base de datos
python instance/limpiar_base_datos.py

# Generar clave de encriptacion para backups
python backup_manager.py genkey

# Desencriptar un backup
python backup_manager.py decrypt backups/archivo.db.enc
```

## Tecnologias

| Componente | Tecnologia |
|------------|-----------|
| Backend | Flask 2.3, Python 3.12 |
| Base de datos | SQLite + SQLAlchemy 2.0 |
| Frontend | Bootstrap 5, JavaScript |
| Autenticacion | Flask-Login + Flask-WTF (CSRF) |
| Generacion de horarios | Google OR-Tools |
| Exportacion | ReportLab (PDF), OpenPyXL (Excel) |
| Seguridad | Flask-Limiter, cryptography (AES-256-GCM) |
| Despliegue | Docker, Gunicorn |

## Licencia

Este proyecto esta bajo la Licencia MIT.
