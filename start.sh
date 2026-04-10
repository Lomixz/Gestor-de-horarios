#!/bin/bash
set -e

echo "=== Gestor de Horarios - Inicio Completo ==="
echo ""

# 1. Verificar que Docker y Docker Compose estén instalados
command -v docker >/dev/null 2>&1 || { echo "ERROR: Docker no instalado. Instálalo primero."; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "ERROR: Docker Compose no disponible."; exit 1; }

# 2. Crear archivo .env si no existe (copia de .env.example)
if [ ! -f .env ]; then
    echo "Creando .env desde .env.example..."
    cp .env.example .env
    echo "IMPORTANTE: Revisa y edita .env con tus credenciales de producción"
    echo ""
fi

# 2b. Generar EXTERNAL_API_KEY automáticamente si no está definida
if ! grep -q "^EXTERNAL_API_KEY=.\+" .env 2>/dev/null; then
    API_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    if grep -q "^EXTERNAL_API_KEY=" .env; then
        sed -i.bak "s/^EXTERNAL_API_KEY=.*/EXTERNAL_API_KEY=${API_KEY}/" .env && rm -f .env.bak
    else
        echo "EXTERNAL_API_KEY=${API_KEY}" >> .env
    fi
    echo "API Key generada y guardada en .env"
fi

# 3. Crear directorios necesarios en el host (para los volúmenes montados)
echo "Creando directorios..."
mkdir -p instance logs backups horarios static/uploads/perfiles static/uploads/firmas

# 4. Construir imágenes Docker
echo "Construyendo imágenes..."
docker compose build

# 5. Levantar todos los servicios
# entrypoint.sh se encarga de: flask db upgrade + python init_config.py + gunicorn
echo ""
echo "Levantando todos los servicios..."
docker compose up -d

# 6. Esperar a que el web esté saludable (migraciones + init incluidos)
echo "Esperando a que el sistema esté listo..."
TIMEOUT=120
ELAPSED=0
until curl -sf http://localhost:5001/health >/dev/null 2>&1; do
    sleep 2
    ELAPSED=$((ELAPSED + 2))
    if [ $ELAPSED -ge $TIMEOUT ]; then
        echo ""
        echo "ERROR: El sistema no respondió en ${TIMEOUT}s."
        echo "Revisa los logs: docker compose logs web"
        exit 1
    fi
    printf "."
done
echo ""

# 7. Verificar que todo está corriendo
echo ""
echo "=== Estado de servicios ==="
docker compose ps

API_KEY=$(grep "^EXTERNAL_API_KEY=" .env | cut -d '=' -f2)

echo ""
echo "=== Sistema listo ==="
echo "  Web:    http://localhost:5001"
echo "  Health: http://localhost:5001/health"
echo "  BD:     PostgreSQL en puerto 5432"
echo "  Redis:  solo accesible internamente (Docker)"
echo ""
echo "=== API de Profesores (para integración externa) ==="
echo "  Ping (sin auth):     http://localhost:5001/api/profesores/ping"
echo "  Listar profesores:   http://localhost:5001/api/profesores"
echo "  Detalle por ID:      http://localhost:5001/api/profesores/{id}"
echo ""
echo "  Header requerido:    X-API-Key: ${API_KEY}"
echo ""
echo "  Ejemplo curl:"
echo "  curl -H \"X-API-Key: ${API_KEY}\" http://localhost:5001/api/profesores"
echo ""
echo "  Filtros disponibles:"
echo "  ?activo=true|false"
echo "  ?tipo=profesor_completo|profesor_asignatura"
echo "  ?carrera_id=<id>"
echo ""
echo "  Logs:   docker compose logs -f"
echo "  Parar:  docker compose down"
echo "  Reset:  docker compose down -v  (borra datos)"
