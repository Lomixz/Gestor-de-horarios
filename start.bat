@echo off
chcp 65001 >nul 2>&1
setlocal

echo === Gestor de Horarios - Inicio Completo ===
echo.

REM 1. Verificar que Docker y Docker Compose esten instalados
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker no instalado. Instalalo primero.
    pause
    exit /b 1
)
docker compose version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker Compose no disponible.
    pause
    exit /b 1
)

REM 2. Crear archivo .env si no existe (copia de .env.example)
if not exist .env (
    echo Creando .env desde .env.example...
    copy .env.example .env >nul
    echo IMPORTANTE: Revisa y edita .env con tus credenciales de produccion
    echo.
)

REM 2b. Generar EXTERNAL_API_KEY automaticamente si no esta definida
findstr /r "^EXTERNAL_API_KEY=." .env >nul 2>&1
if %errorlevel% neq 0 (
    for /f "delims=" %%k in ('python -c "import secrets; print(secrets.token_hex(32))"') do set API_KEY_NEW=%%k
    findstr /r "^EXTERNAL_API_KEY=" .env >nul 2>&1
    if %errorlevel% equ 0 (
        powershell -Command "(Get-Content .env) -replace '^EXTERNAL_API_KEY=.*', 'EXTERNAL_API_KEY=%API_KEY_NEW%' | Set-Content .env"
    ) else (
        echo EXTERNAL_API_KEY=%API_KEY_NEW%>> .env
    )
    echo API Key generada y guardada en .env
)

REM 3. Crear directorios necesarios en el host (para los volumenes montados)
echo Creando directorios...
if not exist instance mkdir instance
if not exist logs mkdir logs
if not exist backups mkdir backups
if not exist horarios mkdir horarios
if not exist static\uploads\perfiles mkdir static\uploads\perfiles
if not exist static\uploads\firmas mkdir static\uploads\firmas

REM 4. Construir imagenes Docker
echo Construyendo imagenes...
docker compose build
if %errorlevel% neq 0 (
    echo ERROR: Fallo al construir las imagenes.
    pause
    exit /b 1
)

REM 5. Levantar todos los servicios
echo.
echo Levantando todos los servicios...
docker compose up -d
if %errorlevel% neq 0 (
    echo ERROR: Fallo al levantar los servicios.
    pause
    exit /b 1
)

REM 6. Esperar a que el web este saludable (migraciones + init incluidos)
echo Esperando a que el sistema este listo...
set TIMEOUT=120
set ELAPSED=0

:wait_loop
curl -sf http://localhost:5001/health >nul 2>&1
if %errorlevel% equ 0 goto :ready

timeout /t 2 /nobreak >nul
set /a ELAPSED+=2
if %ELAPSED% geq %TIMEOUT% (
    echo.
    echo ERROR: El sistema no respondio en %TIMEOUT%s.
    echo Revisa los logs: docker compose logs web
    pause
    exit /b 1
)
set /p "=." <nul
goto :wait_loop

:ready
echo.

REM 7. Verificar que todo esta corriendo
echo.
echo === Estado de servicios ===
docker compose ps

REM Leer API Key desde .env
for /f "tokens=2 delims==" %%a in ('findstr "^EXTERNAL_API_KEY=" .env') do set SHOW_API_KEY=%%a

echo.
echo === Sistema listo ===
echo   Web:    http://localhost:5001
echo   Health: http://localhost:5001/health
echo   BD:     PostgreSQL en puerto 5432
echo   Redis:  solo accesible internamente (Docker)
echo.
echo === API de Profesores (para integracion externa) ===
echo   Ping (sin auth):     http://localhost:5001/api/profesores/ping
echo   Listar profesores:   http://localhost:5001/api/profesores
echo   Detalle por ID:      http://localhost:5001/api/profesores/{id}
echo.
echo   Header requerido:    X-API-Key: %SHOW_API_KEY%
echo.
echo   Ejemplo curl:
echo   curl -H "X-API-Key: %SHOW_API_KEY%" http://localhost:5001/api/profesores
echo.
echo   Filtros disponibles:
echo   ?activo=true^|false
echo   ?tipo=profesor_completo^|profesor_asignatura
echo   ?carrera_id=^<id^>
echo.
echo   Logs:   docker compose logs -f
echo   Parar:  docker compose down
echo   Reset:  docker compose down -v  (borra datos)
echo.
pause
