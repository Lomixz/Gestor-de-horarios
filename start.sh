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

echo ""
echo "=== Sistema listo ==="
echo "  Web:    http://localhost:5001"
echo "  Health: http://localhost:5001/health"
echo "  BD:     PostgreSQL en puerto 5432"
echo "  Redis:  solo accesible internamente (Docker)"
echo ""
echo "  Logs:   docker compose logs -f"
echo "  Parar:  docker compose down"
echo "  Reset:  docker compose down -v  (borra datos)"
