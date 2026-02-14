#!/usr/bin/env python3
"""
Sistema de Backups Automáticos para el Sistema Académico
Ejecutar periódicamente para crear backups de la base de datos
"""
import os
import sys
import shutil
import hashlib
import logging
from datetime import datetime, timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Configurar logging
logging.basicConfig(
    filename='logs/backup.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_encryption_key():
    """Obtener clave de encriptación desde variable de entorno"""
    key_hex = os.environ.get('BACKUP_ENCRYPTION_KEY')
    if not key_hex:
        return None
    try:
        key = bytes.fromhex(key_hex)
        if len(key) != 32:
            logging.error("BACKUP_ENCRYPTION_KEY debe ser de 32 bytes (64 caracteres hex)")
            return None
        return key
    except ValueError:
        logging.error("BACKUP_ENCRYPTION_KEY no es un valor hexadecimal válido")
        return None

def encrypt_file(filepath, key):
    """Encriptar archivo con AES-256-GCM"""
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce para GCM

    with open(filepath, 'rb') as f:
        plaintext = f.read()

    ciphertext = aesgcm.encrypt(nonce, plaintext, None)

    encrypted_path = filepath + '.enc'
    with open(encrypted_path, 'wb') as f:
        # Formato: nonce (12 bytes) + ciphertext
        f.write(nonce + ciphertext)

    # Eliminar archivo original sin encriptar
    os.remove(filepath)
    logging.info(f"Backup encriptado: {encrypted_path}")
    return encrypted_path

def decrypt_file(encrypted_path, key):
    """Desencriptar archivo con AES-256-GCM"""
    aesgcm = AESGCM(key)

    with open(encrypted_path, 'rb') as f:
        data = f.read()

    nonce = data[:12]
    ciphertext = data[12:]

    plaintext = aesgcm.decrypt(nonce, ciphertext, None)

    decrypted_path = encrypted_path.replace('.enc', '')
    with open(decrypted_path, 'wb') as f:
        f.write(plaintext)

    logging.info(f"Backup desencriptado: {decrypted_path}")
    return decrypted_path

def generate_encryption_key():
    """Generar una nueva clave de encriptación AES-256 (para configuración inicial)"""
    key = AESGCM.generate_key(bit_length=256)
    return key.hex()

def create_app():
    """Crear aplicación Flask"""
    app = Flask(__name__)
    basedir = os.path.dirname(os.path.abspath(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "sistema_academico.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    return app

def init_db(app):
    """Inicializar base de datos"""
    # Importar db desde models (igual que en app.py)
    from models import db, BackupHistory, ConfiguracionSistema

    # Inicializar db con la app (igual que en app.py)
    db.init_app(app)

    with app.app_context():
        return db, BackupHistory, ConfiguracionSistema

def crear_backup_automatico():
    """Crear backup automático de la base de datos"""
    try:
        app = create_app()
        db, BackupHistory, ConfiguracionSistema = init_db(app)

        with app.app_context():
            # Verificar frecuencia de backup
            backup_freq = ConfiguracionSistema.get_config('backup_frequency', 'daily')

            # Verificar si ya se hizo backup hoy (para frecuencia diaria)
            hoy = datetime.now().date()
            ultimo_backup = BackupHistory.query.filter(
                BackupHistory.fecha_creacion >= hoy,
                BackupHistory.tipo == 'automatico'
            ).first()

            if ultimo_backup and backup_freq == 'daily':
                logging.info("Backup diario ya realizado hoy")
                return True

            # Crear directorio de backups
            backup_dir = ConfiguracionSistema.get_config('backup_location', 'backups/')
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
                logging.info(f"Directorio de backups creado: {backup_dir}")

            # Generar nombre del archivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'backup_auto_{timestamp}.db'
            filepath = os.path.join(backup_dir, filename)

            # Copiar archivo de base de datos
            db_path = 'instance/sistema_academico.db'
            if not os.path.exists(db_path):
                logging.error(f"Archivo de base de datos no encontrado: {db_path}")
                return False

            shutil.copy2(db_path, filepath)
            logging.info(f"Backup creado: {filepath}")

            # Calcular tamaño y checksum del archivo original
            file_size = os.path.getsize(filepath)
            with open(filepath, 'rb') as f:
                checksum = hashlib.sha256(f.read()).hexdigest()

            # Encriptar backup si la clave está configurada
            encryption_key = get_encryption_key()
            if encryption_key:
                filepath = encrypt_file(filepath, encryption_key)
                filename = filename + '.enc'
                file_size = os.path.getsize(filepath)
                logging.info("Backup encriptado con AES-256-GCM")
            else:
                logging.warning("BACKUP_ENCRYPTION_KEY no configurada - backup sin encriptar")

            # Registrar en historial
            backup = BackupHistory(
                filename=filename,
                tipo='automatico',
                tamano=file_size,
                ruta_archivo=filepath
            )
            backup.checksum = checksum
            db.session.add(backup)
            db.session.commit()

            logging.info(f"Backup automático completado: {filename} ({file_size} bytes)")

            # Limpiar backups antiguos
            limpiar_backups_antiguos(backup_dir, ConfiguracionSistema, BackupHistory, db)

            return True

    except Exception as e:
        logging.error(f"Error al crear backup automático: {str(e)}")
        return False

def limpiar_backups_antiguos(backup_dir, ConfiguracionSistema, BackupHistory, db):
    """Limpiar backups antiguos según la política de retención"""
    try:
        retention_days = int(ConfiguracionSistema.get_config('backup_retention', '30'))

        # Calcular fecha límite
        fecha_limite = datetime.now() - timedelta(days=retention_days)

        # Obtener backups antiguos
        backups_antiguos = BackupHistory.query.filter(
            BackupHistory.fecha_creacion < fecha_limite,
            BackupHistory.tipo == 'automatico'
        ).all()

        backups_eliminados = 0
        for backup in backups_antiguos:
            try:
                # Eliminar archivo físico
                if os.path.exists(backup.ruta_archivo):
                    os.remove(backup.ruta_archivo)
                    logging.info(f"Backup antiguo eliminado: {backup.filename}")

                # Eliminar registro de base de datos
                db.session.delete(backup)
                backups_eliminados += 1

            except Exception as e:
                logging.error(f"Error al eliminar backup {backup.filename}: {str(e)}")

        if backups_eliminados > 0:
            db.session.commit()
            logging.info(f"Se eliminaron {backups_eliminados} backups antiguos")

    except Exception as e:
        logging.error(f"Error al limpiar backups antiguos: {str(e)}")

def crear_backup_manual():
    """Crear backup manual (llamado desde la interfaz web)"""
    return crear_backup_automatico()

def verificar_estado_backups():
    """Verificar estado del sistema de backups"""
    try:
        app = create_app()
        db, BackupHistory, ConfiguracionSistema = init_db(app)

        with app.app_context():
            # Obtener estadísticas
            total_backups = BackupHistory.query.count()
            backups_automaticos = BackupHistory.query.filter_by(tipo='automatico').count()
            backups_manuales = BackupHistory.query.filter_by(tipo='manual').count()

            # Obtener último backup
            ultimo_backup = BackupHistory.query.order_by(BackupHistory.fecha_creacion.desc()).first()

            # Verificar espacio en disco
            backup_dir = ConfiguracionSistema.get_config('backup_location', 'backups/')
            if os.path.exists(backup_dir):
                import shutil
                total, used, free = shutil.disk_usage(backup_dir)
                espacio_libre_gb = free / (1024**3)
            else:
                espacio_libre_gb = 0

            return {
                'total_backups': total_backups,
                'backups_automaticos': backups_automaticos,
                'backups_manuales': backups_manuales,
                'ultimo_backup': ultimo_backup.fecha_creacion if ultimo_backup else None,
                'espacio_libre_gb': round(espacio_libre_gb, 2),
                'backup_dir': backup_dir
            }

    except Exception as e:
        logging.error(f"Error al verificar estado de backups: {str(e)}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        comando = sys.argv[1]

        if comando == 'auto':
            success = crear_backup_automatico()
            print("✅ Backup automático completado" if success else "❌ Error en backup automático")
        elif comando == 'manual':
            success = crear_backup_manual()
            print("✅ Backup manual completado" if success else "❌ Error en backup manual")
        elif comando == 'status':
            status = verificar_estado_backups()
            if status:
                print("📊 Estado del Sistema de Backups:")
                print(f"   Total de backups: {status['total_backups']}")
                print(f"   Backups automáticos: {status['backups_automaticos']}")
                print(f"   Backups manuales: {status['backups_manuales']}")
                print(f"   Último backup: {status['ultimo_backup']}")
                print(f"   Espacio libre: {status['espacio_libre_gb']} GB")
            else:
                print("❌ Error al obtener estado del sistema de backups")
        elif comando == 'genkey':
            key = generate_encryption_key()
            print(f"Nueva clave AES-256 generada:")
            print(f"BACKUP_ENCRYPTION_KEY={key}")
            print(f"\nAgrega esta linea a tu archivo .env")
        elif comando == 'decrypt':
            if len(sys.argv) < 3:
                print("Uso: python backup_manager.py decrypt <archivo.enc>")
                sys.exit(1)
            enc_file = sys.argv[2]
            key = get_encryption_key()
            if not key:
                print("Error: BACKUP_ENCRYPTION_KEY no configurada")
                sys.exit(1)
            try:
                result = decrypt_file(enc_file, key)
                print(f"Backup desencriptado: {result}")
            except Exception as e:
                print(f"Error al desencriptar: {e}")
                sys.exit(1)
        else:
            print("Uso: python backup_manager.py [auto|manual|status|genkey|decrypt <archivo>]")
    else:
        # Ejecutar backup automático por defecto
        success = crear_backup_automatico()
        sys.exit(0 if success else 1)