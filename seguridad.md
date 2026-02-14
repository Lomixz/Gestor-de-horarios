# Plan de Seguridad - Sistema Login Academico

## Contexto
El proyecto es un sistema de gestion academica (Flask + SQLite) que maneja horarios, profesores, materias y usuarios con roles (admin, jefe de carrera, profesor). Se identificaron **40+ vulnerabilidades** que necesitan correccion para que el sistema sea seguro en produccion.

---

## FASE 1: Vulnerabilidades CRITICAS (Corregir de inmediato)

### 1.1 Reemplazar SECRET_KEY hardcodeada
- **Archivo:** `app.py`
- **Problema:** `app.config['SECRET_KEY'] = 'tu_clave_secreta_aqui_cambiala_en_produccion'` - Clave expuesta en codigo fuente
- **Impacto:** Session hijacking, CSRF bypass, autenticacion comprometida
- **Solucion:** Usar variable de entorno con fallback seguro via `secrets.token_hex(32)`

### 1.2 Corregir Open Redirect en login
- **Archivo:** `app.py`
- **Problema:** `redirect(request.args.get('next'))` sin validar - permite redirigir a sitios maliciosos
- **Impacto:** Phishing, robo de credenciales
- **Solucion:** Validar que la URL sea interna con `urlparse().netloc == ''`

### 1.3 Corregir Path Traversal en descarga de backups
- **Archivo:** `app.py`
- **Problema:** El parametro `filename` en ruta de descarga de backups no se valida, permitiendo `../../` para acceder a cualquier archivo
- **Impacto:** Lectura arbitraria de archivos del servidor, robo de base de datos
- **Solucion:** Usar `secure_filename()` y validar que el path resuelto este dentro del directorio de backups

### 1.4 Desactivar debug mode
- **Archivo:** `app.py`
- **Problema:** `app.run(debug=True, host='0.0.0.0')` - Expone debugger interactivo
- **Impacto:** Ejecucion remota de codigo, exposicion de codigo fuente
- **Solucion:** Usar variable de entorno `FLASK_DEBUG`

### 1.5 Crear archivo .gitignore
- **Problema:** No existe `.gitignore`. Base de datos, __pycache__, logs y backups estan en el repositorio
- **Impacto:** Datos sensibles expuestos en historial de git
- **Solucion:** Crear `.gitignore` apropiado

---

## FASE 2: Vulnerabilidades ALTAS

### 2.1 Configurar cookies de sesion seguras
- **Problema:** Sin configuracion de seguridad en cookies (Secure, HttpOnly, SameSite)
- **Impacto:** Robo de sesiones, XSS accediendo cookies

### 2.2 Agregar Security Headers
- **Problema:** Sin headers X-Frame-Options, X-Content-Type-Options, CSP, HSTS
- **Impacto:** Clickjacking, MIME sniffing, XSS

### 2.3 Implementar Rate Limiting en login
- **Problema:** Sin limite de intentos de login
- **Impacto:** Ataques de fuerza bruta

### 2.4 Proteccion CSRF en llamadas fetch/AJAX
- **Problema:** 15+ templates hacen `fetch()` POST sin token CSRF
- **Impacto:** CSRF en operaciones criticas (eliminar horarios, configuracion, generacion masiva)
- **Templates afectados:** generar_horarios_masivo, admin_horario_grupos, admin_horario_profesores, asignacion_masiva_materias, configuracion, jefe_generar_horarios_masivo, asignacion_masiva_materias_grupos

### 2.5 Corregir XSS por filtro |safe en templates
- **Problema:** `{{ variable | safe }}` en multiples templates deshabilita auto-escape
- **Impacto:** Inyeccion de JavaScript malicioso

### 2.6 Eliminar exposicion de passwords temporales en HTML
- **Problema:** Passwords temporales visibles en HTML fuente de importar_profesores.html
- **Impacto:** Passwords capturables por extensiones de navegador, cache, historial

### 2.7 Eliminar almacenamiento de password temporal en texto plano
- **Problema:** Campo `password_temporal` en base de datos sin hashear
- **Impacto:** Si la BD se compromete, passwords en texto plano

### 2.8 Validacion de uploads de archivos
- **Problema:** Sin limite de tamano ni validacion de contenido real
- **Impacto:** DoS por archivos grandes, upload de archivos maliciosos

---

## FASE 3: Vulnerabilidades MEDIAS

### 3.1 Politica de passwords mas fuerte
- **Problema:** Minimo 6 caracteres, sin requisitos de complejidad
- **Solucion:** Minimo 8 chars + mayusculas + numeros + caracteres especiales

### 3.2 Reemplazar print() por logging
- **Problema:** Errores con `print()` pueden exponer informacion sensible
- **Solucion:** Usar modulo `logging` con niveles apropiados

### 3.3 Usar text() para consultas SQL raw
- **Problema:** `db.session.execute('VACUUM')` sin wrapper `text()`
- **Solucion:** Usar `from sqlalchemy import text`

### 3.4 Agregar Audit Logging
- **Problema:** Sin registro de eventos de seguridad
- **Solucion:** Registrar logins fallidos, cambios de password, acciones admin

### 3.5 Encriptar backups
- **Problema:** Backups sin encriptacion
- **Solucion:** Encriptar con clave de entorno

---

## FASE 4: Infraestructura y Docker

### 4.1 No ejecutar container como root
- **Problema:** Dockerfile sin directiva USER
- **Solucion:** Crear usuario no privilegiado

### 4.2 Configuracion basada en variables de entorno
- **Problema:** Credenciales y config hardcodeadas
- **Solucion:** Crear `.env.example` y usar `os.environ`

### 4.3 Permisos de directorios
- **Problema:** Directorios sin permisos restrictivos
- **Solucion:** `chmod 750` en instance, logs, uploads

---

## Estado de Implementacion

| Fase | Item | Estado |
|------|------|--------|
| 1.1 | SECRET_KEY | COMPLETADO |
| 1.2 | Open Redirect | COMPLETADO |
| 1.3 | Path Traversal | COMPLETADO |
| 1.4 | Debug Mode | COMPLETADO |
| 1.5 | .gitignore | COMPLETADO |
| 2.1 | Session Cookies | COMPLETADO (junto con 1.1) |
| 2.2 | Security Headers | COMPLETADO (junto con 1.4) |
| 2.3 | Rate Limiting | COMPLETADO |
| 2.4 | CSRF en fetch | COMPLETADO (19 fetch en 9 templates) |
| 2.5 | XSS safe | COMPLETADO (escape() en servidor) |
| 2.6 | Passwords en HTML | COMPLETADO (ocultas por defecto) |
| 2.7 | Password temporal | COMPLETADO (campo eliminado) |
| 2.8 | Upload validation | COMPLETADO (MIME + tamaño) |
| 3.1 | Password policy | COMPLETADO (8+ chars, mayus, num, especial) |
| 3.2 | Logging | COMPLETADO (30+ print -> logger) |
| 3.3 | SQL text() | COMPLETADO |
| 3.4 | Audit logging | COMPLETADO (login/logout/password) |
| 3.5 | Backup encryption | COMPLETADO (AES-256-GCM) |
| 4.1 | Docker user | COMPLETADO (appuser no-root) |
| 4.2 | Env variables | COMPLETADO (env_file + .env) |
| 4.3 | Dir permissions | COMPLETADO (750/755) |
